
import re


def _text(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(str(item) for item in value)
    return str(value).strip()


def check_application_eligibility(application):
    """
    Determine whether an application has enough information
    for an automated ATS decision.

    Missing resume information is not treated as proof that
    the candidate is unqualified.
    """
    candidate = application.candidate
    snapshot = application.resume_snapshot or {}

    if not isinstance(snapshot, dict):
        snapshot = {}

    resume = snapshot.get("resume", snapshot)
    if not isinstance(resume, dict):
        resume = {}

    skills = (
        resume.get("skills")
        or getattr(candidate, "skills", "")
    )
    experience = (
        resume.get("experience")
        or getattr(candidate, "experience", "")
    )
    education = (
        resume.get("education")
        or getattr(candidate, "education", "")
    )

    has_skills = bool(_text(skills))
    has_experience = bool(_text(experience))
    has_education = bool(_text(education))

    # Require usable resume information before making an
    # automatic reject/shortlist decision.
    if not any((has_skills, has_experience, has_education)):
        return {
            "eligible": False,
            "reason": "Resume data is missing. Manual review required.",
        }

    job = application.job
    required_skills = _text(job.required_skills)

    # Do not require every keyword to match here. Skill matching
    # and percentage calculations are handled by the ATS service.
    if not required_skills and not _text(job.description):
        return {
            "eligible": False,
            "reason": "Job requirements are missing.",
        }

    return {
        "eligible": True,
        "reason": "Sufficient information is available for ATS evaluation.",
    }
