# from django.db.models.signals import post_save
# from django.dispatch import receiver
#
# from .models import Enrollment
# # from telegram_bot.utils import send_telegram_message
#
#
# @receiver(post_save, sender=Enrollment)
# def enrollment_approved(sender, instance, created, **kwargs):
#     # ❗ faqat admin is_active=True qilganda
#     if not created and instance.is_active:
#         user = instance.user
#
#         if hasattr(user, "telegram_chat_id") and user.telegram_chat_id:
#             send_telegram_message(
#                 chat_id=user.telegram_chat_id,
#                 text=(
#                     "✅ <b>Siz kursga qabul qilindingiz!</b>\n\n"
#                     f"📘 Kurs: <b>{instance.course.title}</b>\n\n"
#                     "🎉 O‘qishni boshlashingiz mumkin!"
#                 )
#             )
