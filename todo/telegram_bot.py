# todo/telegram_bot.py
import os
import sys
from pathlib import Path
import django
import logging

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo_comp.settings')
django.setup()

# ПРАВИЛЬНЫЕ ИМПОРТЫ
from telegram import Update  # ← из telegram, НЕ из telegram.ext
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from django.conf import settings
from .bot import register_handlers

logger = logging.getLogger(__name__)

def start_bot():
    try:
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        register_handlers(application)
        logger.info("✅ Запуск Telegram-бота...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.exception(f"❌ Ошибка запуска бота: {e}")