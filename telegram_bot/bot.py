import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, \
    ConversationHandler
from telegram.request import HTTPXRequest
import aiohttp
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Base URL
API_BASE_URL = os.getenv('API_BASE_URL', 'http://127.0.0.1:8000/api/v1')

ADMIN_CHAT_ID =8482885270
ADMIN_USERNAME = "@javohir_begmurotov"


# Conversation states
(WAITING_FOR_EMAIL, WAITING_FOR_PASSWORD, WAITING_FOR_NAME,
 WAITING_FOR_PHONE, WAITING_FOR_CONFIRM_PASSWORD,
 WAITING_FOR_RESET_CODE, WAITING_FOR_NEW_PASSWORD,
 WAITING_FOR_CONTACT_MESSAGE, WAITING_FOR_REVIEW_TEXT,
 WAITING_FOR_REVIEW_RATING, WAITING_FOR_RESET_EMAIL,
 WAITING_FOR_RESET_NEW_PASSWORD, BROWSING_COURSES, VIEWING_COURSE) = range(14)

# Timeout sozlamalari
request = HTTPXRequest(
    connection_pool_size=10,
    connect_timeout=60.0,
    read_timeout=60.0,
    write_timeout=60.0,
    pool_timeout=60.0
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class EduBot:
    def __init__(self, token: str):
        self.token = token
        self.user_sessions: Dict[int, Dict[str, Any]] = {}

    async def notify_admin(self, context, text: str):
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Admin notification error: {e}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        logger.info("START COMMAND RECEIVED!")
        user = update.effective_user
        user_id = user.id

        logger.info(f"User: {user.first_name}, ID: {user_id}")

        # Initialize user session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'logged_in': False,
                'token': None,
                'user_data': None
            }

        keyboard = [
            [KeyboardButton("📚 Kurslar"), KeyboardButton("👤 Profil")],
            [KeyboardButton("📝 Blog"), KeyboardButton("📞 Bog'lanish")],
            [KeyboardButton("📚 Mening kurslarim"), KeyboardButton("ℹ️ Yordam")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        welcome_text = f"""
👋 <b>Assalomu alaykum, {user.first_name}!</b>

🎓 <b>EduPress</b> - onlayn ta'lim platformasiga xush kelibsiz!

<b>Bizda siz:</b>
• Turli yo'nalishlardagi kurslarni topasiz
• Professional o'qituvchilardan bilim olasiz  
• Sertifikat olish imkoniyatiga ega bo'lasiz
• Blog orqali yangi bilimlar egallaysiz

📋 <b>Boshlash uchun:</b>
🔹 Agar akkountingiz bo'lmasa: /register
🔹 Tizimga kirish uchun: /login
🔹 Parolni unutdingizmi? /reset_password
🔹 Yordam uchun: /help

Pastdagi tugmalardan foydalaning 👇
        """

        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

    async def login_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start login process"""
        await update.message.reply_text(
            "🔐 <b>Tizimga kirish</b>\n\n"
            "📧 Email manzilingizni kiriting:",
            parse_mode='HTML'
        )
        return WAITING_FOR_EMAIL

    async def login_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle email input"""
        email = update.message.text

        if '@' not in email or '.' not in email:
            await update.message.reply_text(
                "❌ Noto'g'ri email format. Iltimos, qaytadan kiriting:"
            )
            return WAITING_FOR_EMAIL

        context.user_data['login_email'] = email
        await update.message.reply_text("🔑 Parolingizni kiriting:")
        return WAITING_FOR_PASSWORD

    async def login_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle password and complete login"""
        email = context.user_data.get('login_email')
        password = update.message.text

        await update.message.delete()

        loading_msg = await update.message.reply_text("⏳ Kirish...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{API_BASE_URL}/auth/login/",
                        json={'email': email, 'password': password}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        user_id = update.effective_user.id

                        self.user_sessions[user_id] = {
                            'logged_in': True,
                            'token': data.get('access'),
                            'refresh_token': data.get('refresh'),
                            'user_data': data.get('user')
                        }

                        await loading_msg.edit_text(
                            f"✅ <b>Muvaffaqiyatli kirdingiz!</b>\n\n"
                            f"👤 Ism: <b>{data.get('user', {}).get('full_name', 'N/A')}</b>\n"
                            f"📧 Email: <code>{email}</code>\n\n"
                            f"Endi barcha imkoniyatlardan foydalanishingiz mumkin!",
                            parse_mode='HTML'
                        )
                        return ConversationHandler.END
                    else:
                        error_data = await response.json()
                        await loading_msg.edit_text(
                            f"❌ <b>Xatolik:</b> {error_data.get('detail', 'Email yoki parol noto\'g\'ri')}\n\n"
                            f"Qaytadan urinib ko'ring: /login\n"
                            f"Parolni unutdingizmi? /reset_password",
                            parse_mode='HTML'
                        )
                        return ConversationHandler.END
        except Exception as e:
            logger.error(f"Login error: {e}")
            await loading_msg.edit_text(
                "❌ Serverga ulanishda xatolik. Keyinroq urinib ko'ring."
            )
            return ConversationHandler.END

    async def register_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start registration process"""
        await update.message.reply_text(
            "📝 <b>Ro'yxatdan o'tish</b>\n\n"
            "👤 To'liq ismingizni kiriting:",
            parse_mode='HTML'
        )
        return WAITING_FOR_NAME

    async def register_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle name input"""
        name = update.message.text

        if len(name) < 2:
            await update.message.reply_text(
                "❌ Ism juda qisqa. Iltimos, to'liq ismingizni kiriting:"
            )
            return WAITING_FOR_NAME

        context.user_data['register_name'] = name
        await update.message.reply_text("📧 Email manzilingizni kiriting:")
        return WAITING_FOR_EMAIL

    async def register_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle email input during registration"""
        email = update.message.text

        if '@' not in email or '.' not in email:
            await update.message.reply_text(
                "❌ Noto'g'ri email format. Iltimos, qaytadan kiriting:"
            )
            return WAITING_FOR_EMAIL

        context.user_data['register_email'] = email
        await update.message.reply_text(
            "🔑 Parol yarating (kamida 3 ta belgi):",
            parse_mode='HTML'
        )
        return WAITING_FOR_PASSWORD

    async def register_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle password input"""
        password = update.message.text

        await update.message.delete()

        if len(password) < 3:
            await update.message.reply_text(
                "❌ Parol juda qisqa. Kamida 3 ta belgi bo'lishi kerak:"
            )
            return WAITING_FOR_PASSWORD

        context.user_data['register_password'] = password
        await update.message.reply_text("🔑 Parolni tasdiqlang:")
        return WAITING_FOR_CONFIRM_PASSWORD

    async def register_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Complete registration"""
        password = context.user_data.get('register_password')
        confirm_password = update.message.text

        await update.message.delete()

        if password != confirm_password:
            await update.message.reply_text(
                "❌ Parollar mos kelmadi. Qaytadan urinib ko'ring: /register"
            )
            return ConversationHandler.END

        loading_msg = await update.message.reply_text("⏳ Ro'yxatdan o'tkazilmoqda...")

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'username': context.user_data.get('register_name'),
                    'email': context.user_data.get('register_email'),
                    'password': password,
                    'password2': confirm_password
                }

                async with session.post(
                        f"{API_BASE_URL}/auth/register/",
                        json=payload
                ) as response:
                    if response.status == 201:
                        await loading_msg.edit_text(
                            "✅ <b>Muvaffaqiyatli ro'yxatdan o'tdingiz!</b>\n\n"
                            "Endi tizimga kirish uchun /login buyrug'ini yuboring.",
                            parse_mode='HTML'
                        )
                        return ConversationHandler.END
                    else:
                        error_data = await response.json()
                        error_msg = "Ro'yxatdan o'tishda xatolik:\n"

                        if isinstance(error_data, dict):
                            for key, value in error_data.items():
                                if isinstance(value, list):
                                    error_msg += f"• {key}: {', '.join(value)}\n"
                                else:
                                    error_msg += f"• {key}: {value}\n"
                        else:
                            error_msg += str(error_data)

                        await loading_msg.edit_text(
                            f"❌ {error_msg}\n\nQaytadan urinib ko'ring: /register"
                        )
                        return ConversationHandler.END
        except Exception as e:
            logger.error(f"Registration error: {e}")
            await loading_msg.edit_text(
                "❌ Serverga ulanishda xatolik. Keyinroq urinib ko'ring."
            )
            return ConversationHandler.END

    # ========== PASSWORD RESET ==========
    async def reset_password_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start password reset process"""
        await update.message.reply_text(
            "🔐 <b>Parolni tiklash</b>\n\n"
            "📧 Ro'yxatdan o'tgan email manzilingizni kiriting:",
            parse_mode='HTML'
        )
        return WAITING_FOR_RESET_EMAIL

    async def reset_password_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send reset code to email"""
        email = update.message.text

        if '@' not in email or '.' not in email:
            await update.message.reply_text(
                "❌ Noto'g'ri email format. Qaytadan kiriting:"
            )
            return WAITING_FOR_RESET_EMAIL

        context.user_data['reset_email'] = email
        loading_msg = await update.message.reply_text("⏳ Kod yuborilmoqda...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{API_BASE_URL}/auth/auth/reset-code/",
                        json={'email': email}
                ) as response:
                    if response.status == 200:
                        await loading_msg.edit_text(
                            "✅ Tasdiqlash kodi emailingizga yuborildi!\n\n"
                            "📧 Emailingizni tekshiring va kodni kiriting:",
                            parse_mode='HTML'
                        )
                        return WAITING_FOR_RESET_CODE
                    else:
                        await loading_msg.edit_text(
                            "❌ Email topilmadi yoki xatolik yuz berdi.\n\n"
                            "Qaytadan urinib ko'ring: /reset_password"
                        )
                        return ConversationHandler.END
        except Exception as e:
            logger.error(f"Reset code error: {e}")
            await loading_msg.edit_text(
                "❌ Serverga ulanishda xatolik. Keyinroq urinib ko'ring."
            )
            return ConversationHandler.END

    async def reset_password_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Verify reset code"""
        code = update.message.text
        context.user_data['reset_code'] = code

        await update.message.reply_text(
            "🔑 Yangi parol yarating (kamida 8 ta belgi):",
            parse_mode='HTML'
        )
        return WAITING_FOR_RESET_NEW_PASSWORD

    async def reset_password_new(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Complete password reset"""
        new_password = update.message.text

        await update.message.delete()

        if len(new_password) < 8:
            await update.message.reply_text(
                "❌ Parol juda qisqa. Kamida 8 ta belgi bo'lishi kerak:"
            )
            return WAITING_FOR_RESET_NEW_PASSWORD

        loading_msg = await update.message.reply_text("⏳ Parol tiklanmoqda...")

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'email': context.user_data.get('reset_email'),
                    'code': context.user_data.get('reset_code'),
                    'password': new_password,
                    'confirm_password': new_password
                }

                async with session.post(
                        f"{API_BASE_URL}/auth/auth/reset-code/confirm/",
                        json=payload
                ) as response:
                    if response.status == 200:
                        await loading_msg.edit_text(
                            "✅ <b>Parol muvaffaqiyatli tiklandi!</b>\n\n"
                            "Endi tizimga kirish uchun /login buyrug'ini yuboring.",
                            parse_mode='HTML'
                        )
                        return ConversationHandler.END
                    else:
                        error_data = await response.json()
                        await loading_msg.edit_text(
                            f"❌ Xatolik: {error_data.get('detail', 'Kod noto\'g\'ri yoki muddati o\'tgan')}\n\n"
                            f"Qaytadan urinib ko'ring: /reset_password"
                        )
                        return ConversationHandler.END
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            await loading_msg.edit_text(
                "❌ Serverga ulanishda xatolik. Keyinroq urinib ko'ring."
            )
            return ConversationHandler.END

    async def get_courses(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get all courses - NO CATEGORIES"""
        loading_msg = await update.message.reply_text("⏳ Kurslar yuklanmoqda...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}/courses/") as response:
                    if response.status == 200:
                        courses = await response.json()

                        if not courses:
                            await loading_msg.edit_text("📚 Hozircha kurslar mavjud emas.")
                            return

                        text = "📚 <b>Barcha kurslar</b>\n\n"
                        text += f"Jami: <b>{len(courses)}</b> ta kurs\n\n"
                        keyboard = []

                        for i, course in enumerate(courses[:10], 1):
                            text += f"{i}. <b>{course.get('title')}</b>\n"
                            text += f"   👨‍🏫 {course.get('instructor_name', 'N/A')}\n"
                            text += f"   💰 {course.get('price')} so'm\n\n"

                            keyboard.append([
                                InlineKeyboardButton(
                                    f"📖 {course.get('title', 'N/A')[:30]}",
                                    callback_data=f"course_{course.get('slug')}"
                                )
                            ])

                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await loading_msg.edit_text(
                            text,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                    else:
                        await loading_msg.edit_text("❌ Kurslarni yuklashda xatolik.")
        except Exception as e:
            logger.error(f"Get courses error: {e}")
            await loading_msg.edit_text("❌ Serverga ulanishda xatolik.")

    async def course_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle course selection"""
        query = update.callback_query
        await query.answer()

        course_slug = query.data.split('_', 1)[1]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}/courses/{course_slug}/") as response:
                    if response.status == 200:
                        course = await response.json()

                        text = f"📚 <b>{course.get('title', 'N/A')}</b>\n\n"
                        text += f"📝 {course.get('description', course.get('short_description', 'Tavsif mavjud emas'))}\n\n"
                        text += f"💰 Narx: <b>{course.get('price', '0')} so'm</b>\n"
                        text += f"👨‍🏫 O'qituvchi: <b>{course.get('instructor_name', 'N/A')}</b>\n"
                        text += f"📊 Daraja: {course.get('level', 'N/A')}\n"
                        text += f"👥 Talabalar: {course.get('students_count', 0)}\n"
                        text += f"📚 Darslar: {course.get('lessons_count', 0)}\n"

                        keyboard = [
                            [InlineKeyboardButton("✍️ Ro'yxatdan o'tish", callback_data=f"enroll_{course_slug}")],
                            [InlineKeyboardButton("✏️ Sharh qoldirish", callback_data=f"write_review_{course_slug}")],
                            [InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_courses")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
                    else:
                        await query.edit_message_text("❌ Kurs ma'lumotlarini yuklashda xatolik.")
        except Exception as e:
            logger.error(f"Course callback error: {e}")
            await query.edit_message_text("❌ Serverga ulanishda xatolik.")

    async def show_reviews(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show course reviews - FIXED WITH SLUG"""
        query = update.callback_query
        await query.answer()

        course_slug = query.data.split('_', 1)[1]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}/courses/{course_slug}/reviews/") as response:
                    if response.status == 200:
                        reviews = await response.json()

                        if not reviews or len(reviews) == 0:
                            text = "💬 <b>Sharhlar</b>\n\nHali sharhlar yo'q. Birinchi bo'lib sharh qoldiring!"
                        else:
                            text = f"💬 <b>Sharhlar ({len(reviews)})</b>\n\n"
                            for i, review in enumerate(reviews[:10], 1):
                                stars = "⭐" * int(review.get('rating', 0))
                                text += f"{i}. {stars} ({review.get('rating', 0)}/5)\n"

                                # User info
                                user_info = review.get('user', 'Anonim')
                                if isinstance(user_info, dict):
                                    user_info = user_info.get('username', user_info.get('full_name', 'Anonim'))

                                text += f"   👤 {user_info}\n"
                                text += f"   💬 {review.get('comment', 'Sharh yo\'q')}\n"

                                created_at = review.get('created_at', '')
                                if created_at:
                                    text += f"   📅 {created_at[:10]}\n"
                                text += "\n"

                        keyboard = [
                            [InlineKeyboardButton("✏️ Sharh qoldirish", callback_data=f"write_review_{course_slug}")],
                            [InlineKeyboardButton("◀️ Orqaga", callback_data=f"course_{course_slug}")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
                    else:
                        await query.edit_message_text("❌ Sharhlarni yuklashda xatolik. Qaytadan urinib ko'ring.")
        except Exception as e:
            logger.error(f"Show reviews error: {e}")
            await query.edit_message_text("❌ Serverga ulanishda xatolik.")

    async def write_review_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start writing review"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id
        session_data = self.user_sessions.get(user_id, {})

        if not session_data.get('logged_in'):
            await query.edit_message_text(
                "❌ Sharh qoldirish uchun tizimga kirish kerak.\n\n"
                "Kirish: /login"
            )
            return

        course_slug = query.data.split('_', 2)[2]
        context.user_data['review_course_slug'] = course_slug

        keyboard = [
            [InlineKeyboardButton("⭐", callback_data="rating_1"),
             InlineKeyboardButton("⭐⭐", callback_data="rating_2"),
             InlineKeyboardButton("⭐⭐⭐", callback_data="rating_3")],
            [InlineKeyboardButton("⭐⭐⭐⭐", callback_data="rating_4"),
             InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="rating_5")],
            [InlineKeyboardButton("◀️ Bekor qilish", callback_data=f"course_{course_slug}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "⭐ <b>Sharh qoldirish</b>\n\n"
            "Kursga baho bering (1-5):",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return WAITING_FOR_REVIEW_RATING

    async def write_review_rating(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        rating = int(query.data.split('_')[1])
        context.user_data['review_rating'] = rating

        await query.edit_message_text(
            f"⭐️ Baho: {'⭐️' * rating}\n\n"
            "💬 Fikringizni yozing:",
            parse_mode='HTML'
        )

        return WAITING_FOR_REVIEW_TEXT

    async def write_review_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle review text and submit"""
        comment = update.message.text
        rating = context.user_data.get('review_rating')
        course_slug = context.user_data.get('review_course_slug')

        user_id = update.effective_user.id
        session_data = self.user_sessions.get(user_id, {})
        token = session_data.get('token')

        loading_msg = await update.message.reply_text("⏳ Sharh yuborilmoqda...")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {token}'}
                payload = {
                    'rating': rating,
                    'comment': comment
                }

                async with session.post(
                        f"{API_BASE_URL}/courses/{course_slug}/reviews/",
                        headers=headers,
                        json=payload
                ) as response:
                    if response.status == 201:
                        await loading_msg.edit_text(
                            "✅ <b>Sharh muvaffaqiyatli qoldirildi!</b>\n\n"
                            "Rahmat! 🙏",
                            parse_mode='HTML'
                        )
                    else:
                        await loading_msg.edit_text("❌ Sharhni kursga yozilgan user qoldira olad !.")
        except Exception as e:
            logger.error(f"Write review error: {e}")
            await loading_msg.edit_text("❌ Serverga ulanishda xatolik.")

        return ConversationHandler.END

    async def enroll_course(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer("⏳ So‘rov yuborilmoqda...")

        user_id = update.effective_user.id
        session_data = self.user_sessions.get(user_id, {})

        if not session_data.get("logged_in"):
            await query.edit_message_text(
                "❌ Kursga yozilish uchun tizimga kirish kerak.\n\n/login",
                parse_mode="HTML"
            )
            return

        course_slug = query.data.split("_", 1)[1]
        token = session_data.get("token")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{API_BASE_URL}/courses/{course_slug}/enrol/",
                        headers={"Authorization": f"Bearer {token}"}
                ) as response:

                    data = await response.json()

                    # ⏳ PENDING (ADMIN TASDIQLASHI KERAK)
                    if response.status == 200:
                        await query.edit_message_text(
                            "⏳ <b>So‘rov yuborildi</b>\n\n"
                            "Admin tasdiqlashini kuting.\n"
                            "Tasdiqlangach kurslaringizda paydo bo‘ladi.",
                            parse_mode="HTML"
                        )

                    # ✅ DARHOL YOZILDI (agar bo‘lsa)
                    elif response.status == 201:
                        await query.edit_message_text(
                            "✅ <b>Kursga muvaffaqiyatli yozildingiz!</b>\n\n"
                            "📚 Mening kurslarim bo‘limidan ko‘rishingiz mumkin.",
                            parse_mode="HTML"
                        )

                    elif response.status == 400:
                        await query.edit_message_text(
                            "⚠️ Siz allaqachon bu kursga so‘rov yuborgansiz."
                        )

                    else:
                        await query.edit_message_text(
                            f"❌ Xatolik (status: {response.status})"
                        )

        except Exception as e:
            logger.error(f"Enroll exception: {e}")
            await query.edit_message_text("❌ Server bilan bog‘lanishda xatolik.")

    async def my_courses(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's enrolled courses"""
        user_id = update.effective_user.id
        session_data = self.user_sessions.get(user_id, {})

        if not session_data.get('logged_in'):
            await update.message.reply_text(
                "❌ Kurslaringizni ko'rish uchun tizimga kirish kerak.\n\n"
                "Kirish: /login"
            )
            return

        loading_msg = await update.message.reply_text("⏳ Yuklanmoqda...")
        token = session_data.get('token')

        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {token}'}
                async with session.get(
                        f"{API_BASE_URL}/courses/enrol/my/",
                        headers=headers
                ) as response:
                    if response.status == 200:
                        enrollments = await response.json()

                        if not enrollments:
                            await loading_msg.edit_text(
                                "📚 Siz hali birorta kursga yozilmagansiz.\n\n"
                                "Kurslarni ko'rish: /courses"
                            )
                            return

                        text = "📚 <b>Mening kurslarim</b>\n\n"

                        for i, enroll in enumerate(enrollments, 1):
                            course = enroll.get('course', {})

                            text += f"{i}. <b>{course.get('title', 'Noma\'lum kurs')}</b>\n"
                            text += f"   👨‍🏫 O'qituvchi: {course.get('instructor_name', 'N/A')}\n"
                            text += f"   💰 Narx: {course.get('price', '0')} so'm\n"

                            enrolled_date = enroll.get('enrolled_at')
                            if enrolled_date:
                                text += f"   📅 Yozilgan: {enrolled_date[:10]}\n"

                            text += "\n"

                        await loading_msg.edit_text(text, parse_mode='HTML')
                    elif response.status == 401:
                        await loading_msg.edit_text(
                            "❌ Session muddati tugagan. Qaytadan kirish: /login"
                        )
                    else:
                        await loading_msg.edit_text("❌ Ma'lumotlarni yuklashda xatolik.")
        except Exception as e:
            logger.error(f"My courses error: {e}")
            await loading_msg.edit_text("❌ Serverga ulanishda xatolik.")

    async def get_payment_plans(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get payment plans"""
        loading_msg = await update.message.reply_text("⏳ Yuklanmoqda...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}/payments/plans/") as response:
                    if response.status == 200:
                        plans = await response.json()

                        if not plans:
                            await loading_msg.edit_text("💳 Hozircha to'lov rejalari mavjud emas.")
                            return

                        text = "💳 <b>To'lov Rejalari</b>\n\n"

                        for i, plan in enumerate(plans, 1):
                            text += f"{i}. <b>{plan.get('name', 'N/A')}</b>\n"
                            text += f"   💰 Narx: {plan.get('price', '0')} so'm\n"
                            text += f"   ⏱ Muddat: {plan.get('duration_days', 'N/A')} kun\n"
                            text += f"   📝 {plan.get('description', 'Tavsif yo\'q')}\n\n"

                        await loading_msg.edit_text(text, parse_mode='HTML')
                    else:
                        await loading_msg.edit_text("❌ Rejalarni yuklashda xatolik.")
        except Exception as e:
            logger.error(f"Get payment plans error: {e}")
            await loading_msg.edit_text("❌ Serverga ulanishda xatolik.")

    async def get_blog(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get blog posts"""
        loading_msg = await update.message.reply_text("⏳ Blog postlar yuklanmoqda...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}/blog/") as response:
                    if response.status == 200:
                        posts = await response.json()

                        if not posts:
                            await loading_msg.edit_text("📝 Hozircha blog postlar mavjud emas.")
                            return

                        text = "📝 <b>Blog postlar</b>\n\n"
                        keyboard = []

                        for i, post in enumerate(posts[:10], 1):
                            text += f"{i}. <b>{post.get('title', 'N/A')}</b>\n"
                            text += f"   📅 {post.get('created_at', 'N/A')[:10]}\n"
                            text += f"   👁 {post.get('views', 0)} ko'rildi\n\n"

                            keyboard.append([
                                InlineKeyboardButton(
                                    f"📖 {post.get('title', 'N/A')[:30]}",
                                    callback_data=f"blog_{post.get('slug')}"
                                )
                            ])

                        reply_markup = InlineKeyboardMarkup(keyboard)
                        await loading_msg.edit_text(
                            text,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                    else:
                        await loading_msg.edit_text("❌ Blog postlarni yuklashda xatolik.")
        except Exception as e:
            logger.error(f"Get blog error: {e}")
            await loading_msg.edit_text("❌ Serverga ulanishda xatolik.")

    async def blog_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle blog post selection"""
        query = update.callback_query
        await query.answer()

        slug = query.data.split('_', 1)[1]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE_URL}/blog/{slug}/") as response:
                    if response.status == 200:
                        post = await response.json()

                        text = f"📝 <b>{post.get('title', 'N/A')}</b>\n\n"
                        text += f"{post.get('content', 'Mazmun mavjud emas')[:500]}...\n\n"
                        text += f"📅 Sana: {post.get('created_at', 'N/A')[:10]}\n"
                        text += f"👁 Ko'rishlar: {post.get('views', 0)}\n"

                        keyboard = [
                            [InlineKeyboardButton("◀️ Orqaga", callback_data="back_to_blog")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        await query.edit_message_text(
                            text,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                    else:
                        await query.edit_message_text("❌ Post ma'lumotlarini yuklashda xatolik.")
        except Exception as e:
            logger.error(f"Blog callback error: {e}")
            await query.edit_message_text("❌ Serverga ulanishda xatolik.")

    async def profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user profile - NO MY_COURSES BUTTON"""
        user_id = update.effective_user.id
        session_data = self.user_sessions.get(user_id, {})

        if not session_data.get('logged_in'):
            await update.message.reply_text(
                "❌ Profilni ko'rish uchun tizimga kirish kerak.\n\n"
                "Kirish: /login"
            )
            return

        loading_msg = await update.message.reply_text("⏳ Yuklanmoqda...")
        token = session_data.get('token')

        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {token}'}
                async with session.get(
                        f"{API_BASE_URL}/auth/me/",
                        headers=headers
                ) as response:
                    if response.status == 200:
                        user_data = await response.json()

                        text = "👤 <b>Profil</b>\n\n"
                        text += f"Username: <b>{user_data.get('username', 'N/A')}</b>\n"
                        text += f"Email: <code>{user_data.get('email', 'N/A')}</code>\n"
                        text += f"Rol: <b>{user_data.get('role', 'student')}</b>\n"

                        # FAQAT CHIQISH TUGMASI
                        keyboard = [
                            [InlineKeyboardButton("🚪 Chiqish", callback_data="logout")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        await loading_msg.edit_text(
                            text,
                            reply_markup=reply_markup,
                            parse_mode='HTML'
                        )
                    else:
                        await loading_msg.edit_text("❌ Profil ma'lumotlarini yuklashda xatolik.")
        except Exception as e:
            logger.error(f"Profile error: {e}")
            await loading_msg.edit_text("❌ Serverga ulanishda xatolik.")

    async def logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Logout user"""
        query = update.callback_query
        await query.answer()

        user_id = update.effective_user.id

        if user_id in self.user_sessions:
            del self.user_sessions[user_id]

        await query.edit_message_text(
            "👋 Tizimdan chiqdingiz.\n\n"
            "Qayta kirish: /login"
        )

    async def contact_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show contact info"""
        contact_text = """
📞 <b>Bog'lanish</b>

Biz bilan bog'lanish uchun:

📱 Telefon: <code>+998991303032</code>
💬 Telegram: @javohir_begmurotov

Savollaringiz bo'lsa, bemalol murojaat qiling!
        """
        await update.message.reply_text(contact_text, parse_mode='HTML')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help"""
        help_text = """
ℹ️ <b>Yordam</b>

<b>📋 Mavjud buyruqlar:</b>

/start - Botni ishga tushirish
/login - Tizimga kirish
/register - Ro'yxatdan o'tish
/reset_password - Parolni tiklash
/courses - Kurslarni ko'rish
/payment_plans - To'lov rejalari
/blog - Blog postlarni ko'rish
/profile - Profilni ko'rish
/contact - Bog'lanish
/help - Yordam

<b>💡 Maslahatlar:</b>
• Har bir kursga sharh qoldirishingiz mumkin
• Blog orqali foydali maqolalarni o'qing
• Parolni unutsangiz /reset_password dan foydalaning

Savollaringiz bo'lsa /contact orqali murojaat qiling.
        """
        await update.message.reply_text(help_text, parse_mode='HTML')

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages from keyboard"""
        text = update.message.text

        if text == "📚 Kurslar":
            await self.get_courses(update, context)
        elif text == "👤 Profil":
            await self.profile(update, context)
        elif text == "📝 Blog":
            await self.get_blog(update, context)
        elif text == "📞 Bog'lanish":
            await self.contact_start(update, context)
        elif text == "ℹ️ Yordam":
            await self.help_command(update, context)
        elif text == "📚 Mening kurslarim":
            await self.my_courses(update, context)
        elif text == "🚪 Chiqish":
            user_id = update.effective_user.id
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            await update.message.reply_text("👋 Tizimdan chiqdingiz.\n\nQayta kirish: /login")

    async def back_to_courses(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back to courses button"""
        query = update.callback_query
        await query.answer()

        # Redirect to get_courses
        await query.message.delete()

        # Create a fake update for get_courses
        fake_update = Update(
            update_id=update.update_id,
            message=query.message
        )
        await self.get_courses(fake_update, context)

    async def back_to_blog(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle back to blog button"""
        query = update.callback_query
        await query.answer()

        # Redirect to get_blog
        await query.message.delete()

        # Create a fake update for get_blog
        fake_update = Update(
            update_id=update.update_id,
            message=query.message
        )
        await self.get_blog(fake_update, context)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        await update.message.reply_text("❌ Bekor qilindi.")
        return ConversationHandler.END


    def run(self):
        """Run the bot"""
        application = (
            Application.builder()
            .token(self.token)
            .request(request)
            .get_updates_request(request)
            .build()
        )

        # ==================================================
        # 🔥 CONVERSATION HANDLERS (AVVAL)
        # ==================================================

        # 🔐 Login conversation
        login_conv = ConversationHandler(
            entry_points=[CommandHandler("login", self.login_start)],
            states={
                WAITING_FOR_EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.login_email)
                ],
                WAITING_FOR_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.login_password)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # 📝 Registration conversation
        register_conv = ConversationHandler(
            entry_points=[CommandHandler("register", self.register_start)],
            states={
                WAITING_FOR_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_name)
                ],
                WAITING_FOR_EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_email)
                ],
                WAITING_FOR_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_password)
                ],
                WAITING_FOR_CONFIRM_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.register_confirm)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # 🔁 Password reset conversation
        reset_conv = ConversationHandler(
            entry_points=[CommandHandler("reset_password", self.reset_password_start)],
            states={
                WAITING_FOR_RESET_EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.reset_password_email)
                ],
                WAITING_FOR_RESET_CODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.reset_password_code)
                ],
                WAITING_FOR_NEW_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.reset_password_new)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # ⭐ Review / Rating conversation
        review_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.write_review_start, pattern="^write_review_")
            ],
            states={
                WAITING_FOR_REVIEW_RATING: [
                    CallbackQueryHandler(self.write_review_rating, pattern="^rating_")
                ],
                WAITING_FOR_REVIEW_TEXT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.write_review_text)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        # 👉 Conversation’larni ulaymiz (ENG MUHIM)
        application.add_handler(login_conv)
        application.add_handler(register_conv)
        application.add_handler(reset_conv)
        application.add_handler(review_conv)

        # ==================================================
        # 🔹 ODDIY COMMAND HANDLERS (KEYIN)
        # ==================================================

        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("courses", self.get_courses))
        application.add_handler(CommandHandler("blog", self.get_blog))
        application.add_handler(CommandHandler("profile", self.profile))
        application.add_handler(CommandHandler("payment_plans", self.get_payment_plans))
        application.add_handler(CommandHandler("contact", self.contact_start))

        # ==================================================
        # 🔘 CALLBACK QUERY HANDLERS
        # ==================================================

        application.add_handler(CallbackQueryHandler(self.course_callback, pattern="^course_"))
        application.add_handler(CallbackQueryHandler(self.enroll_course, pattern="^enroll_"))
        application.add_handler(CallbackQueryHandler(self.show_reviews, pattern="^reviews_"))
        application.add_handler(CallbackQueryHandler(self.blog_callback, pattern="^blog_"))
        application.add_handler(CallbackQueryHandler(self.back_to_courses, pattern="^back_to_courses$"))
        application.add_handler(CallbackQueryHandler(self.back_to_blog, pattern="^back_to_blog$"))
        application.add_handler(CallbackQueryHandler(self.logout, pattern="^logout$"))

        # ==================================================
        # 📨 TEXT HANDLER (ENG OXIRIDA)
        # ==================================================

        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)
        )

        # ==================================================
        # 🚀 START BOT
        # ==================================================

        logger.info("Bot ishga tushdi...")
        print("✅ Bot muvaffaqiyatli ishga tushdi!")
        print("🔹 Botni to'xtatish uchun Ctrl+C bosing")

        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    BOT_TOKEN = os.getenv('BOT_TOKEN')

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN topilmadi!")
        print("Iltimos, .env faylda BOT_TOKEN ni sozlang yoki bevosita kiriting:")
        BOT_TOKEN = input("Bot Token: ").strip()

    if BOT_TOKEN:
        bot = EduBot(BOT_TOKEN)
        bot.run()
    else:
        print("❌ Bot token kiritilmadi. Dastur to'xtatildi.")