from django.urls import path
from todo.forms import CustomAuthenticationForm
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView

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
    path('tasks/<int:pk>/complete/', views.complete_task, name='task_complete'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:file_id>/delete-file/', views.delete_file, name='delete_file'),
    path('api/tasks/', views.get_tasks_json, name='api_tasks'),
    
    # Calendar
    path('api/calendar-events/', views.get_calendar_events, name='calendar_events'),

    # History
    path('history/', views.TaskHistoryListView.as_view(), name='history_list'),

    # Telegram Users
    path('api/generate-telegram-link/', views.generate_telegram_link, name='generate_telegram_link'),
    path('unlink-telegram/', views.unlink_telegram, name='unlink_telegram'),

    # Login, Logout 
    path('login/', LoginView.as_view(
        template_name='todo/auth/login.html',
        authentication_form=CustomAuthenticationForm,
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

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