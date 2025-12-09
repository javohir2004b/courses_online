from drf_spectacular.utils import extend_schema
from rest_framework import permissions,status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.blog.models import Post
from apps.core.serializer import HomePageSerializer
from apps.courses.models import Course, Lesson, Enrollment, Category

@extend_schema(tags=['core'])
class HomePageAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self,request):
        total_courses = Course.objects.count()
        total_lessons = Lesson.objects.count()
        total_students = (Enrollment.objects.filter(is_active=True).values('user').distinct().count())
        statistic = {
            'total_courses':total_courses,
            'total_lessons':total_lessons,
            'total_students':total_students
        }
        featured_courses = Course.objects.filter().order_by('-students_count')[:6]
        categories = Category.objects.all()[:6]
        latest_posts = Post.objects.order_by('-created_at')[:3]

        data = {
            'statistic':statistic,
            'featured_courses':featured_courses,
            'categories':categories,
            'latest_posts':latest_posts,
        }

        serializer = HomePageSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)