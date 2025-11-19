from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView,TemplateView
from todo.forms import CustomUserCreationForm, TaskForm
from .models import UserModel, TaskModel, TaskHistoryModel, TelegramUserModel
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.contrib import messages
from django.http import HttpResponse


# Create your views here.
class UserListView(LoginRequiredMixin, ListView):
    model = UserModel
    template_name = 'todo/users/list.html'
    context_object_name = 'users'
    paginate_by = 10
    ordering = ['username']

class UserDetailView(DetailView):
    model = UserModel
    template_name = 'todo/users/detail.html'
    context_object_name = 'profile'
    
class TaskListView(LoginRequiredMixin, ListView):
    model = TaskModel
    template_name = 'todo/tasks/list.html'
    context_object_name = 'tasks'
    paginate_by = 10
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'employee':
            return TaskModel.objects.filter(assignee=user)
        elif user.role == 'manager':
            return TaskModel.objects.all()
        return TaskModel.objects.none()

class TaskDetailView(DetailView):
    model = TaskModel
    template_name = 'todo/tasks/detail.html'
    context_object_name = 'task'
    
class TaskCreateView(CreateView):
    model = TaskModel
    template_name = 'todo/tasks/create.html'
    success_url = reverse_lazy('todo:task_list')
    form_class = TaskForm

    
class TaskHistoryListView(ListView):
    model = TaskHistoryModel
    template_name = 'todo/history/list.html'
    context_object_name = 'histories'
    paginate_by = 20
    ordering = ['-changed_at']

class TaskHistoryDetailView(DetailView):
    model = TaskHistoryModel
    template_name = 'todo/history/detail.html'
    context_object_name = 'history'

class TelegramUserListView(ListView):
    model = TelegramUserModel
    template_name = 'todo/telegram_users/list.html'
    context_object_name = 'telegram_users'
    paginate_by = 10
    ordering = ['user__username']

class TelegramUserDetailView(DetailView):
    model = TelegramUserModel
    template_name = 'todo/telegram_users/detail.html'
    context_object_name = 'telegram_user'
    
class TelegramUserCreateView(CreateView):
    model = TelegramUserModel
    fields = ['user', 'telegram_id', 'is_active']
    template_name = 'todo/telegram_users/create.html'
    success_url = reverse_lazy('todo:telegram_user_list')

class RegistrationDoneView(TemplateView):
    template_name = 'todo/auth/registration_done.html'

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Отправляем письмо с подтверждением
            current_site = get_current_site(request)
            mail_subject = 'Активируйте ваш аккаунт'
            message = render_to_string('todo/auth/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            return redirect('todo:registration_done')
    else:
        form = CustomUserCreationForm()
    return render(request, 'todo/auth/register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = UserModel.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Ваш аккаунт успешно активирован! Теперь вы можете войти.')
        return redirect('todo:login')  # ← редирект на вход
    else:
        messages.error(request, 'Ссылка активации недействительна или уже использована.')
        return redirect('todo:login')

