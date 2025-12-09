from django.contrib.auth import get_user_model
from django.db import models
from rest_framework import serializers

from apps.courses.models import Course, Category ,Lesson ,Enrollment,CoursReview

User = get_user_model()

class InstructorSerializer(serializers.ModelSerializer):   #oqituchi malumotlari
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "avatar", "bio")
        read_only_fields = fields


class CategorySerializer(serializers.ModelSerializer):   #kurs kategoriyasi
    class Meta:
        model = Category
        fields = ("id","name","slug")

class LessonSerializer(serializers.ModelSerializer):    #Darslar
    class Meta:
        model = Lesson
        fields = ["id","title","order","duration","video_url","content"]


class CourseListSerializer(serializers.ModelSerializer):     #Kurslar royxati
    instructor_name = serializers.CharField(source="instructor.username")
    class Meta:
        model =Course
        fields = ("id","title","slug","short_description","price","level","thumbnail","lessons_count","students_count","instructor_name",)




# baholash va sharh

# class CourseReviewSerializer(serializers.ModelSerializer):
#     # user = serializers.CharField(source='user.username',read_only=True)
#     user = serializers.StringRelatedField(read_only=True)
#
#     class Meta:
#         model = CoursReview
#         fields = ['id','user','rating','comment','created_at']
#         read_only_fields = ['id','user','created_at']
#
#     def validate_rating(self,value):
#         if value < 1 or value >5:
#             raise serializers.ValidationError("rating 1 dan 5 gacha bolish kere")
#         return value
#
#
#     # def create(self, validated_data):
#     #     request = self.context.get("request")
#     #     course = validated_data.get("course")
#     #     validated_data['user'] = request.user
#     #     validated_data['course']=course
#     #     review = super().create(validated_data)
#
#         course.reviews_count = course.reviews_count()
#         course.avg_rating = course.reviews.aggregate(models.Avg("rating"))['rating__avg']or 0
#         course.save(update_fields=['reviews_count','avg_rating'])
#         return review

#hozir yozgan kod
class CourseReviewSerializer(serializers.ModelSerializer):
    # user = serializers.CharField(source='user.username', read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CoursReview
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("rating 1 dan 5 gacha bo'lish kerak")
        return value

class CourseDetailSerializer(serializers.ModelSerializer):    #bitta kurs sahifasi
    instructor_name = serializers.CharField(source="instructor.username")
    category = CategorySerializer()
    lessons = LessonSerializer(many=True,read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    reviews = CourseReviewSerializer(many=True, read_only=True)
    class Meta:
        model = Course
        fields = "__all__"

    def get_is_enrolled(self , obj):  #joriy foydalalnuvchi shu kursga yozilganmi yoqmi
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return obj.enrollments.filter(user=request.user, is_active=True).exists()

class MyCourseSerializer(serializers.ModelSerializer):    #userni oz kurslari
    course = CourseListSerializer(read_only=True)
    class  Meta:
        model = Enrollment
        fields = ["id","course","created_at"]






