from apps.core.services.call_schedule import get_next_ai_call_time
from apps.core.models import Application, AICall
from apps.core.services.call_eligibility import (
    check_ai_call_eligibility,
)
from django.db import transaction


def create_ai_call_if_eligible(application_id):
    """
    Create an AI call record when an application passes
    all AI call eligibility checks.

    This function does not place a real phone call.
    """

    application = (
        Application.objects.select_related(
            "job",
            "candidate",
            "candidate__user",
        )
        .filter(pk=application_id)
        .first()
    )

    if application is None:
        return {
            "created": False,
            "reason": "Application not found.",
        }

    eligibility = check_ai_call_eligibility(application)

    if not eligibility["eligible"]:
        return {
            "created": False,
            "reason": eligibility["reason"],
        }

    scheduled_at = get_next_ai_call_time()

    call, created = AICall.objects.get_or_create(
        application=application,
        defaults={
            "status": AICall.Status.SCHEDULED,
            "scheduled_at": scheduled_at,
        },
    )

    if created:
        def dispatch_ai_call():
            from apps.core.tasks import queue_ai_call

            queue_ai_call.apply_async(
                args=[call.id],
                eta=call.scheduled_at,
            )

        transaction.on_commit(
            dispatch_ai_call,
            robust=True,
        )

    return {
        "created": created,
        "call_id": call.id,
        "status": call.status,
        "reason": (
            "AI call scheduled."
            if created
            else "AI call record already exists."
        ),
    }