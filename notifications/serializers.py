from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification

class SenderMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('username',)

class NotificationSerializer(serializers.ModelSerializer):
    sender = SenderMiniSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ('id', 'recipient', 'sender', 'message', 'type', 'post', 'is_read', 'created_at')
        read_only_fields = ('recipient', 'sender', 'created_at')
