from django.db import transaction

from apps.core.models import Application, NotificationLog


def queue_application_notification(application_id, event_type):
    application = (
        Application.objects
        .select_related("candidate__user", "job")
        .get(pk=application_id)
    )

    recipient = application.candidate.user.email

    if not recipient:
        return None

    subjects = {
        NotificationLog.EventType.APPLICATION_SUBMITTED:
            f"Application received: {application.job.title}",
        NotificationLog.EventType.SHORTLISTED:
            f"Application shortlisted: {application.job.title}",
        NotificationLog.EventType.REJECTED:
            f"Application update: {application.job.title}",
    }

    subject = subjects.get(event_type)

    if subject is None:
        raise ValueError(
            f"Unsupported notification event: {event_type}"
        )

    notification = NotificationLog.objects.create(
        application=application,
        event_type=event_type,
        recipient=recipient,
        subject=subject,
    )

    def enqueue():
        from apps.core.tasks.notifications import (
            send_application_notification,
        )

        send_application_notification.delay(notification.pk)

    transaction.on_commit(enqueue, robust=True)

    return notification
