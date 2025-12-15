import re
from apps.users.services.courses import get_course_detail
from apps.users.services.utils import edit_tg_message
from apps.courses.models import Course
from apps.users.services.courses import get_courses_list
from apps.users.services.utils import send_tg_message

from apps.courses.models import Enrollment
from apps.users.services.courses import get_course_detail
from django.utils import timezone
from apps.users.services.utils import send_tg_message
from apps.users.models import TelegramChat, PasswordResetCode
from django.contrib.auth import get_user_model
User = get_user_model()
EMAIL_REGEX = r"[^@]+@[^@]+\.[^@]+"


def handle_command(tg_chat: TelegramChat, text: str) -> None:
    """
    Barcha / komandalar shu yerdan boshqariladi
    """
    parts = text.split()
    command = parts[0].lower()

    if command == "/start":
        start_command(tg_chat)
        return

    # keyin qo‘shamiz:
    # if command == "/reset":
    # if command == "/profile":
    # if command == "/courses":

    send_tg_message(
        tg_chat.chat_id,
        "❌ Noma’lum buyruq.\n\n"
        "Mavjud buyruqlar:\n"
        "/start — boshlash\n"
        "/reset — parolni tiklash",
    )


def start_command(tg_chat: TelegramChat, text: str) -> None:
    """
    /start komandasi
    """
    tg_chat.last_active = timezone.now()
    tg_chat.state = "started"
    tg_chat.save(update_fields=["last_active", "state"])

    message = (
        "👋 <b>Xush kelibsiz!</b>\n\n"
        "Bu — <b>Online Courses</b> platformasining rasmiy Telegram boti.\n\n"
        "📌 Bu yerda siz:\n"
        "• Kurslarni ko‘rishingiz\n"
        "• O‘qituvchilar bilan tanishishingiz\n"
        "• Parolni tiklashingiz\n"
        "• Obunalarni boshqarishingiz mumkin\n\n"
        "👉 Davom etish uchun buyruqlardan foydalaning:\n"
        "/login — tizimga kirish\n"
        "/reset — parolni tiklash\n"
        "/profile — profilingiz\n"
        "/courses — kurslar ro‘yxati\n"

    )

    send_tg_message(tg_chat.chat_id, message)


def register_command(tg_chat, text: str) -> None:
    """
    /register → email so‘raydi
    """
    tg_chat.state = "register_email"
    tg_chat.last_active = timezone.now()
    tg_chat.save(update_fields=["state", "last_active"])

    send_tg_message(
        tg_chat.chat_id,
        (
            "📝 <b>Ro‘yxatdan o‘tish</b>\n\n"
            "Email manzilingizni yuboring:\n"
            "Masalan: <code>example@gmail.com</code>"
        ),
    )


def profile_command(tg_chat: TelegramChat, text: str) -> None:
    user = getattr(tg_chat, "user", None)

    if not user:
        send_tg_message(
            tg_chat.chat_id,
            "❌ Siz hali akkaunt bilan bog‘lanmagansiz.\n\n"
            "👉 Parolni tiklash uchun:\n/reset email@example.com"
        )
        return

    message = (
        "👤 <b>Sizning profilingiz</b>\n\n"
        f"🆔 ID: {user.id}\n"
        f"📧 Email: {user.email}\n"
        f"👤 Username: {user.username}\n"
        f"📅 Ro‘yxatdan o‘tgan: {user.date_joined:%d.%m.%Y}\n"
    )

    tg_chat.last_active = timezone.now()
    tg_chat.save(update_fields=["last_active"])

    send_tg_message(tg_chat.chat_id, message)



def reset_command(tg_chat, text: str) -> None:
    tg_chat.state = "awaiting_reset_email"
    tg_chat.save(update_fields=["state"])

    send_tg_message(
        tg_chat.chat_id,
        "🔐 <b>Parolni tiklash</b>\n\n"
        "Email manzilingizni yuboring:"
    )



def yes_command(tg_chat: TelegramChat, text: str) -> None:
        if tg_chat.state != "awaiting_reset_confirm":
            send_tg_message(tg_chat.chat_id, "❗ Hozir tasdiqlash bosqichi yo‘q.")
            return

        email = tg_chat.temp_email

        # bu yerda email mavjudligini tekshirasan
        # PasswordResetCode yaratib emailga yuboramiz

        tg_chat.state = "awaiting_code"
        tg_chat.save(update_fields=["state"])

        send_tg_message(
            tg_chat.chat_id,
            (
                "📩 Emailga tasdiqlash kodi yuborildi.\n\n"
                "Kodni yuboring:\n"
                "<code>/code 123456</code>"
            )
        )


