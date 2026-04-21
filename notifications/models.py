from django.conf import settings
from django.db import models


class UserNotification(models.Model):
    """Foydalanuvchiga kelgan bildirishnoma (admin yuboradi)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="foydalanuvchi",
    )
    title = models.CharField("sarlavha", max_length=255)
    body = models.TextField("matn")
    read_at = models.DateTimeField("o‘qilgan vaqti", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
        verbose_name="yuborgan admin",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"

    def __str__(self):
        return f"{self.title} → {self.user}"
