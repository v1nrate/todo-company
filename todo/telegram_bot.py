# todo/telegram_bot.py
import logging
from telegram import Update
from telegram.ext import Application
from django.conf import settings
from .bot import register_handlers, set_bot

logger = logging.getLogger(__name__)

def start_bot():
    try:
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        set_bot(application.bot)  # ← сохраняем ссылку на бота
        register_handlers(application)
        logger.info("✅ Запуск Telegram-бота...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.exception(f"❌ Ошибка запуска бота: {e}")