# todo/bot.py
from asgiref.sync import sync_to_async
import logging
from datetime import datetime
from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from django.conf import settings
from django.utils import timezone

# Импортируем модели — безопасно, т.к. Django уже инициализирован при импорте
from .models import UserModel, TelegramUserModel, TaskModel

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения бота — будет установлена из telegram_bot.py
_bot_instance = None

def set_bot(bot):
    """Вызывается один раз при запуске бота."""
    global _bot_instance
    _bot_instance = bot

def get_bot():
    return _bot_instance

# === Асинхронные обёртки для ORM ===

@sync_to_async
def get_telegram_user(telegram_id):
    try:
        return TelegramUserModel.objects.select_related('user').get(telegram_id=telegram_id)
    except TelegramUserModel.DoesNotExist:
        return None

@sync_to_async
def get_user_by_code(code):
    try:
        return UserModel.objects.get(telegram_link_code=code)
    except UserModel.DoesNotExist:
        return None

@sync_to_async
def link_telegram_user(user, telegram_id, username=None):
    TelegramUserModel.objects.update_or_create(
        user=user,
        defaults={
            'telegram_id': telegram_id,
            'username': username,  # ← сохраняем
            'is_active': True
        }
    )
    user.telegram_link_code = None
    user.save()

@sync_to_async
def get_user_tasks(user):
    return list(
        TaskModel.objects.filter(
            assignee=user,
            status__in=['new', 'in_progress', 'overdue']
        )
    )

@sync_to_async
def get_telegram_user_with_user(telegram_id):
    try:
        return TelegramUserModel.objects.select_related('user').get(telegram_id=telegram_id)
    except TelegramUserModel.DoesNotExist:
        return None

@sync_to_async
def unlink_telegram_user(telegram_id):
    try:
        TelegramUserModel.objects.get(telegram_id=telegram_id).delete()
        return True
    except TelegramUserModel.DoesNotExist:
        return False

@sync_to_async
def mark_task_completed(task_id):
    try:
        task = TaskModel.objects.get(id=task_id)
        task.status = 'completed'
        task.save()
        return True
    except TaskModel.DoesNotExist:
        return False

@sync_to_async
def get_task_detail(task_id):
    try:
        return TaskModel.objects.select_related('created_by').get(id=task_id)
    except TaskModel.DoesNotExist:
        return None

@sync_to_async
def get_assignee_telegram_id(user_id):
    try:
        telegram_user = TelegramUserModel.objects.get(user_id=user_id, is_active=True)
        return telegram_user.telegram_id
    except TelegramUserModel.DoesNotExist:
        return None

# === Обработчики команд и сообщений ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    effective_user = update.effective_user
    telegram_id = str(effective_user.id)
    username = effective_user.username  # Может быть None, если у пользователя нет юзернейма

    telegram_user = await get_telegram_user(telegram_id)

    if context.args:
        code = context.args[0]
        user = await get_user_by_code(code)
        if user:
            await link_telegram_user(user, telegram_id, username)
            await update.message.reply_text("✅ Telegram успешно привязан!")
        else:
            await update.message.reply_text("❌ Неверный или устаревший код.")
    else:
        if telegram_user:
            await update.message.reply_text(f"✅ Привет, {telegram_user.user.first_name}!")
        else:
            await update.message.reply_text(
                "Привет! Чтобы привязать аккаунт, откройте сайт и нажмите «Привязать Telegram»."
            )
    await send_main_menu(update, context)

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /link <код>")
        return

    code = context.args[0]
    telegram_id = str(update.effective_user.id)
    user = await get_user_by_code(code)

    if user:
        await link_telegram_user(user, telegram_id)
        await update.message.reply_text("✅ Telegram успешно привязан!")
    else:
        await update.message.reply_text("❌ Неверный или устаревший код.")

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("📋 Мои задачи")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    telegram_user = await get_telegram_user_with_user(telegram_id)

    if not telegram_user:
        await update.message.reply_text("Сначала привяжи Telegram через сайт.")
        return

    tasks_list = await get_user_tasks(telegram_user.user)
    if not tasks_list:
        await update.message.reply_text("У тебя нет активных задач.")
        return

    for task in tasks_list:
        keyboard = [
            [
                InlineKeyboardButton("✅ Завершить", callback_data=f"complete_{task.id}"),
                InlineKeyboardButton("📄 Подробнее", callback_data=f"detail_{task.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = (
            f"• *{task.title}*\n"
            f"Дедлайн: {timezone.localtime(task.deadline).strftime('%d.%m.%Y %H:%M')}"
        )
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_task_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    telegram_id = str(update.effective_user.id)
    telegram_user = await get_telegram_user_with_user(telegram_id)

    if not telegram_user:
        await query.edit_message_text("❌ Аккаунт не привязан.")
        return

    if data.startswith("complete_"):
        try:
            task_id = int(data.split("_")[1])
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Некорректный ID задачи.")
            return

        success = await mark_task_completed(task_id)
        if success:
            await query.edit_message_text("✅ Задача отмечена как выполненная!")
        else:
            await query.edit_message_text("❌ Задача не найдена.")

    elif data.startswith("detail_"):
        try:
            task_id = int(data.split("_")[1])
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Некорректный ID задачи.")
            return

        task = await get_task_detail(task_id)
        if not task:
            await query.edit_message_text("Задача не найдена.")
            return

        description = task.description or "Без описания"
        priority = task.get_priority_display()
        creator = task.created_by.first_name if task.created_by else "—"
        status = task.get_status_display()
        msg = (
            f"*{task.title}*\n\n"
            f"**Статус:** {status}\n"
            f"**Приоритет:** {priority}\n"
            f"**Создал:** {creator}\n"
            f"**Дедлайн:** {timezone.localtime(task.deadline).strftime('%d.%m.%Y %H:%M')}\n\n"
            f"{description}"
        )
        keyboard = [[InlineKeyboardButton("✅ Завершить", callback_data=f"complete_{task.id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

async def unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    success = await unlink_telegram_user(telegram_id)
    if success:
        await update.message.reply_text("✅ Telegram успешно отвязан.")
    else:
        await update.message.reply_text("Вы не были привязаны к аккаунту.")

# === Уведомления о новых задачах ===

async def notify_new_task(task_id):
    try:
        task = await sync_to_async(TaskModel.objects.select_related('assignee').get)(id=task_id)
        if not task.assignee:
            return

        telegram_id = await get_assignee_telegram_id(task.assignee.id)
        if not telegram_id:
            return

        bot = get_bot()
        if not bot:
            logger.warning("Bot not initialized — cannot send notification")
            return

        msg = (
            f"🆕 *Новая задача!*\n\n"
            f"*{task.title}*\n"
            f"Дедлайн: {timezone.localtime(task.deadline).strftime('%d.%m.%Y %H:%M')}"
        )
        await bot.send_message(chat_id=telegram_id, text=msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification for task {task_id}: {e}")

# === Регистрация обработчиков ===

def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("link", link))
    application.add_handler(CommandHandler("unlink", unlink))
    application.add_handler(MessageHandler(filters.Text("📋 Мои задачи"), show_tasks))
    application.add_handler(CallbackQueryHandler(handle_task_button))