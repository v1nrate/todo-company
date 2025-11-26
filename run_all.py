# run_all.py
import os
import sys
import threading
import django
from django.core.management import execute_from_command_line
from django.conf import settings

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo_comp.settings')
    django.setup()

    # Проверка: запускаем бота ТОЛЬКО в основном процессе (не в reloader)
    if os.environ.get('RUN_MAIN') != 'true':
        # Это reloader процесс — не запускаем бота
        execute_from_command_line([sys.argv[0], "runserver", "127.0.0.1:8000"])
        return

    # Это основной процесс — запускаем и бота, и сервер
    from todo.telegram_bot import start_bot
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

    execute_from_command_line([sys.argv[0], "runserver", "127.0.0.1:8000"])

if __name__ == "__main__":
    main()