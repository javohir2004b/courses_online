from django.urls import path
from .views import BlogCategoryAPIView , PostDetailAPIView ,BlogPostAPIView
urlpatterns = [
    path('categories/' , BlogCategoryAPIView.as_view()),
    path('<slug:slug>/', PostDetailAPIView.as_view()),
    path('',BlogPostAPIView.as_view()),


]