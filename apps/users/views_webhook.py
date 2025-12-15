import json
import logging

from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.users.models import TelegramChat
from apps.users.services.telegram_router import route_telegram_update

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    """
    Telegram Webhook entrypoint
    """

    def post(self, request, secret: str):
        if secret != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning("Invalid TG webhook secret")
            return HttpResponseForbidden("Invalid secret")

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            logger.error("Invalid JSON from Telegram")
            return JsonResponse({"ok": False})

        try:
            route_telegram_update(payload)
        except Exception as exc:
            logger.exception("Telegram webhook processing error: %s", exc)
            # Telegram retry qilmasligi uchun 200 qaytaramiz
            return JsonResponse({"ok": True})

        return JsonResponse({"ok": True})
