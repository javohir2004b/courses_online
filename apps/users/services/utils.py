import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_tg_message(
    chat_id: str,
    text: str,
    parse_mode: str = "HTML",
    disable_preview: bool = True,
    reply_markup: dict | None = None,
):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_preview,
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    r = requests.post(url, json=payload, timeout=5)
    return r.json()

def edit_tg_message(chat_id, message_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/editMessageText"

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(url, json=payload, timeout=5)



def answer_callback_query(callback_query_id: str):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery"

    payload = {
        "callback_query_id": callback_query_id
    }

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        logger.exception("TG callback answer error")
