
from decimal import Decimal

from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

from apps.core.models import (
    Application,
    ApplicationStatusHistory,
    ATSScore,
    ShortlistingRule,
    User,
)
from apps.core.services.ats_scoring import calculate_ats_score
from apps.core.services.eligibility import check_application_eligibility


TERMINAL_STATUSES = {"rejected", "selected"}


def _can_manage_job(user, job):
    if not user or not user.is_authenticated:
        return False

    if user.role == User.Role.ADMIN:
        return True

    return (
        user.role == User.Role.EMPLOYER
        and job.employer.user_id == user.id
    )


def _get_rule(job):
    rule, _ = ShortlistingRule.objects.get_or_create(job=job)
    return rule


def _save_ats_score(application):
    result = calculate_ats_score(application)

    ATSScore.objects.update_or_create(
        application=application,
        defaults={
            "score": result["score"],
            "skills_score": result["skills_score"],
            "experience_score": result["experience_score"],
            "education_score": result["education_score"],
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"],
        },
    )

    return result


def _notify_candidate(application, new_status):
    """
    Best-effort email notification. Configure Django email
    settings before enabling production email delivery.
    """
    candidate_user = application.candidate.user
    email = getattr(candidate_user, "email", None)

    if not email:
        return

    try:
        send_mail(
            subject=f"Application update: {application.job.title}",
            message=(
                f"Your application for {application.job.title} "
                f"has been updated to: {new_status}."
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        # A mail server problem must not undo an application status.
        pass


def _record_status_change(application, new_status, actor=None, action=""):
    old_status = application.status

    if old_status == new_status:
        return False

    # Use the project's established legal transitions.
    allowed_transitions = {
        "applied": {"shortlisted", "rejected"},
        "shortlisted": {"interview_scheduled", "rejected"},
        "interview_scheduled": {"selected", "rejected"},
        "rejected": set(),
        "selected": set(),
    }

    if new_status not in allowed_transitions.get(old_status, set()):
        raise ValueError(
            f"Status transition from {old_status} to {new_status} "
            "is not allowed."
        )

    application.status = new_status
    application.save(update_fields=["status"])

    ApplicationStatusHistory.objects.create(
        application=application,
        old_status=old_status,
        new_status=new_status,
        changed_by=actor,
        action=action,
    )

    return True


@transaction.atomic
def process_application(application, actor=None):
    """
    Score one application and make an automated decision.

    Existing rejected/selected applications are never overwritten.
    Only applications in 'applied' status are considered for an
    automatic shortlist or rejection.
    """
    application = (
        Application.objects.select_for_update()
        .select_related(
            "job",
            "job__employer",
            "job__employer__user",
            "candidate",
            "candidate__user",
        )
        .get(pk=application.pk)
    )

    if application.status in TERMINAL_STATUSES:
        return {
            "application_id": application.id,
            "status": application.status,
            "decision": "skipped",
            "reason": "Application is already in a terminal status.",
        }

    if application.status != "applied":
        return {
            "application_id": application.id,
            "status": application.status,
            "decision": "skipped",
            "reason": "Only applied applications are processed automatically.",
        }

    eligibility = check_application_eligibility(application)

    if not eligibility["eligible"]:
        return {
            "application_id": application.id,
            "status": application.status,
            "decision": "review",
            "reason": eligibility["reason"],
        }

    result = _save_ats_score(application)
    score = Decimal(str(result["score"]))
    rule = _get_rule(application.job)

    if not rule.is_enabled:
        return {
            "application_id": application.id,
            "status": application.status,
            "decision": "review",
            "score": float(score),
            "reason": "Automatic shortlisting is disabled for this job.",
        }

    new_status = None
    decision = "review"

    if score >= rule.shortlist_threshold:
        new_status = "shortlisted"
        decision = "shortlisted"

    elif rule.auto_reject_enabled and score < rule.reject_threshold:
        new_status = "rejected"
        decision = "rejected"

    changed = False

    if new_status:
        changed = _record_status_change(
            application=application,
            new_status=new_status,
            actor=actor,
            action=f"auto_{decision}",
        )

        if changed and rule.auto_notify_enabled:
            transaction.on_commit(
                lambda app_id=application.id, status=new_status:
                _notify_candidate(
                    Application.objects.select_related(
                        "candidate__user", "job"
                    ).get(pk=app_id),
                    status,
                )
            )

    return {
        "application_id": application.id,
        "status": new_status or application.status,
        "decision": decision,
        "score": float(score),
        "skills_score": float(result["skills_score"]),
        "experience_score": float(result["experience_score"]),
        "education_score": float(result["education_score"]),
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "reason": (
            "Decision applied."
            if changed
            else "Candidate remains under review."
        ),
    }


def process_job_applications(job, actor=None):
    """
    Process all currently applied applications for one job.
    """
    applications = (
        Application.objects.filter(job=job, status="applied")
        .order_by("applied_at", "id")
    )

    results = []
    for application in applications.iterator():
        try:
            results.append(process_application(application, actor=actor))
        except Exception as exc:
            results.append({
                "application_id": application.id,
                "decision": "error",
                "reason": str(exc),
            })

    return {
        "job_id": job.id,
        "processed": len(results),
        "shortlisted": sum(
            item.get("decision") == "shortlisted" for item in results
        ),
        "rejected": sum(
            item.get("decision") == "rejected" for item in results
        ),
        "review": sum(
            item.get("decision") == "review" for item in results
        ),
        "errors": sum(
            item.get("decision") == "error" for item in results
        ),
        "results": results,
    }
