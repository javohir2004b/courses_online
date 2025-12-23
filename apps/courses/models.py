from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    LEVELS = (
    ("beginner","Beginner"),
    ("intermediate","Intermediate"),
    ("advanced" , "Advanced"),
    )

    instructor = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    short_description = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    level = models.CharField(max_length=20 , choices=LEVELS , default="beginner")
    price = models.DecimalField(max_digits=8, decimal_places=2 , default=0)
    thumbnail = models.ImageField(upload_to="courses/",blank=True,null=True)
    avg_rating = models.FloatField(default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    lessons_count = models.PositiveIntegerField(default=0)
    students_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(Course , on_delete=models.CASCADE,related_name="lessons")
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    duration = models.CharField(max_length=50 , blank=True, null=True)
    video_url = models.URLField(blank=True,null=True)
    content = models.TextField(blank=True,null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together = ("user","course")

    def __str__(self):
        return f"{self.user}->{self.course}"

# Review rating qism

class CourseReview(models.Model):
    course = models.ForeignKey(Course , on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE , related_name='course_reviews')
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
        unique_together = ('user','course')

    def __str__(self):
        return f"{self.course.title}-{self.user.username} ({self.rating}"

