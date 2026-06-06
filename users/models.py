from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model using email as the login field.
    """

    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    is_email_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "username"
    ]

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["created_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower().strip()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.email