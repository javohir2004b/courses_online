from rest_framework import serializers

from apps.contact.models import ContactMessage


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id','name','email','subject','message','created_at']
        read_only_fields = ['id','created_at']