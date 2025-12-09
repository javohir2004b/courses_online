from django.db import models
from django.conf import settings
from django.utils.text import Truncator

User = settings.AUTH_USER_MODEL

class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    def __str__(self):
        return self.name

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL , null=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    excerpt = models.CharField(max_length=255,blank=True,null=True)
    content = models.TextField()
    thumbnail = models.ImageField(upload_to="blog/",blank=True,null=True)
    is_featured = models.BooleanField(default=False)  #home page korsatish uchun
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.excerpt and self.content:
            self.excerpt = Truncator(self.content).chars(150)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


