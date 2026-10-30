from decimal import Decimal

from apps.core.models import ATSScore, ShortlistingRule, Application


DEFAULT_ATS_THRESHOLD = Decimal("75.00")


def check_ai_call_eligibility(application):
    """
    Check whether an application is eligible for an AI interview call.

    Returns:
        {
            "eligible": bool,
            "reason": str,
            "ats_score": float or None,
            "threshold": float
        }
    """

    candidate = application.candidate
    job = application.job

    # 1. Application must be shortlisted.
    if application.status != "shortlisted":
        return {
            "eligible": False,
            "reason": "Application is not shortlisted.",
            "ats_score": None,
            "threshold": float(DEFAULT_ATS_THRESHOLD),
        }

    # 2. Job must be active.
    if job.status != "active":
        return {
            "eligible": False,
            "reason": "Job is not active.",
            "ats_score": None,
            "threshold": float(DEFAULT_ATS_THRESHOLD),
        }

    # 3. Candidate profile must be active.
    if not candidate.is_active:
        return {
            "eligible": False,
            "reason": "Candidate profile is inactive.",
            "ats_score": None,
            "threshold": float(DEFAULT_ATS_THRESHOLD),
        }

    # 4. Candidate must have given consent.
    if not candidate.ai_call_consent:
        return {
            "eligible": False,
            "reason": "Candidate has not consented to AI calls.",
            "ats_score": None,
            "threshold": float(DEFAULT_ATS_THRESHOLD),
        }

    # 5. Candidate must be available.
    if not candidate.available_for_ai_call:
        return {
            "eligible": False,
            "reason": "Candidate is not available for AI calls.",
            "ats_score": None,
            "threshold": float(DEFAULT_ATS_THRESHOLD),
        }

    # 6. Get the configured ATS threshold for this job.
    rule = ShortlistingRule.objects.filter(job=job).first()

    threshold = (
        rule.shortlist_threshold
        if rule
        else DEFAULT_ATS_THRESHOLD
    )

    # 7. An ATS score must exist.
    try:
        ats_score = application.ats_score
    except ATSScore.DoesNotExist:
        return {
            "eligible": False,
            "reason": "ATS score has not been calculated.",
            "ats_score": None,
            "threshold": float(threshold),
        }

    # 8. ATS score must meet the threshold.
    if ats_score.score < threshold:
        return {
            "eligible": False,
            "reason": "ATS score is below the required threshold.",
            "ats_score": float(ats_score.score),
            "threshold": float(threshold),
        }

    return {
        "eligible": True,
        "reason": "Application is eligible for an AI interview call.",
        "ats_score": float(ats_score.score),
        "threshold": float(threshold),
    }