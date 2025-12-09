from django.urls import path
from .views import RegisterView, LoginView, MeView, LogoutView, InstructorListAPIView, InstructorDetailSerializer, \
    InstructorDetailAPIView, ForgotPasswordAPIView, ResetPasswordAPIView

urlpatterns = [
    path('register/', RegisterView.as_view(), name="auth-register"),
    path('login/', LoginView.as_view(), name="auth-login"),
    path('me/', MeView.as_view(),name="auth-me"),
    path('logout/', LogoutView.as_view(),name="auth-logout"),
    path('instructors/', InstructorListAPIView.as_view(),name='instructor-list'),
    path('instructors/<int:pk>/', InstructorDetailAPIView.as_view(),name='instructor-detail'),
    path('forgot-password/', ForgotPasswordAPIView.as_view(),name='forgot-password'),
    path('reset-password/', ResetPasswordAPIView.as_view(),name='reset-password'),
]