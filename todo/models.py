from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Create your models here.
class UserModel(AbstractUser):
    ROLE_CHOICES = [
        ('employee', 'Сотрудник'),
        ('manager', 'Руководитель'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee', verbose_name='Роль')
    email = models.EmailField(unique=True, verbose_name='Email')
    telegram_link_code = models.CharField(max_length=32, blank=True, null=True, unique=True)
    telegram_link_expires = models.DateTimeField(blank=True, null=True)
    
    @property
    def completed_tasks_count(self):
        return self.tasks.filter(status='completed').count()

    @property
    def in_progress_tasks_count(self):
        return self.tasks.filter(status='in_progress').count()

    @property
    def overdue_tasks_count(self):
        return self.tasks.filter(status='overdue').count()

    def __str__(self):
        return f"{self.first_name} ({self.get_role_display()})"
    
class TaskModel(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочно'),
    ]

    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершена'),
        ('overdue', 'Просрочена'),
    ]

    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    assignee = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="tasks", verbose_name="Исполнитель")
    created_by = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, related_name="created_tasks", verbose_name="Создал")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    deadline = models.DateTimeField(verbose_name="Дедлайн")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name="Приоритет")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='new', verbose_name='Статус')

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title} → {self.assignee}"
    
    def save(self, *args, **kwargs):
        logger.info(f"Сохраняем задачу {self.id}: status={self.status}, deadline={self.deadline}, now={timezone.now()}")
        if self.deadline < timezone.now() and self.status != 'completed':
            logger.info(f"Задача {self.id} просрочена → меняем статус на 'overdue'")
            self.status = 'overdue'
        super().save(*args, **kwargs)

class TaskHistoryModel(models.Model):
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name='history', verbose_name='Задачи')
    changed_by = models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, verbose_name='Изменил')
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата изменения")
    field_changed = models.CharField(max_length=50, verbose_name='Поле')
    old_value = models.TextField(blank=True, verbose_name='Старое значение')
    new_value = models.TextField(blank=True, verbose_name='Новое значение')
    reason = models.TextField(verbose_name='Причина изменения (например, перенос дедлайна)', blank=True)

    class Meta:
        verbose_name = "История задачи"
        verbose_name_plural = "Истории задач"
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.task.title} - {self.field_changed} ({self.changed_at})"
    
class TelegramUserModel(models.Model):
    user = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name="telegram_profile", null=True, blank=True)
    telegram_id = models.CharField(max_length=50, unique=True, verbose_name="Telegram ID")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    last_notification = models.DateTimeField(null=True, blank=True, verbose_name="Последнее уведомление")

    class Meta:
        verbose_name = "Telegram-пользователь"
        verbose_name_plural = "Telegram-пользователи"

    def __str__(self):
        return f"{self.user.username} → {self.telegram_id}"
    
class TaskFile(models.Model):
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name='files', verbose_name='Задача')
    file = models.FileField(upload_to='task_files/', verbose_name='Файл')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Загружен')

    def __str__(self):
        return self.file.name