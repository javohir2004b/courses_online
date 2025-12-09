from rest_framework import serializers
from apps.courses.serializers import CourseListSerializer
from apps.blog.serializers import PostListSerializer
from apps.courses.models import Category


class HomeStatisticSerializer(serializers.Serializer):
    total_courses = serializers.IntegerField()
    total_lessons = serializers.IntegerField()
    total_students = serializers.IntegerField()

class CategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name','slug']

class HomePageSerializer(serializers.Serializer):
    statistic = HomeStatisticSerializer()
    featured_courses = CourseListSerializer(many=True)
    categories = CategorySimpleSerializer(many=True)
    latest_posts = PostListSerializer(many=True)