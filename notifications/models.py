from django.db import models
from django.conf import settings


class Notification(models.Model):

    # Notification Types
    TYPE_WELCOME = "welcome"
    TYPE_PASSWORD_RESET = "password_reset"
    TYPE_ALERT = "alert"

    NOTIFICATION_TYPES = [
        (TYPE_WELCOME, "Welcome Email"),
        (TYPE_PASSWORD_RESET, "Password Reset"),
        (TYPE_ALERT, "Alert"),
    ]

    # Statuses
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    subject = models.CharField(
        max_length=255
    )

    message = models.TextField()

    error_message = models.TextField(
        blank=True
    )

    retry_count = models.PositiveIntegerField(
        default=0
    )

    last_retry_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.notification_type} - "
            f"{self.user.email} "
            f"[{self.status}]"
        )