from django.core.mail import send_mail
from django.conf import settings


def send_reset_email(email: str, code: str) -> None:
    """
    Password reset code yuborish
    """
    send_mail(
        subject="Password Reset Code",
        message=f"Sizning parolni tiklash kodingiz: {code}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
