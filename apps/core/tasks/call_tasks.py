from celery import shared_task
from django.utils import timezone

from apps.core.models import AICall


@shared_task(
    bind=True,
    max_retries=3,
    name="core.queue_ai_call",
)
def queue_ai_call(self, call_id):
    """
    Prepare an eligible AI call for the queue.

    This task does not place a real telephone call.
    """

    try:
        call = AICall.objects.get(pk=call_id)

        # Do not queue a call before its scheduled time.
        if (
            call.scheduled_at
            and call.scheduled_at > timezone.now()
        ):
            queue_ai_call.apply_async(
                args=[call.id],
                eta=call.scheduled_at,
            )

            return {
                "status": call.status,
                "call_id": call.id,
                "message": "Call is not due yet. Rescheduled.",
            }

        # Do not process terminal calls again.
        if call.status in (
            AICall.Status.COMPLETED,
            AICall.Status.FAILED,
        ):
            return {
                "status": call.status,
                "call_id": call.id,
                "message": "Call is already in a terminal state.",
            }

        # Avoid duplicate queue processing.
        if call.status == AICall.Status.QUEUED:
            return {
                "status": call.status,
                "call_id": call.id,
                "message": "Call is already queued.",
            }

        if call.status != AICall.Status.SCHEDULED:
            return {
                "status": call.status,
                "call_id": call.id,
                "message": "Call is not in a schedulable state.",
            }

        call.status = AICall.Status.QUEUED
        call.failure_reason = ""
        call.save(
            update_fields=[
                "status",
                "failure_reason",
                "updated_at",
            ]
        )

        return {
            "status": call.status,
            "call_id": call.id,
            "message": "AI call workflow added to the queue.",
        }

    except AICall.DoesNotExist:
        return {
            "status": "error",
            "call_id": call_id,
            "message": "AI call record not found.",
        }

    except Exception as exc:
        try:
            call = AICall.objects.get(pk=call_id)

            if self.request.retries >= call.max_retries:
                call.retry_count = call.max_retries
                call.status = AICall.Status.FAILED
                call.failure_reason = str(exc)

                call.save(
                    update_fields=[
                        "retry_count",
                        "status",
                        "failure_reason",
                        "updated_at",
                    ]
                )

                return {
                    "status": AICall.Status.FAILED,
                    "call_id": call_id,
                    "message": "Maximum retries exceeded.",
                }

            call.retry_count = self.request.retries + 1
            call.failure_reason = str(exc)

            call.save(
                update_fields=[
                    "retry_count",
                    "failure_reason",
                    "updated_at",
                ]
            )

        except AICall.DoesNotExist:
            pass

        raise self.retry(
            exc=exc,
            countdown=30 * (2 ** self.request.retries),
            max_retries=call.max_retries,
        )