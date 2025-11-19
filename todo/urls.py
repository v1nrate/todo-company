from django.urls import path
from todo.forms import CustomAuthenticationForm
from . import views
from django.contrib.auth import views as auth_views

app_name = 'todo'

urlpatterns = [
    # Users
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),

    # Tasks
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),

    # History
    path('history/', views.TaskHistoryListView.as_view(), name='history_list'),
    path('history/<int:pk>/', views.TaskHistoryDetailView.as_view(), name='history_detail'),

    # Telegram Users
    path('telegram-users/', views.TelegramUserListView.as_view(), name='telegram_user_list'),
    path('telegram-users/<int:pk>/', views.TelegramUserDetailView.as_view(), name='telegram_user_detail'),
    path('telegram-users/create/', views.TelegramUserCreateView.as_view(), name='telegram_user_create'),

    # Login, Logout 
    path('login/', auth_views.LoginView.as_view(template_name='todo/auth/login.html', authentication_form=CustomAuthenticationForm), name='login'),
    path('login/', auth_views.LogoutView.as_view(), name='logout'),

    # Registration
    path('register/', views.register, name='register'),
    path('register/done', views.RegistrationDoneView.as_view(), name='registration_done'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    # Сброс пароля
     path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='todo/auth/password_reset_form.html',
             email_template_name='todo/auth/password_reset_email.html',
             subject_template_name='todo/auth/password_reset_subject.txt',
             success_url='/password-reset/done/'
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='todo/auth/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='todo/auth/password_reset_confirm.html',
             success_url='/reset/done/'
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='todo/auth/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]   