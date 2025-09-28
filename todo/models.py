from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.
class UserModel(AbstractUser):
    ROLE_CHOICES = [
        ('employee', 'Сотрудник'),
        ('manager', 'Руководитель'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee', verbose_name='Роль')
    telegram_id = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name='Телеграм ИД')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
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
        if self.deadline < timezone.now() and self.status != 'completed':
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
    user = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name="telegram_profile")
    telegram_id = models.CharField(max_length=50, unique=True, verbose_name="Telegram ID")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    last_notification = models.DateTimeField(null=True, blank=True, verbose_name="Последнее уведомление")

    class Meta:
        verbose_name = "Telegram-пользователь"
        verbose_name_plural = "Telegram-пользователи"

    def __str__(self):
        return f"{self.user.username} → {self.telegram_id}"