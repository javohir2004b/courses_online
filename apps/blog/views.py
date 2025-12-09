from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from apps.blog.models import BlogCategory, Post
from apps.blog.serializers import BlogCategorySerializer, PostListSerializer, PostDetailSerializer

@extend_schema(tags=['blog'])
class BlogCategoryAPIView(generics.ListAPIView):
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    permission_classes = [permissions.AllowAny]

@extend_schema(tags=['blog'])
class BlogPostAPIView(generics.ListAPIView):
    queryset = Post.objects.select_related('category','author')
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        category_slug = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        is_featured = [permissions.AllowAny]
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if search:
            qs = qs.filter(title__icontains=search)
        if is_featured == 'true':
            qs = qs.filter(is_featured=True)
        return qs

@extend_schema(tags=['blog'])
class PostDetailAPIView(generics.RetrieveAPIView):
    queryset = Post.objects.select_related('category','author')
    serializer_class = PostDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'