from django.urls import path
from . import views

app_name = 'todo'

urlpatterns = [
    # Users
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),

    # Tasks
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),

    # History
    path('history/', views.TaskHistoryListView.as_view(), name='history_list'),
    path('history/<int:pk>/', views.TaskHistoryDetailView.as_view(), name='history_detail'),

    # Telegram Users
    path('telegram-users/', views.TelegramUserListView.as_view(), name='telegram_user_list'),
    path('telegram-users/<int:pk>/', views.TelegramUserDetailView.as_view(), name='telegram_user_detail'),
    path('telegram-users/create/', views.TelegramUserCreateView.as_view(), name='telegram_user_create'),
]   