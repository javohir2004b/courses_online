from telegram import Bot
from django.conf import settings

bot = Bot(token=settings.TG_BOT_TOKEN)

def send_telegram_message(chat_id, text):
    bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML"
    )
