from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Swagger / OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),


    path('api/v1/auth/' , include('apps.users.urls')),
    path("api/v1/courses/", include("apps.courses.urls")),
    path('api/v1/blog/', include('apps.blog.urls')),
    path('api/v1/contact/',include('apps.contact.urls')),
    path('api/v1/home/' , include('apps.core.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
path("api/v1/payments/", include("apps.payments.urls")),

]
