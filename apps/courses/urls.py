from django.urls import path
from .views import CategoryListAPIView, CourseListAPIView, CourseDetailAPIView, EnrollCourseAPIView, MyCoursesAPIView,DashboardStatisticAPIView,CourseReviewListCreateAPIview
urlpatterns = [
    # /api/v1/courses/
    path("", CourseListAPIView.as_view(), name="course-list"),
    # /api/v1/courses/categories/
    path("categories/", CategoryListAPIView.as_view(), name="category-list"),
    # /api/v1/courses/my/
    path("enrol/my/", MyCoursesAPIView.as_view(), name="my-courses"),
    # /api / v1 / courses / dashboard /
    path('dashboard/statistic/', DashboardStatisticAPIView.as_view(),name='dashboard-statistika'),
    path("<slug:slug>/enrol/", EnrollCourseAPIView.as_view(), name="enroll-course"),
    path("<slug:slug>/", CourseDetailAPIView.as_view(), name="course-detail"),
    path("<slug:slug>/reviews/", CourseReviewListCreateAPIview.as_view(), name="course-reviews"),

]
