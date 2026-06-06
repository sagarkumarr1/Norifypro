# tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_welcome_email(self, user_id):
    """
    Welcome email queue — Run in background.
    Fail hone pe 3 baar retry karta hai, 60 sec baad.
    """
    from django.contrib.auth import get_user_model
    from .models import Notification

    User = get_user_model()
    notification = None  # FIX: Variable को पहले ही None इनिशियलाइज़ किया ताकि except ब्लॉक क्रैश न हो

    try:
        user = User.objects.get(id=user_id)

        # DB mein record banao — pending status
        notification = Notification.objects.create(
            user=user,
            notification_type=Notification.TYPE_WELCOME,
            subject=f"Welcome to NotifyPro, {user.username}!",
            message=f"Hi {user.username},\n\nAapka account successfully create ho gaya hai.\n\nThank you!",
            status=Notification.STATUS_PENDING
        )

        # Email bhejo
        send_mail(
            subject=notification.subject,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        # Success — status update karo
        notification.status = Notification.STATUS_SENT
        notification.sent_at = timezone.now()
        notification.save()

        logger.info(f"Welcome email sent to {user.email}")
        return f"Email sent to {user.email}"

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return "User not found"

    except Exception as exc:
        # Fail hua — record update karo (अगर नोटिफिकेशन ऑब्जेक्ट बन चुका था), फिर retry
        if notification:
            try:
                notification.status = Notification.STATUS_FAILED
                notification.error_message = str(exc)
                notification.save()
            except Exception as db_err:
                logger.error(f"Failed to update notification status in DB: {db_err}")

        logger.error(f"Email failed for user {user_id}: {exc}")
        raise self.retry(exc=exc)  # Celery 3 बार रिट्राय करेगा


@shared_task
def send_daily_report():
    """
    Har raat 12 baje chalega automatically.
    Aaj kitne users register hue, kitne notifications gaye.
    """
    from django.contrib.auth import get_user_model
    from .models import Notification
    from django.utils import timezone

    User = get_user_model()
    today = timezone.now().date()

    # Aaj ke stats
    new_users = User.objects.filter(
        date_joined__date=today
    ).count()

    notifications_sent = Notification.objects.filter(
        created_at__date=today,
        status=Notification.STATUS_SENT
    ).count()

    notifications_failed = Notification.objects.filter(
        created_at__date=today,
        status=Notification.STATUS_FAILED
    ).count()

    report = {
        'date': str(today),
        'new_users': new_users,
        'notifications_sent': notifications_sent,
        'notifications_failed': notifications_failed,
    }

    logger.info(f"Daily Report: {report}")
    return report


@shared_task
def retry_failed_notifications():
    """
    Har 30 minute mein chalega.
    Jo notifications fail hui hain unhe dobara try karega.
    """
    from .models import Notification

    failed = Notification.objects.filter(
        status=Notification.STATUS_FAILED
    )[:10]  # Ek baar mein max 10

    retried = 0
    for notification in failed:
        if notification.user:
            # Dobara queue mein dalo
            send_welcome_email.delay(notification.user.id)
            retried += 1

    logger.info(f"Retried {retried} failed notifications")
    return f"Retried: {retried}"
