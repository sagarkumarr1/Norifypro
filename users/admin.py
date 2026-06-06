from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "email",
        "username",
        "is_email_verified",
        "is_staff",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_email_verified",
        "is_staff",
        "is_active",
        "created_at",
    )

    search_fields = (
        "email",
        "username",
        "first_name",
        "last_name",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        (
            "Account Information",
            {
                "fields": (
                    "email",
                    "username",
                    "password",
                )
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Verification",
            {
                "fields": (
                    "is_email_verified",
                )
            },
        ),
        (
            "Important Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "created_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                    "is_email_verified",
                ),
            },
        ),
    )