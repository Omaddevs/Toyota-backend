from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserNotification
from .serializers import UserNotificationSerializer


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Joriy foydalanuvchi bildirishnomalari — o‘qish va o‘chirish."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserNotificationSerializer
    pagination_class = None

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        read = request.query_params.get("read")
        if read == "true":
            qs = qs.exclude(read_at__isnull=True)
        elif read == "false":
            qs = qs.filter(read_at__isnull=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.read_at is None:
            return Response(
                {"detail": "Faqat o‘qilgan bildirishnomalarni o‘chirish mumkin."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        n = self.get_queryset().filter(read_at__isnull=True).count()
        return Response({"count": n})

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        obj = self.get_object()
        if obj.read_at is None:
            obj.read_at = timezone.now()
            obj.save(update_fields=["read_at"])
        return Response(UserNotificationSerializer(obj).data)
