from django.conf import settings

def telegram_bot_username(request):
    return {'TELEGRAM_BOT_USERNAME': settings.TELEGRAM_BOT_USERNAME}