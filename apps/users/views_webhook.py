import json
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model

from apps.users.models import Telegramchat, PasswordResetCode  # agar nomlar boshqacha bo'lsa o'zgartiring
from apps.users.utils import send_tg_message  # agar nom boshqacha bo'lsa moslashtiring

User = get_user_model()

@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    """
    Telegram webhook uchun class-based view.
    CSRF exempt qilingan — chunki Telegram POST so'rov yuboradi.
    URLda secret tekshiriladi: /api/v1/auth/telegram/webhook/<secret>/
    """

    def post(self, request, secret):
        # 1) secret tekshiruvi
        expected = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)
        if expected and secret != expected:
            return HttpResponseForbidden("invalid secret")

        # 2) request body parse
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"ok": False, "detail": "invalid json"}, status=400)

        message = payload.get("message") or payload.get("edited_message")
        if not message:
            return JsonResponse({"ok": True})  # boshqa update turlari ham bo'lishi mumkin

        chat = message.get("chat", {})
        chat_id = str(chat.get("id"))
        text = (message.get("text") or "").strip()

        # 3) Telegram chat yozuvi (yoki yarat)
        tg_chat, created = Telegramchat.objects.get_or_create(chat_id=chat_id)

        # 4) komandalarni ajratish
        parts = text.split()
        cmd = parts[0].lower() if parts else ""

        # STATES: 'awaiting_code', 'awaiting_new_password'
        if cmd == "/start":
            send_tg_message(chat_id, "Salom! Parolingizni tiklash uchun /reset <email> yuboring.")
            return JsonResponse({"ok": True})

        if cmd == "/reset" and len(parts) >= 2:
            email = parts[1]
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                send_tg_message(chat_id, "Bunday email ro'yxatda topilmadi.")
                return JsonResponse({"ok": True})

            reset = PasswordResetCode.objects.create(user=user)
            tg_chat.state = "awaiting_code"
            tg_chat.temp_token = str(reset.token)
            tg_chat.user = user
            tg_chat.save()

            # (email yuborishning alohida logikasi mavjud bo'lishi kerak — bu yerda faqat botga xabar)
            send_tg_message(chat_id, "Emailga reset kodi yuborildi. Emaildagi tokenni /code <token> bilan yuboring.")
            return JsonResponse({"ok": True})

        if cmd == "/code" and len(parts) >= 2:
            token = parts[1]
            try:
                reset = PasswordResetCode.objects.get(token=token)
            except PasswordResetCode.DoesNotExist:
                send_tg_message(chat_id, "Token noto'g'ri yoki muddati o'tgan.")
                return JsonResponse({"ok": True})

            tg_chat.state = "awaiting_new_password"
            tg_chat.temp_token = token
            tg_chat.user = reset.user
            tg_chat.save()

            send_tg_message(chat_id, "Token tasdiqlandi. Yangi parolni quyidagicha yuboring:\n/newpass <yangi_parol> <confirm_parol>")
            return JsonResponse({"ok": True})

        if cmd == "/newpass" and len(parts) >= 3:
            new_pass = parts[1]
            confirm = parts[2]

            if new_pass != confirm:
                send_tg_message(chat_id, "Parollar mos emas. Iltimos qaytadan urinib ko'ring.")
                return JsonResponse({"ok": True})

            if len(new_pass) < 6:
                send_tg_message(chat_id, "Parol kamida 6 ta belgidan iborat bo'lishi kerak.")
                return JsonResponse({"ok": True})

            # state tekshiruvi - mos nomlar bilan
            if tg_chat.state != "awaiting_new_password" or not tg_chat.temp_token:
                send_tg_message(chat_id, "Siz tokenni hali yubormagansiz. Avval /reset <email> va /code <token> bajaring.")
                return JsonResponse({"ok": True})

            try:
                reset = PasswordResetCode.objects.get(token=tg_chat.temp_token)
            except PasswordResetCode.DoesNotExist:
                send_tg_message(chat_id, "Token topilmadi yoki muddati o'tgan.")
                return JsonResponse({"ok": True})

            # parolni o'zgartirish
            u = reset.user
            u.set_password(new_pass)
            u.save()

            # belgilash (agar modelda mavjud bo'lsa)
            reset.used = True
            reset.used_at = timezone.now()
            reset.save()

            # chat state tozalash
            tg_chat.state = ""
            tg_chat.temp_token = ""
            tg_chat.save()

            send_tg_message(chat_id, "Parolingiz muvaffaqiyatli yangilandi. Endi odatdagi tarzda tizimga kiring.")
            return JsonResponse({"ok": True})

        # default javob
        send_tg_message(chat_id, "Noma'lum buyruq. Parol tiklash uchun: /reset <email>")
        return JsonResponse({"ok": True})
