import secrets
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView,TemplateView, UpdateView, DeleteView
from todo.forms import CommentForm, CustomUserCreationForm, TaskForm
from .models import TaskFile, UserModel, TaskModel, TelegramUserModel
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.contrib import messages
from django.http import JsonResponse


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Генерируем Telegram-код (как у тебя уже есть)
        if not user.telegram_link_code or (user.telegram_link_expires and timezone.now() > user.telegram_link_expires):
            user.telegram_link_code = secrets.token_urlsafe(16)
            user.telegram_link_expires = timezone.now() + timedelta(minutes=10)
            user.save()
        context['telegram_link_code'] = user.telegram_link_code

        # ДОБАВЛЯЕМ ТОЛЬКО АКТИВНЫЕ ЗАДАЧИ (не завершённые)
        context['active_tasks'] = self.object.tasks.exclude(status='completed')

        return context


class TaskListView(LoginRequiredMixin, ListView):
    model = TaskModel
    template_name = 'todo/tasks/list.html'
    context_object_name = 'tasks'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = TaskModel.objects.filter(
            assignee=user,
            status__in=['new', 'in_progress', 'overdue']
        )

        sort_by = self.request.GET.get('sort', '-created_at')
        valid_sort_fields = [
            'title', '-title',
            'created_at', '-created_at',
            'deadline', '-deadline',
            'status', '-status',
            'priority', '-priority',
            'assignee__first_name', '-assignee__first_name'
        ]
        if sort_by in valid_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Генерация календаря
        today = datetime.now().date()
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)

        # Собираем задачи по дням
        tasks = self.get_queryset().filter(deadline__gte=first_day_of_month, deadline__lte=last_day_of_month)
        calendar_tasks = defaultdict(list)
        for task in tasks:
            date_key = task.deadline.date()
            calendar_tasks[date_key].append(task)

        # Генерируем список дней месяца
        days_in_month = []
        current_day = first_day_of_month
        while current_day <= last_day_of_month:
            days_in_month.append(current_day)
            current_day += timedelta(days=1)

        context['calendar_days'] = {}
        for day in days_in_month:
            context['calendar_days'][day] = calendar_tasks[day]

        context['today'] = today
        return context

@method_decorator(never_cache, name='dispatch')
class TaskDetailView(DetailView):
    model = TaskModel
    template_name = 'todo/tasks/detail.html'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        return context

    def post(self, request, *args, **kwargs):
        task = self.get_object()

        # Проверка прав
        if not (request.user == task.assignee or request.user == task.created_by or request.user.role == 'manager'):
            messages.error(request, "У вас нет прав для загрузки файлов к этой задаче.")
            return redirect('todo:task_detail', pk=task.pk)

        # Обработка комментария (если есть поле 'text')
        if 'text' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.task = task
                comment.author = request.user
                comment.save()
                messages.success(request, "Комментарий добавлен.")
                return redirect('todo:task_detail', pk=task.pk)
            else:
                context = self.get_context_data()
                context['comment_form'] = form
                return self.render_to_response(context)

        # Обработка файлов (если есть загрузка)
        elif 'files' in request.FILES:
            files = request.FILES.getlist('files')  # ← принимает несколько файлов!
            for f in files:
                TaskFile.objects.create(task=task, file=f)
            messages.success(request, f"Загружено файлов: {len(files)}.")
            return redirect('todo:task_detail', pk=task.pk)

        else:
            messages.error(request, "Некорректный запрос.")
            return redirect('todo:task_detail', pk=task.pk)
    
class TaskCreateView(LoginRequiredMixin, CreateView):
    model = TaskModel
    template_name = 'todo/tasks/create.html'
    success_url = reverse_lazy('todo:task_list')
    form_class = TaskForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user  # ← auto-assign
        task = form.save()
        files = self.request.FILES.getlist('files')
        for f in files:
            TaskFile.objects.create(task=task, file=f)
        return super().form_valid(form)

