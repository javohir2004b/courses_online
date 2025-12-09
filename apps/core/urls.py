from django.urls import path

from apps.core.views import HomePageAPIView

urlpatterns = [
    path('home-page/', HomePageAPIView.as_view(), name='home-page'),
]