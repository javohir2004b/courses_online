from django.db.models.aggregates import Avg
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.courses.models import Course,Category,Enrollment,Lesson,CourseReview
from .serializers import CourseListSerializer, CategorySerializer, MyCourseSerializer, CourseDetailSerializer, \
    CourseReviewSerializer


@extend_schema(tags=['courses'])
class CategoryListAPIView(generics.ListAPIView):   #kategoriyalar royxati
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

@extend_schema(
    tags=['courses'],
    parameters=[
        OpenApiParameter(name='category', type=str, description='Kategoriya slug (vergul bilan)', required=False),
        OpenApiParameter(name='search', type=str, description='Kurs nomi bo‘yicha qidirish', required=False),
        OpenApiParameter(name='level', type=str, description='beginner/intermediate/advanced', required=False),
        # OpenApiParameter(name='price', type=str, description='free/paid', required=False),
        OpenApiParameter(name='rating', type=int, description='Minimum rating (1–5)', required=False),
    ]
)
@extend_schema(tags=['courses'])
class CourseListAPIView(generics.ListAPIView):   #kurslar royxati(filter + search)
    queryset = Course.objects.all().select_related("category", "instructor")
    serializer_class = CourseListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        category_slug = self.request.query_params.get("category")
        search = self.request.query_params.get('search')
        level = self.request.query_params.get('level')
        instructor_id = self.request.query_params.get('instuctor')
        price = self.request.query_params.get('price')
        min_rating = self.request.query_params.get('rating')

        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if search:
            qs = qs.filter(title__icontains=search)
        if level in ['beginner' , 'intermediate' , 'advanced']:
            qs = qs.filter(level = level)
        if instructor_id:
            qs = qs.filter(instructor_id=instructor_id)
        if price=='free':
            qs =qs.filter(price=0)
        elif price=='paid':
            qs = qs.filter(price__gt=0)
        if min_rating:
            try:
                min_rating = int(min_rating)
                qs = qs.filter(avg_rating__gte=min_rating)
            except ValueError:
                pass
        return qs


@extend_schema(tags=['courses'])
class CourseDetailAPIView(generics.RetrieveAPIView): #bitta kurs (details+lessons+is_enrolled
    queryset = Course.objects.all().select_related("category", "instructor").prefetch_related('lessons')
    serializer_class = CourseDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx



@extend_schema(tags=['courses'])
class EnrollCourseAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        try:
            course = Course.objects.get(slug=slug)
        except Course.DoesNotExist:
            return Response(
                {"detail": "Course not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={"is_active": False}
        )

        if not created:
            return Response(
                {"detail": "Siz allaqachon so‘rov yuborgansiz"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"detail": "So‘rovingiz yuborildi. Admin tasdiqlashini kuting."},
            status=status.HTTP_200_OK
        )





@extend_schema(tags=['courses'])
class MyCoursesAPIView(generics.ListAPIView):  #Mening kurslarim get
    serializer_class = MyCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(
            user=self.request.user,
            is_active=True
        ).select_related("course", "course__category", "course__instructor")

# DASHBOARD QISMI  umumiy statistika
@extend_schema(tags=['courses'])
class DashboardStatisticAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request):
        user = request.user

        total_courses = Course.objects.count()
        total_lessons = Lesson.objects.count()
        total_students = (Enrollment.objects.filter(is_active=True).values('user').distinct().count())

        my_enrollments= Enrollment.objects.filter(user=user,is_active=True)
        my_courses_count = my_enrollments.count()
        my_lessons_count = Lesson.objects.filter(course__enrollments__in=my_enrollments).distinct().count()

        data = {
            'total_courses': total_courses,
            'total_lessons': total_lessons,
            'total_students': total_students,
            'my_courses_count': my_courses_count,
            'my_lessons_count': my_lessons_count
        }
        return Response(data , status=status.HTTP_200_OK)





@extend_schema(tags=['baholash va sharh'])
class CourseReviewListCreateAPIview(generics.ListCreateAPIView):
    serializer_class = CourseReviewSerializer

    # 👇 GET va POST uchun alohida ruxsat
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]          # 👀 hamma ko‘radi
        return [IsAuthenticated()]       # ✍️ faqat login yozadi

    def get_queryset(self):
        course_slug = self.kwargs['slug']
        return (
            CourseReview.objects
            .filter(course__slug=course_slug)
            .select_related('user')
        )

    def perform_create(self, serializer):
        course = Course.objects.get(slug=self.kwargs['slug'])
        user = self.request.user

        # ❗ Kursga yozilganligini tekshiramiz
        if not Enrollment.objects.filter(
            user=user,
            course=course,
            is_active=True
        ).exists():
            raise PermissionDenied("Siz bu kursga yozilmagansiz")

        # ❗ Bir user bir marta sharh yozsin
        if CourseReview.objects.filter(user=user, course=course).exists():
            raise PermissionDenied("Siz bu kursga allaqachon sharh yozgansiz")

        # ✅ Review saqlanadi
        review = serializer.save(
            course=course,
            user=user,
        )

        # 📊 Statistikani yangilaymiz
        course.reviews_count = course.reviews.count()
        course.avg_rating = course.reviews.aggregate(
            avg=Avg('rating')
        )['avg'] or 0
        course.save(update_fields=['reviews_count', 'avg_rating'])

        return review
