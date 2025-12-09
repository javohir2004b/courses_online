from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

from .models import PasswordReset ,User
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, LogoutSerializer, \
    InstructorDetailSerializer, InstructorListSerializer, ForgotPasswordSerializer, ResetPasswordSerializer

User = get_user_model()

@extend_schema(tags=['users'])
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

@extend_schema(tags=['users'])
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        # FAQAT BIRTA Response obyektini qaytaramiz
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )

@extend_schema(tags=['users'])
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(request=LogoutSerializer, responses={205: {"description": "Logged out"}},tags=['users'])
class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({"detail": "Logged out"}, status=status.HTTP_205_RESET_CONTENT)


@extend_schema(tags=['users'])
class InstructorListAPIView(generics.ListAPIView):  # hamma oqituvchilani royxati
    serializer_class = InstructorListSerializer
    permissions_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(course__isnull=False).distinct()

@extend_schema(tags=['users'])
class InstructorDetailAPIView(generics.RetrieveAPIView):  # bitta oqituvchi+kurslari
    serializer_class = InstructorDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'

    def get_queryset(self):
        return User.objects.filter(course__isnull=False).distinct()

#login parol tiklash
@extend_schema(tags=['qoshimcha '])
class ForgotPasswordAPIView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [AllowAny]

    def post(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        reset= PasswordReset.objects.create(user=user)
        reset_link = f"http://localhost:3000/reset-password/?token={reset.token}"

        try:
            send_mail(
                subject="Parolni tiklash",
                message=f'parolingizni tiiklash uchin link: {reset_link}',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL','noreply@example.com'),
                recipient_list=[user.email],
                fail_silently=True,

            )
        except Exception:
            pass
        return Response(
            {'detail':'Emailga token ham qaytarildi','token':str(reset.token)},status=status.HTTP_200_OK,
        )

@extend_schema(tags=['qoshimcha '])
class ResetPasswordAPIView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail':'parol muvafaqiyatli ozgartirildi.'}, status=status.HTTP_200_OK)
