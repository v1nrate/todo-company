from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TaskModel
from .bot import notify_new_task
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

        if loop.is_running():
            # Если уже запущен (например, в боевом ASGI), отправляем через create_task
            loop.create_task(notify_new_task(instance.id))
        else:
            # Иначе — запускаем синхронно (например, в админке или shell)
            async_to_sync(notify_new_task)(instance.id)