from django.core.cache import cache
from apps.courses.models import Course

def get_courses_list():
    cache_key = "courses:list"

    courses = cache.get(cache_key)
    if courses:
        return courses

    courses = list(
        Course.objects.only("id", "title").values("id", "title")
    )

    cache.set(cache_key, courses, timeout=300)  # 5 daqiqa
    return courses


def get_course_detail(course_id: int):
    cache_key = f"course:{course_id}"

    course = cache.get(cache_key)
    if course:
        return course

    try:
        course = Course.objects.only(
            "id", "title", "price", "description"
        ).get(id=course_id)
    except Course.DoesNotExist:
        return None

    cache.set(cache_key, course, timeout=300)
    return course
