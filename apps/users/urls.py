from django.urls import path

from .views import RegisterView, LoginView, MeView, LogoutView, InstructorListAPIView, InstructorDetailAPIView, \
    ForgotPasswordEmailView, ResetPasswordWithCodeView
from .views_webhook import TelegramWebhookView

urlpatterns = [
    path('register/', RegisterView.as_view(), name="auth-register"),
    path('login/', LoginView.as_view(), name="auth-login"),
    path('me/', MeView.as_view(),name="auth-me"),
    path('logout/', LogoutView.as_view(),name="auth-logout"),
    path('instructors/', InstructorListAPIView.as_view(),name='instructor-list'),
    path('instructors/<int:pk>/', InstructorDetailAPIView.as_view(),name='instructor-detail'),
    path('auth/reset-code/', ForgotPasswordEmailView.as_view()),
    path('auth/reset-code/confirm/', ResetPasswordWithCodeView.as_view()),
    #TELEGRAM BOT UCHUN
    path("telegram/webhook/<str:secret>/", TelegramWebhookView.as_view(), name="tg-webhook"),
]