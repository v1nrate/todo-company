from django.views.generic import ListView, DetailView
from .models import UserModel, TaskModel, TaskHistoryModel, TelegramUserModel

# Create your views here.
class UserListView(ListView):
    model = UserModel
    template_name = ''
    context_object_name = 'users'
    paginate_by = 10
    ordering = ['username']

class UserDetailView(DetailView):
    model = UserModel
    template_name = ''
    context_object_name = 'profile'

class TaskListView(ListView):
    model = TaskModel
    template_name = ''
    context_object_name = 'tasks'
    paginate_by = 10
    ordering = ['-created_at']

class TaskDetailView(DetailView):
    model = TaskModel
    template_name = ''
    context_object_name = 'task'

class TaskHistoryListView(ListView):
    model = TaskHistoryModel
    template_name = ''
    context_object_name = 'histories'
    paginate_by = 20
    ordering = ['-changed_at']

class TaskHistoryDetailView(DetailView):
    model = TaskHistoryModel
    template_name = ''
    context_object_name = 'history'

class TelegramUserListView(ListView):
    model = TelegramUserModel
    template_name = ''
    context_object_name = 'telegram_users'
    paginate_by = 10
    ordering = ['user__username']

class TelegramUserDetailView(DetailView):
    model = TelegramUserModel
    template_name = ''
    context_object_name = 'telegram_user'