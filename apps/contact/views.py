from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions

from apps.contact.models import ContactMessage
from apps.contact.serializer import ContactMessageSerializer

@extend_schema(tags=['contact-message'])
class ContactMessageAPIView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]
