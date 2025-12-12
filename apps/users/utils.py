import requests
from django.conf import settings

TELEGRAM_BASE = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

def send_tg_message(chat_id, text):
    url = f"{TELEGRAM_BASE}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload , timeout=5)
    except Exception:
        pass
