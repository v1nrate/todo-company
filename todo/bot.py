# todo/bot.py
from asgiref.sync import sync_to_async
import logging
import os
import sys
from pathlib import Path
import django
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)

# Настройка окружения Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo_comp.settings')
django.setup()

# ИМПОРТИРУЕМ МОДЕЛИ ТОЛЬКО ПОСЛЕ django.setup() ✅
from todo.models import UserModel, TelegramUserModel, TaskModel
from django.conf import settings

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    
    # Проверяем, есть ли уже привязка
    try:
        telegram_user = TelegramUserModel.objects.get(telegram_id=telegram_id)
        await update.message.reply_text(f"✅ Вы уже привязаны как {telegram_user.user.first_name}!")
        return
    except TelegramUserModel.DoesNotExist:
        pass

    # Если передан код: /start ABC123
    if context.args:
        code = context.args[0]
        try:
            user = UserModel.objects.get(telegram_link_code=code)
            TelegramUserModel.objects.update_or_create(
                user=user,
                defaults={'telegram_id': telegram_id, 'is_active': True}
            )
            user.telegram_link_code = None
            user.save()
            await update.message.reply_text("✅ Telegram успешно привязан!")
        except UserModel.DoesNotExist:
            await update.message.reply_text("❌ Неверный или устаревший код.")
    else:
        # Без кода — просто инструкция
        await update.message.reply_text(
            "Привет! Чтобы привязать аккаунт, откройте сайт и нажмите «Привязать Telegram»."
        )

@sync_to_async
def get_user_by_code(code):
    try:
        return UserModel.objects.get(telegram_link_code=code)
    except UserModel.DoesNotExist:
        return None

@sync_to_async
def create_or_update_telegram_user(user, telegram_id):
    TelegramUserModel.objects.update_or_create(
        user=user,
        defaults={'telegram_id': telegram_id, 'is_active': True}
    )
    user.telegram_link_code = None
    user.save()

@sync_to_async
def invalidate_code(user):
    user.telegram_link_code = None
    user.save()

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Используй: /link <код>")
            return

        code = context.args[0]
        telegram_id = str(update.effective_user.id)

        # Асинхронно ищем пользователя по коду
        user = await get_user_by_code(code)

        if user:
            # Асинхронно привязываем Telegram и очищаем код
            await create_or_update_telegram_user(user, telegram_id)
            await update.message.reply_text("✅ Telegram успешно привязан!")
        else:
            await update.message.reply_text("❌ Неверный или устаревший код.")
    except Exception as e:
        logger.error(f"Ошибка привязки Telegram: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")

@sync_to_async
def get_user_tasks(user):
    return list(TaskModel.objects.filter(assignee=user))

@sync_to_async
def get_telegram_user_with_user(telegram_id):
    try:
        # Используем select_related для предварительной загрузки user
        return TelegramUserModel.objects.select_related('user').get(telegram_id=telegram_id)
    except TelegramUserModel.DoesNotExist:
        return None

async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    telegram_user = await get_telegram_user_with_user(telegram_id)
    
    if telegram_user:
        # Получаем user через связанное поле
        tasks_list = await get_user_tasks(telegram_user.user)
        if tasks_list:
            msg = "📋 Твои задачи:\n\n"
            for task in tasks_list:
                msg += f"• {task.title} (до {task.deadline.strftime('%d.%m %H:%M')})\n"
        else:
            msg = "У тебя нет активных задач."
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("Сначала привяжи Telegram через сайт.")

# Регистрация команд
def main():
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("link", link))
    application.add_handler(CommandHandler("tasks", tasks))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()