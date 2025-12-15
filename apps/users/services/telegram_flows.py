from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.users.models import PasswordResetCode
from apps.users.services.emails import send_reset_email

from apps.users.services.utils import send_tg_message
from apps.users.models import TelegramChat

User = get_user_model()


def handle_text_flow(tg_chat: TelegramChat, text: str) -> None:
    """
    Telegram text flow (state machine)
    """

    # =======================
    # 🔐 RESET PASSWORD FLOW
    # =======================

    # 1️⃣ EMAIL QABUL QILISH
    if tg_chat.state == "awaiting_reset_email":
        try:
            validate_email(text)
        except ValidationError:
            send_tg_message(
                tg_chat.chat_id,
                "❌ Email noto‘g‘ri. Qayta urinib ko‘ring.",
            )
            return

        tg_chat.temp_email = text
        tg_chat.state = "awaiting_reset_confirm"
        tg_chat.last_active = timezone.now()
        tg_chat.save(update_fields=["temp_email", "state", "last_active"])

        send_tg_message(
            tg_chat.chat_id,
            (
                f"📧 Email qabul qilindi: <code>{text}</code>\n\n"
                "Davom etamizmi?\n"
                "Tasdiqlash uchun <b>ha</b>\n"
                "Bekor qilish uchun <b>yo‘q</b>"
            ),
        )
        return

    # 2️⃣ TASDIQLASH (HA / YO‘Q)
    if tg_chat.state == "awaiting_reset_confirm":
        if text.lower() != "ha":
            send_tg_message(
                tg_chat.chat_id,
                "❌ Parolni tiklash bekor qilindi.\n"
                "/reset orqali qayta boshlashingiz mumkin.",
            )
            tg_chat.state = "new"
            tg_chat.save(update_fields=["state"])
            return

        user = User.objects.filter(email=tg_chat.temp_email).first()
        if not user:
            send_tg_message(
                tg_chat.chat_id,
                "❌ Bunday email bilan foydalanuvchi topilmadi.",
            )
            tg_chat.state = "new"
            tg_chat.save(update_fields=["state"])
            return

        reset = PasswordResetCode.objects.create(user=user)

        tg_chat.state = "awaiting_reset_code"
        tg_chat.last_active = timezone.now()
        tg_chat.save(update_fields=["state", "last_active"])

        send_reset_email(user.email, reset.code)

        send_tg_message(
            tg_chat.chat_id,
            "📩 Email manzilingizga tasdiqlash kodi yuborildi.\n\n"
            "Iltimos, kodni shu yerga yuboring:",
        )
        return

    # 3️⃣ KODNI TEKSHIRISH
    if tg_chat.state == "awaiting_reset_code":
        reset = PasswordResetCode.objects.filter(
            code=text,
            used=False
        ).first()

        if not reset:
            send_tg_message(
                tg_chat.chat_id,
                "❌ Kod noto‘g‘ri yoki eskirgan. Qayta urinib ko‘ring.",
            )
            return

        reset.used = True
        reset.save(update_fields=["used"])

        tg_chat.user = reset.user
        tg_chat.state = "awaiting_reset_new_password"
        tg_chat.last_active = timezone.now()
        tg_chat.save(update_fields=["user", "state", "last_active"])

        send_tg_message(
            tg_chat.chat_id,
            (
                "🔑 Yangi parolni yuboring.\n"
                "Format:\n"
                "<code>parol parol</code>"
            ),
        )
        return

    # 4️⃣ YANGI PAROL
    if tg_chat.state == "awaiting_reset_new_password":
        parts = text.split()
        if len(parts) != 2 or parts[0] != parts[1]:
            send_tg_message(
                tg_chat.chat_id,
                "❌ Parollar mos emas. Qayta urinib ko‘ring.",
            )
            return

        user = tg_chat.user
        user.set_password(parts[0])
        user.save()

        tg_chat.state = "new"
        tg_chat.temp_email = None
        tg_chat.last_active = timezone.now()
        tg_chat.save(update_fields=["state", "temp_email", "last_active"])

        send_tg_message(
            tg_chat.chat_id,
            "✅ <b>Parol muvaffaqiyatli yangilandi!</b>\n\n"
            "/login orqali tizimga kirishingiz mumkin.",
        )
        return

    # =======================
    # 🔑 LOGIN FLOW (OTP)
    # =======================

    # 1️⃣ EMAIL QABUL QILISH
    if tg_chat.state == "awaiting_login_email":
        try:
            validate_email(text)
        except ValidationError:
            send_tg_message(
                tg_chat.chat_id,
                "❌ Email noto‘g‘ri. Qayta urinib ko‘ring.",
            )
            return

        user = User.objects.filter(email=text).first()
        if not user:
            send_tg_message(
                tg_chat.chat_id,
                "❌ Bunday email bilan foydalanuvchi topilmadi.",
            )
            tg_chat.state = "new"
            tg_chat.save(update_fields=["state"])
            return

        from apps.users.models import LoginOTP
        from apps.users.services.otp import generate_otp

        otp_code = generate_otp()
        LoginOTP.objects.create(user=user, code=otp_code)

        send_reset_email(user.email, otp_code)

        tg_chat.user = user
        tg_chat.state = "awaiting_login_code"
        tg_chat.last_active = timezone.now()
        tg_chat.save(update_fields=["user", "state", "last_active"])

        send_tg_message(
            tg_chat.chat_id,
            "📩 Gmail’ga kirish kodi yuborildi.\n"
            "Iltimos, kodni shu yerga yuboring:",
        )
        return

    # 2️⃣ OTP TEKSHIRISH
    if tg_chat.state == "awaiting_login_code":
        from apps.users.models import LoginOTP

        otp = LoginOTP.objects.filter(
            user=tg_chat.user,
            code=text,
            is_used=False
        ).order_by("-created_at").first()

        if not otp:
            send_tg_message(
                tg_chat.chat_id,
                "❌ Kod noto‘g‘ri. Qayta urinib ko‘ring.",
            )
            return

        if otp.is_expired():
            send_tg_message(
                tg_chat.chat_id,
                "⏰ Kod muddati tugagan.\n"
                "/login orqali qayta urinib ko‘ring.",
            )
            tg_chat.state = "new"
            tg_chat.save(update_fields=["state"])
            return

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        tg_chat.state = "registered"
        tg_chat.last_active = timezone.now()
        tg_chat.save(update_fields=["state", "last_active"])

        send_tg_message(
            tg_chat.chat_id,
            "✅ <b>Muvaffaqiyatli tizimga kirdingiz!</b>\n\n"
            "/profile orqali profilingizni ko‘rishingiz mumkin.",
        )
        return

