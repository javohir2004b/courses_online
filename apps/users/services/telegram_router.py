from apps.users.models import TelegramChat
from apps.users.services.utils import send_tg_message, answer_callback_query
from apps.users.services.telegram_flows import handle_text_flow
from apps.users.services.telegram_commands import (
    start_command,
    reset_command,
    login_command,
    profile_command,
    courses_command,
)

COMMAND_HANDLERS = {
    "/start": start_command,
    "/reset": reset_command,
    "/login": login_command,
    "/profile": profile_command,
    "/courses": courses_command,
}

def route_telegram_update(payload: dict) -> None:

    # =======================
    # 1️⃣ INLINE CALLBACK
    # =======================
    callback = payload.get("callback_query")
    if callback:
        callback_id = callback.get("id")
        data = callback.get("data")

        message = callback.get("message", {})
        chat = message.get("chat", {})
        chat_id = str(chat.get("id"))

        tg_chat, _ = TelegramChat.objects.get_or_create(chat_id=chat_id)

        # 🔴 MUHIM: loadingni darhol yopadi
        if callback_id:
            answer_callback_query(callback_id)

        if data and data.startswith("course:"):
            from apps.users.services.telegram_commands import course_detail_by_id
            course_id = int(data.split(":")[1])
            course_detail_by_id(tg_chat, course_id)

        if data == "courses_back":
            courses_command(tg_chat, "/courses")

        return

    # =======================
    # 2️⃣ ODDIY MESSAGE
    # =======================
    message = payload.get("message") or payload.get("edited_message")
    if not message:
        return

    text = (message.get("text") or "").strip()
    chat = message.get("chat", {})
    chat_id = str(chat.get("id"))

    tg_chat, _ = TelegramChat.objects.get_or_create(chat_id=chat_id)

    if text.startswith("/"):
        command = text.split()[0].split("@")[0]
        handler = COMMAND_HANDLERS.get(command)
        if handler:
            handler(tg_chat, text)
        else:
            send_tg_message(chat_id, "❓ Noma’lum buyruq.\n/start")
    else:
        handle_text_flow(tg_chat, text)
