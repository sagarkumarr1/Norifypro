from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .models import Notification

User = get_user_model()


class NotificationModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass123!'
        )

    def test_notification_created_pending(self):
        notification = Notification.objects.create(
            user=self.user,
            notification_type=Notification.TYPE_WELCOME,
            subject='Welcome!',
            message='Hello!'
        )
        self.assertEqual(notification.status, Notification.STATUS_PENDING)
        self.assertEqual(notification.retry_count, 0)

    def test_notification_str(self):
        notification = Notification.objects.create(
            user=self.user,
            notification_type=Notification.TYPE_WELCOME,
            subject='Welcome!',
            message='Hello!'
        )
        self.assertIn('welcome', str(notification))
        self.assertIn('test@example.com', str(notification))

    def test_notification_status_update(self):
        from django.utils import timezone
        notification = Notification.objects.create(
            user=self.user,
            notification_type=Notification.TYPE_WELCOME,
            subject='Welcome!',
            message='Hello!'
        )
        notification.status = Notification.STATUS_SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=['status', 'sent_at'])

        refreshed = Notification.objects.get(id=notification.id)
        self.assertEqual(refreshed.status, Notification.STATUS_SENT)
        self.assertIsNotNone(refreshed.sent_at)