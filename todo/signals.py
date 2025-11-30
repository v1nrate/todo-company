from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TaskModel
import asyncio
from asgiref.sync import async_to_sync

@receiver(post_save, sender=TaskModel)
def send_telegram_notification_on_new_task(sender, instance, created, **kwargs):
    if created:
        # Запускаем асинхронную функцию в текущем event loop или создаём новый
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
