from django.contrib import admin
from .models import Course, Category, Lesson, CourseReview ,Enrollment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'avg_rating', 'reviews_count')
    search_fields = ('title',)
    list_filter = ('category',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course')
    search_fields = ('title',)


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'course',
        'user',
        'rating',
        'short_comment',
        'created_at',
    )
    list_filter = ('rating', 'created_at', 'course')
    search_fields = ('user__email', 'user__username', 'comment')
    ordering = ('-created_at',)

    def short_comment(self, obj):
        return obj.comment[:40]

    short_comment.short_description = "Sharh"

@admin.action(description="✅ Tanlanganlarni tasdiqlash")
def approve_enrollments(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "is_active", "created_at")
    list_filter = ("is_active", "course")
    search_fields = ("user__username", "course__title")
    ordering = ("-created_at",)