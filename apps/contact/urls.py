from django.urls import path
from .views import ContactMessageAPIView

urlpatterns =[
    path('', ContactMessageAPIView.as_view(), name='contact-api')
]