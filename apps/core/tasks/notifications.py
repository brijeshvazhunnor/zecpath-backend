from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.core.models import NotificationLog, Application


@shared_task(bind=True, max_retries=3)
def send_application_notification(self, notification_id):
    try:
        notification = NotificationLog.objects.get(
            pk=notification_id
        )
    except NotificationLog.DoesNotExist:
        return {"status": "missing", "notification_id": notification_id}

    if notification.status == NotificationLog.DeliveryStatus.SENT:
        return {"status": "already_sent", "notification_id": notification_id}

    notification.attempts += 1
    notification.save(update_fields=["attempts"])

    try:
        application = notification.application

        if application is None:
            raise ValueError("The related application no longer exists.")

        candidate_name = application.candidate.full_name
        job_title = application.job.title

        messages = {
            NotificationLog.EventType.APPLICATION_SUBMITTED: (
                f"Hello {candidate_name},\n\n"
                f"Your application for '{job_title}' was submitted "
                "successfully. We will notify you about updates.\n\n"
                "Regards,\nZecpath Team"
            ),
            NotificationLog.EventType.SHORTLISTED: (
                f"Hello {candidate_name},\n\n"
                f"Good news! You have been shortlisted for "
                f"'{job_title}'. Please watch for further updates.\n\n"
                "Regards,\nZecpath Team"
            ),
            NotificationLog.EventType.REJECTED: (
                f"Hello {candidate_name},\n\n"
                f"Your application for '{job_title}' was not selected "
                "for the next stage. Thank you for your interest.\n\n"
                "Regards,\nZecpath Team"
            ),
        }

        message = messages.get(notification.event_type)

        if message is None:
            raise ValueError(
                f"Unsupported notification event: {notification.event_type}"
            )

        send_mail(
            subject=notification.subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient],
            fail_silently=False,
        )

        notification.status = NotificationLog.DeliveryStatus.SENT
        notification.sent_at = timezone.now()
        notification.last_error = ""
        notification.save(
            update_fields=["status", "sent_at", "last_error"]
        )

        return {
            "status": "sent",
            "notification_id": notification_id,
        }

    except Exception as exc:
        notification.last_error = str(exc)

        if self.request.retries < self.max_retries:
            notification.status = NotificationLog.DeliveryStatus.PENDING
            notification.save(
                update_fields=["status", "last_error"]
            )
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)

        notification.status = NotificationLog.DeliveryStatus.FAILED
        notification.save(
            update_fields=["status", "last_error"]
        )

        return {
            "status": "failed",
            "notification_id": notification_id,
            "error": str(exc),
        }
