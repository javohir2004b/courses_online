from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from .models import User, PasswordReset
from ..courses.serializers import CourseListSerializer

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

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if not user:
            raise serializers.ValidationError("Login yoki parol noto'gri")
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

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True,min_length=6)

    def validate(self,attrs):
        token = attrs.get('token')
        try:
            reset_obj = PasswordReset.objects.get(token=token, is_used=False)
        except PasswordReset.DoesNotExist:
            raise serializers.ValidationError({"token":"Token notogri yoki ishlatilgan"})
        if reset_obj.is_expired():
            raise serializers.ValidationError({"token":"tokenni muddati tugagaan"})
        attrs['reset_obj']=reset_obj
        return attrs

    def save(self, **kwargs):
        reset_obj = self.validated_data['reset_obj']
        new_password = self.validated_data['new_password']
        user = reset_obj.user
        user.set_password(new_password)
        user.save()
        reset_obj.is_used = True
        reset_obj.save()
        return User