from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_welcome_email(self, notification_id):
    """
    Send welcome email asynchronously.

    Features:
    - Retry up to 3 times
    - Track retry count
    - Prevent duplicate emails
    - Store failure reason
    """

    from .models import Notification

    try:
        notification = Notification.objects.select_related(
            "user"
        ).get(id=notification_id)

        user = notification.user

        # Idempotency protection
        if (
            notification.status == Notification.STATUS_SENT
            and notification.sent_at is not None
        ):
            logger.info(
                f"Notification {notification.id} already sent."
            )
            return "Already sent"

        send_mail(
            subject=notification.subject,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        notification.status = Notification.STATUS_SENT
        notification.sent_at = timezone.now()
        notification.error_message = ""

        notification.save(
            update_fields=[
                "status",
                "sent_at",
                "error_message",
            ]
        )

        logger.info(
            f"Email sent successfully to {user.email}"
        )

        return f"Email sent to {user.email}"

    except Notification.DoesNotExist:

        logger.error(
            f"Notification {notification_id} not found"
        )

        return "Notification not found"

    except Exception as exc:

        try:
            notification = Notification.objects.get(
                id=notification_id
            )

            notification.retry_count = (
                self.request.retries + 1
            )

            notification.last_retry_at = (
                timezone.now()
            )

            notification.error_message = str(exc)

            # Final failure
            if self.request.retries >= self.max_retries:

                notification.status = (
                    Notification.STATUS_FAILED
                )

                notification.save(
                    update_fields=[
                        "status",
                        "retry_count",
                        "last_retry_at",
                        "error_message",
                    ]
                )

                logger.error(
                    f"Notification {notification.id} "
                    f"permanently failed: {exc}"
                )

                raise

            notification.save(
                update_fields=[
                    "retry_count",
                    "last_retry_at",
                    "error_message",
                ]
            )

        except Notification.DoesNotExist:
            pass

        logger.warning(
            f"Retry {self.request.retries + 1}/3 "
            f"for notification {notification_id}"
        )

        raise self.retry(exc=exc)


@shared_task
def send_daily_report():
    """
    Daily statistics report.
    Runs via Celery Beat.
    """

    from django.contrib.auth import get_user_model
    from .models import Notification

    User = get_user_model()

    today = timezone.now().date()

    report = {
        "date": str(today),
        "new_users": User.objects.filter(
            date_joined__date=today
        ).count(),

        "notifications_sent": Notification.objects.filter(
            created_at__date=today,
            status=Notification.STATUS_SENT
        ).count(),

        "notifications_failed": Notification.objects.filter(
            created_at__date=today,
            status=Notification.STATUS_FAILED
        ).count(),
    }

    logger.info(f"Daily Report: {report}")

    return report


@shared_task
def retry_failed_notifications():
    """
    Runs every 30 minutes.

    Retries permanently failed
    notifications.
    """

    from .models import Notification

    failed_notifications = Notification.objects.filter(
        status=Notification.STATUS_FAILED
    ).order_by("created_at")[:10]

    retried = 0

    for notification in failed_notifications:

        notification.status = (
            Notification.STATUS_PENDING
        )

        notification.error_message = ""

        notification.last_retry_at = (
            timezone.now()
        )

        notification.save(
            update_fields=[
                "status",
                "error_message",
                "last_retry_at",
            ]
        )

        send_welcome_email.delay(
            notification.id
        )

        retried += 1

    logger.info(
        f"Retried {retried} failed notifications"
    )

    return {
        "retried": retried
    }