from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView
from .models import UserModel, TaskModel, TaskHistoryModel, TelegramUserModel
from django import forms

# Create your views here.
class UserListView(ListView):
    model = UserModel
    template_name = 'todo/users/list.html'
    context_object_name = 'users'
    paginate_by = 10
    ordering = ['username']

class UserDetailView(DetailView):
    model = UserModel
    template_name = 'todo/users/detail.html'
    context_object_name = 'profile'
    
# Форма для создания пользователя (без пароля вручную — только через админку или register)
class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = UserModel
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'password']
    
class UserCreateView(CreateView):
    model = UserModel
    form_class = UserCreateForm
    template_name = 'todo/users/create.html'
    success_url = reverse_lazy('todo:user_list')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        return super().form_valid(form)


class TaskListView(ListView):
    model = TaskModel
    template_name = 'todo/tasks/list.html'
    context_object_name = 'tasks'
    paginate_by = 10
    ordering = ['-created_at']

class TaskDetailView(DetailView):
    model = TaskModel
    template_name = 'todo/tasks/detail.html'
    context_object_name = 'task'
    
class TaskCreateView(CreateView):
    model = TaskModel
    fields = ['title', 'description', 'assignee', 'created_by', 'deadline', 'priority', 'status']
    template_name = 'todo/tasks/create.html'
    success_url = reverse_lazy('todo:task_list')

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
    success_url = 'todo:telegram_user_list'