def no_command(tg_chat: TelegramChat, text: str) -> None:
    tg_chat.state = "new"
    tg_chat.temp_email = None
    tg_chat.save(update_fields=["state", "temp_email"])

    send_tg_message(
        tg_chat.chat_id,
        "❌ Bekor qilindi.\nQayta urinish uchun:\n<code>/reset email@example.com</code>"
    )




def login_command(tg_chat, text: str) -> None:
    tg_chat.state = "awaiting_login_email"
    tg_chat.save(update_fields=["state"])

    send_tg_message(
        tg_chat.chat_id,
        "🔐 <b>Kirish</b>\n\n"
        "Email manzilingizni yuboring:"
    )


#courses qismi
def courses_command(tg_chat, text: str) -> None:
    if not tg_chat.user:
        send_tg_message(
            tg_chat.chat_id,
            "❌ Kurslarni ko‘rish uchun avval /login qiling."
        )
        return

    courses = get_courses_list()
    if not courses:
        send_tg_message(
            tg_chat.chat_id,
            "📭 Hozircha kurslar mavjud emas."
        )
        return

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": course["title"],
                    "callback_data": f"course:{course['id']}"
                }
            ]
            for course in courses
        ]
    }

    send_tg_message(
        tg_chat.chat_id,
        "📚 <b>Kurslar ro‘yxati</b>\nKursni tanlang 👇",
        reply_markup=keyboard
    )




def course_detail_command(tg_chat, text: str) -> None:
    # 🔐 login tekshiruvi
    if not tg_chat.user:
        send_tg_message(
            tg_chat.chat_id,
            "❌ Kursni ko‘rish uchun avval /login qiling."
        )
        return

    # /course_12 → 12
    try:
        course_id = int(text.split("_")[1])
    except (IndexError, ValueError):
        send_tg_message(
            tg_chat.chat_id,
            "❌ Noto‘g‘ri format.\nMisol: /course_1"
        )
        return

    from apps.users.services.courses import get_course_detail

    course = get_course_detail(course_id)
    if not course:
        send_tg_message(
            tg_chat.chat_id,
            "❌ Bunday kurs topilmadi."
        )
        return

    message = (
        f"📘 <b>{course.title}</b>\n\n"
        f"📝 {course.short_description or course.description}\n\n"
        f"💰 Narxi: {course.price} so‘m\n"
        f"📊 Daraja: {course.level}\n"
        f"👨‍🏫 O‘qituvchi: {course.instructor}\n"
        f"🎓 O‘quvchilar: {course.students_count}\n"
    )

    send_tg_message(tg_chat.chat_id, message)

from apps.courses.models import Course
from apps.users.services.utils import send_tg_message



def course_detail_by_id(tg_chat, course_id: int, message_id: int):

    course = get_course_detail(course_id)
    if not course:
        edit_tg_message(
            tg_chat.chat_id,
            message_id,
            "❌ Kurs topilmadi"
        )
        return

    text = (
        f"📘 <b>{course.title}</b>\n\n"
        f"💰 Narxi: {course.price} so‘m\n\n"
        f"📝 {course.description or '—'}"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "⬅️ Orqaga", "callback_data": "courses_back"}]
        ]
    }

    edit_tg_message(
        tg_chat.chat_id,
        message_id,
        text,
        reply_markup=keyboard
    )




def enroll_course_command(tg_chat, course_id: int):
    if not tg_chat.user:
        send_tg_message(
            tg_chat.chat_id,
            "❌ Avval /login qiling."
        )
        return

    obj, created = Enrollment.objects.get_or_create(
        user=tg_chat.user,
        course_id=course_id
    )

    if not created:
        send_tg_message(
            tg_chat.chat_id,
            "ℹ️ Siz allaqachon bu kursga yozilgansiz."
        )
        return

    send_tg_message(
        tg_chat.chat_id,
        "✅ <b>Kursga muvaffaqiyatli yozildingiz!</b>"
    )

