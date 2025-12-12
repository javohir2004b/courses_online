import random
from django.conf import settings
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from .models import User, PasswordReset, PasswordResetCode
from ..courses.serializers import CourseListSerializer
from django.core.mail import send_mail

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('username', 'email', 'password' ,'password2', 'is_instructor')

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Parollar mos kelmadi")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        # 1) Avval email bo‘yicha userni topamiz
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Email yoki parol noto'g'ri")

        # 2) Django authenticate faqat username bilan ishlaydi, shuning uchun:
        user = authenticate(username=user_obj.username, password=password)

        if not user:
            raise serializers.ValidationError("Email yoki parol noto'g'ri")

        data["user"] = user
        return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_instructor')

class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username','email','is_instructor','bio','avatar')
        read_only_fields = ('id','email')

class InstructorListSerializer(serializers.ModelSerializer):
    courses_count = serializers.IntegerField(source='course_set.count', read_only=True)
    class Meta:
        model =User
        fields = ('id','username','email','courses_count','bio','avatar')

class InstructorDetailSerializer(serializers.ModelSerializer):
    courses = CourseListSerializer(source='course_set',many=True,read_only=True)
    class Meta:
        model = User
        fields = ('id','username','first_name','last_name','avatar','email','courses')
        read_only_fields = ('id','email')


# login parol qayta yuklash qismi

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("bu email bn foydalanuchi topilmadi")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self,value):
        try:
            user = User.objects.get(email=value)
        except PasswordReset.DoesNotExist:
            raise serializers.ValidationError({"User with this email not found"})
        self.user= user
        return value

    def create(self, validated_data):
        user = self.user
        code = str(random.randint(10000,999999))
        PasswordReset.objects.create(user=user, code=code)
        subject = "Password reset code"
        message = f"Your password reset code is: {code}\nThis code is valid for 15 minutes."
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            # email ishlamasa ham API yiqilmasin
            pass

        return {"email": user.email}


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True , min_length=3)
    confirm_password = serializers.CharField(write_only=True , min_length=3)
    def validate(self, attrs):
        email = attrs['email']
        code = attrs['code']
        new_password = attrs['new_password']
        confirm_password = attrs['confirm_password']

        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm-password": 'Paswords do not match'})
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email":"User with this email not found"})

        reset_qs = PasswordReset.objects.filter(user=user, code=code , is_used=False).order_by("-created_at")
        reset_obj = reset_qs.first()
        if not reset_obj:
            raise serializers.ValidationError({"code": "Invalid or already used code."})

        if reset_obj.is_expired():
            raise serializers.ValidationError({"code": "Code expired."})

        attrs["user"] = user
        attrs["reset_obj"] = reset_obj
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        reset_obj = self.validated_data["reset_obj"]
        new_password = self.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        reset_obj.is_used = True
        reset_obj.save()

        return user


class ForgotPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email topilmadi")
        return value

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)

        code = str(random.randint(100000, 999999))  # 6 xonali kod
        PasswordResetCode.objects.create(user=user, code=code)

        send_mail(
            subject="Password reset code",
            message=f"Sizning tasdiqlash kodingiz: {code}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False
        )


class ResetPasswordWithCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Parollar mos kelmadi!")

        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Email noto'g'ri")

        try:
            reset_code = PasswordResetCode.objects.filter(
                user=user, code=attrs['code']
            ).latest('created_at')
        except PasswordResetCode.DoesNotExist:
            raise serializers.ValidationError("Kod noto'g'ri!")

        if not reset_code.is_valid():
            raise serializers.ValidationError("Kod eskirgan! Yangi kod oling!")

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['password'])
        user.save()
