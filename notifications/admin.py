from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'status', 'created_at', 'sent_at']
    list_filter = ['status', 'notification_type']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'sent_at']