class TaskHistoryListView(LoginRequiredMixin, ListView):
    model = TaskModel
    template_name = 'todo/history/list.html'
    context_object_name = 'tasks'  
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.role == 'employee':
            queryset = TaskModel.objects.filter(assignee=user)
        else:  # manager
            queryset = TaskModel.objects.all()

        # Добавляем сортировку
        sort_by = self.request.GET.get('sort', '-created_at')
        valid_sort_fields = [
            'title', '-title',
            'created_at', '-created_at',
            'deadline', '-deadline',
            'status', '-status',
            'priority', '-priority',
            'assignee__first_name', '-assignee__first_name'  # ← ДОБАВЛЕНО
        ]
        if sort_by in valid_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_completed'] = True  # ← флаг для шаблона
        context['title'] = "История задач"
        return context

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = TaskModel
    form_class = TaskForm
    template_name = "todo/tasks/update.html"
    success_url = reverse_lazy('todo:task_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        # Передаём существующие файлы
        data['existing_files'] = self.object.files.all()
        return data

    def form_valid(self, form):
        task = form.save()
        # Удаляем файлы, отмеченные для удаления
        for file in task.files.all():
            field_name = f"delete_file_{file.id}"
            if self.request.POST.get(field_name):
                file.delete()
        # Добавляем новые файлы
        files = self.request.FILES.getlist('files')
        for f in files:
            TaskFile.objects.create(task=task, file=f)
        return super().form_valid(form)

class TaskDeleteView(DeleteView):
    model = TaskModel
    template_name = "todo/tasks/delete.html"
    success_url = reverse_lazy('todo:task_list')


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
    
@login_required
def delete_file(request, file_id):
    try:
        file_obj = TaskFile.objects.get(pk=file_id)
        # Проверка доступа
        if request.user.role == 'employee' and file_obj.task.assignee != request.user:
            return JsonResponse({'success': False, 'error': 'Нет доступа'}, status=403)

        file_obj.delete()
        return JsonResponse({'success': True})
    except TaskFile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Файл не найден'}, status=404)
    
@login_required
def get_tasks_json(request):
    active_statuses = ['new', 'in_progress', 'overdue']  # ← ЗАВЕРШЁННЫЕ ИСКЛЮЧЕНЫ!
    if request.user.role == 'employee':
        tasks = TaskModel.objects.filter(assignee=request.user, status__in=active_statuses)
    else:  # manager
        tasks = TaskModel.objects.filter(status__in=active_statuses)

    # ДОБАВЬТЕ СОРТИРОВКУ
    sort_by = request.GET.get('sort', '-created_at')
    valid_sort_fields = [
        'title', '-title',
        'created_at', '-created_at',
        'deadline', '-deadline',
        'status', '-status',
        'priority', '-priority',
        'assignee__first_name', '-assignee__first_name'
    ]
    if sort_by in valid_sort_fields:
        tasks = tasks.order_by(sort_by)
    else:
        tasks = tasks.order_by('-created_at')
    
    tasks_data = []
    for task in tasks:
        task_dict = {
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'status_display': task.get_status_display(),
            'priority': task.priority,
            'priority_display': task.get_priority_display(),
            'created_by__first_name': task.created_by.first_name if task.created_by else "—",
            'deadline': timezone.localtime(task.deadline).strftime('%d.%m.%Y %H:%M'),
        }
        # Добавляем исполнителя ТОЛЬКО если пользователь — менеджер
        if request.user.role == 'manager':
            task_dict['assignee__first_name'] = task.assignee.first_name if task.assignee else "—"
        tasks_data.append(task_dict)

    return JsonResponse({
        'tasks': tasks_data,
        'user_is_manager': request.user.role == 'manager'  # ← добавляем флаг
    })

@login_required
def get_calendar_events(request):
    active_statuses = ['new', 'in_progress', 'overdue']
    if request.user.role == 'employee':
        tasks = TaskModel.objects.filter(assignee=request.user, status__in=active_statuses)
    else:
        tasks = TaskModel.objects.filter(status__in=active_statuses)

    events = []
    for task in tasks:
        events.append({
            'title': task.title,
            'start': task.deadline.isoformat(),  # FullCalendar требует ISO 8601
            'url': reverse_lazy('todo:task_detail', args=[task.id]),
            'backgroundColor': {
                'urgent': '#dc3545',
                'high': '#fd7e14',
                'medium': '#ffc107',
                'low': '#28a745'
            }.get(task.priority, '#6c757d'),
            'borderColor': 'transparent',
        })
    return JsonResponse(events, safe=False) 

@login_required
def complete_task(request, pk):
    try:
        task = TaskModel.objects.get(pk=pk)
        # Проверка: если сотрудник — может завершать только свои задачи
        if request.user.role == 'employee' and task.assignee != request.user:
            messages.error(request, "Вы не можете завершить чужую задачу.")
            return redirect('todo:task_list')
        
        task.status = 'completed'
        task.save()
        messages.success(request, f"Задача '{task.title}' успешно завершена!")
    except TaskModel.DoesNotExist:
        messages.error(request, "Задача не найдена.")
    
    return redirect('todo:task_list')

@login_required
def generate_telegram_link(request):
    if request.method == "POST":
        code = get_random_string(32)
        expires = timezone.now() + timedelta(minutes=10)
        request.user.telegram_link_code = code
        request.user.telegram_link_expires = expires
        request.user.save()
        return JsonResponse({'code': code})
    return JsonResponse({'error': 'Only POST'}, status=405)


@login_required
def unlink_telegram(request):
    try:
        telegram_profile = request.user.telegram_profile  # Теперь это объект!
        telegram_profile.delete()
        messages.success(request, "Telegram успешно отвязан.")
    except TelegramUserModel.DoesNotExist:
        messages.warning(request, "Telegram не был привязан.")
    return redirect('todo:user_detail', pk=request.user.pk)

def post(self, request, *args, **kwargs):
    task = self.get_object()
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()
        # Перенаправляем с параметром
        return redirect(f"{task.get_absolute_url()}?comment=added")
    # ...
