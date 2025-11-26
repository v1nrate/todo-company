# todo/bot.py
from asgiref.sync import sync_to_async
import logging
import os
import sys
from pathlib import Path
import django
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

logger = logging.getLogger(__name__)

# Настройка окружения Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo_comp.settings')
django.setup()

# ИМПОРТИРУЕМ МОДЕЛИ ТОЛЬКО ПОСЛЕ django.setup() ✅
from todo.models import TaskHistoryModel, UserModel, TelegramUserModel, TaskModel
from django.conf import settings

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

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
def link_telegram_user(user, telegram_id):
    TelegramUserModel.objects.update_or_create(
        user=user,
        defaults={'telegram_id': telegram_id, 'is_active': True}
    )
    user.telegram_link_code = None
    user.save()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    telegram_user = await get_telegram_user(telegram_id)

    if context.args:
        code = context.args[0]
        user = await get_user_by_code(code)
        if user:
            await link_telegram_user(user, telegram_id)
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

    # Всегда показываем главное меню
    await send_main_menu(update, context)

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

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📋 Мои задачи")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

@sync_to_async
def get_user_tasks(user):
    return list(TaskModel.objects.filter(
        assignee=user,
        status__in=['new', 'in_progress', 'overdue']  # ← включаем просроченные!
    ))

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
    
    if not telegram_user:
        await update.message.reply_text("Сначала привяжи Telegram через сайт.")
        return

    tasks_list = await get_user_tasks(telegram_user.user)
    if not tasks_list:
        await update.message.reply_text("У тебя нет активных задач.")
        return

    for task in tasks_list:
        # Кнопки под задачей
        keyboard = [
            [
                InlineKeyboardButton("✅ Завершить", callback_data=f"complete_{task.id}"),
                InlineKeyboardButton("📄 Подробнее", callback_data=f"detail_{task.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        msg = f"• *{task.title}*\nДедлайн: {task.deadline.strftime('%d.%m %Y %H:%M')}"
        await update.message.reply_text(
            msg,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

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

        msg = f"• *{task.title}*\nДедлайн: {task.deadline.strftime('%d.%m %Y %H:%M')}"
        await update.message.reply_text(
            msg,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

@sync_to_async
def unlink_telegram_user(telegram_id):
    try:
        telegram_user = TelegramUserModel.objects.get(telegram_id=telegram_id)
        telegram_user.delete()  # Или можно сделать is_active=False, если хочешь сохранять историю
        return True
    except TelegramUserModel.DoesNotExist:
        return False

@sync_to_async
def mark_task_completed_secure(task_id, user):
    try:
        task = TaskModel.objects.get(id=task_id)  # ← без проверки assignee
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

async def handle_task_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    telegram_id = str(update.effective_user.id)
    telegram_user = await get_telegram_user_with_user(telegram_id)

    if not telegram_user:
        await query.edit_message_text("❌ Аккаунт не привязан.")
        return

    user = telegram_user.user

    if data.startswith("complete_"):
        try:
            task_id = int(data.split("_")[1])
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Некорректный ID задачи.")
            return

        try:
            success = await mark_task_completed_secure(task_id, user)
            if success:
                await query.edit_message_text("✅ Задача отмечена как выполненная!")
            else:
                await query.edit_message_text("❌ Не удалось завершить задачу. Возможно, она уже завершена или назначена другому пользователю.")
        except Exception as e:
            logger.error(f"Ошибка при завершении задачи: {e}")
            await query.edit_message_text("Произошла ошибка. Попробуйте позже.")
        return

    elif data.startswith("detail_"):
        task_id = int(data.split("_")[1])
        task = await get_task_detail(task_id)
        if task:
            description = task.description or "Без описания"
            priority = task.get_priority_display()
            creator = task.created_by.first_name if task.created_by else "—"
            status = task.get_status_display()
            msg = (
                f"*{task.title}*\n\n"
                f"**Статус:** {status}\n"
                f"**Приоритет:** {priority}\n"
                f"**Создал:** {creator}\n"
                f"**Дедлайн:** {task.deadline.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"{description}"
            )

            keyboard = [
                [
                    InlineKeyboardButton("✅ Завершить", callback_data=f"complete_{task.id}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await query.edit_message_text("Задача не найдена.")
        return
    
async def unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    success = await unlink_telegram_user(telegram_id)
    if success:
        await update.message.reply_text("✅ Telegram успешно отвязан.")
    else:
        await update.message.reply_text("Вы не были привязаны к аккаунту.")


# todo/bot.py
def register_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("link", link))
    application.add_handler(MessageHandler(filters.Text("📋 Мои задачи"), show_tasks))
    application.add_handler(CommandHandler("unlink", unlink))
    application.add_handler(CallbackQueryHandler(handle_task_button))