from django.urls import path
from . import views

urlpatterns = [
    # Users
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),

    # Tasks
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),

    # History
    path('history/', views.TaskHistoryListView.as_view(), name='history_list'),
    path('history/<int:pk>/', views.TaskHistoryDetailView.as_view(), name='history_detail'),

    # Telegram Users
    path('telegram-users/', views.TelegramUserListView.as_view(), name='telegram_user_list'),
    path('telegram-users/<int:pk>/', views.TelegramUserDetailView.as_view(), name='telegram_user_detail'),
]