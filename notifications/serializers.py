from rest_framework import serializers

from .models import UserNotification


class UserNotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = UserNotification
        fields = ("id", "title", "body", "is_read", "read_at", "created_at")
        read_only_fields = ("read_at", "created_at")

    def get_is_read(self, obj):
        return obj.read_at is not None
