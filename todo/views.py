from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView,TemplateView, UpdateView, DeleteView
from todo.forms import CustomUserCreationForm, TaskFileFormSet, TaskForm
from .models import TaskFile, UserModel, TaskModel, TaskHistoryModel, TelegramUserModel
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

    def form_valid(self, form):
        # Сохраняем задачу
        self.object = form.save()
        
        # Обрабатываем несколько файлов
        files = self.request.FILES.getlist('files')
        for f in files:
            TaskFile.objects.create(task=self.object, file=f)
        
        return super().form_valid(form)
  
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

class TaskUpdateView(UpdateView):
    model = TaskModel
    form_class = TaskForm
    template_name = "todo/tasks/update.html"
    success_url = reverse_lazy('todo:task_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['file_formset'] = TaskFileFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            data['file_formset'] = TaskFileFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        file_formset = context['file_formset']
        if file_formset.is_valid():
            self.object = form.save()
            file_formset.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class TaskDeleteView(DeleteView):
    model = TaskModel
    template_name = "todo/tasks/delete.html"
    success_url = reverse_lazy('todo:task_list')


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

