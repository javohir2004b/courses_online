# 🎓 Online Courses Platform + Telegram Bot

A full-featured **online education platform** built with **Django REST Framework** and an integrated **Telegram Bot** for user interaction, course enrollment, and admin approval workflows.

---

## 🚀 Features

### 🌐 Backend (Django REST)
- User authentication (JWT)
- Course catalog with categories
- Course enrollment system
- **Admin approval flow** for enrollments
- Course reviews & ratings
- Statistics dashboard
- PostgreSQL database
- Docker & Docker Compose support

### 🤖 Telegram Bot
- User registration & login
- Browse courses via Telegram
- Request course enrollment
- **Admin approval notification**
- Automatic user notification after approval
- View enrolled courses
- Leave course reviews
- Password reset flow

---

## 🧱 Tech Stack

- **Backend:** Django, Django REST Framework
- **Authentication:** JWT (SimpleJWT)
- **Database:** PostgreSQL
- **Bot:** python-telegram-bot (async)
- **Infrastructure:** Docker, Docker Compose
- **API Docs:** Swagger / drf-spectacular

---

## 📁 Project Structure

```text
courses_online/
├── apps/
│   ├── courses/
│   ├── users/
│   ├── payments/
│
├── telegram_bot/
│   ├── bot.py
│   └── utils.py
│
├── config/
│   ├── settings.py
│   └── urls.py
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── manage.py
