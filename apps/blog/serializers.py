from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import BlogCategory , Post

User = get_user_model()

class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = ['id', 'name', 'slug']

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name']

class PostListSerializer(serializers.ModelSerializer):
    category = BlogCategorySerializer(read_only=True)
    author = AuthorSerializer(read_only=True)
    class Meta:
        model = Post
        fields = ['id','title','slug','excerpt','category','author','thumbnail','is_featured','created_at']

class PostDetailSerializer(serializers.ModelSerializer):
    category = BlogCategorySerializer(read_only=True)
    author = AuthorSerializer(read_only=True)
    class Meta:
        model = Post
        fields= ['id','title', 'slug', 'excerpt','category','content','thumbnail','author','created_at']