
import re
from decimal import Decimal, ROUND_HALF_UP


WEIGHTS = {
    "skills": Decimal("0.50"),
    "experience": Decimal("0.30"),
    "education": Decimal("0.20"),
}


def _as_text(value):
    """Convert a value into text safely."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "\n".join(str(item) for item in value)
    return str(value)


def _split_skills(value):
    """Split comma-, newline-, semicolon- or pipe-separated skills."""
    if isinstance(value, (list, tuple, set)):
        items = value
    else:
        items = re.split(r"[,;\n|•]+", _as_text(value))

    result = []
    seen = set()

    for item in items:
        skill = re.sub(r"\s+", " ", str(item)).strip()
        key = skill.casefold()

        if skill and key not in seen:
            result.append(skill)
            seen.add(key)

    return result


def _normalize_skill(skill):
    """Normalize common spelling variations for comparison."""
    value = re.sub(r"\s+", " ", skill.casefold()).strip()

    aliases = {
        "ml": "machine learning",
        "ai": "artificial intelligence",
        "dl": "deep learning",
        "postgres": "postgresql",
        "js": "javascript",
        "drf": "django rest framework",
    }

    return aliases.get(value, value)


def _get_resume_data(application):
    """
    Read Day 24 parsed data from the application snapshot,
    falling back to the candidate's profile fields.
    """
    snapshot = application.resume_snapshot or {}
    parsed = snapshot.get("resume", snapshot)

    if not isinstance(parsed, dict):
        parsed = {}

    skills = parsed.get("skills") or application.candidate.skills
    education = (
        parsed.get("education")
        or application.candidate.education
    )
    experience = (
        parsed.get("experience")
        or application.candidate.experience
    )

    if isinstance(experience, dict):
        years = experience.get("years")
        experience_text = _as_text(experience.get("roles", []))
    else:
        years = None
        experience_text = _as_text(experience)

    if years is None:
        years = _extract_years(experience_text)

    if years is None and not isinstance(experience, dict):
        years = _extract_years(experience)

    return {
        "skills": _split_skills(skills),
        "education": _as_text(education),
        "experience_years": years,
        "experience_text": experience_text,
    }


def _extract_years(value):
    """Extract a stated experience duration, not employment dates."""
    if value is None:
        return None

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*\+?\s*years?"
        r"(?:\s+of)?\s+experience",
        str(value),
        re.IGNORECASE,
    )

    if not match:
        match = re.search(
            r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+experience",
            str(value),
            re.IGNORECASE,
        )

    if match:
        return float(match.group(1))

    return None


def _required_experience(job):
    """
    Extract the minimum stated years from Job.experience.
    For '2-4 years', use 2 as the minimum.
    """
    value = _as_text(job.experience).casefold()

    if any(word in value for word in ("fresher", "no experience", "entry-level")):
        return 0.0

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:-|to)\s*\d+(?:\.\d+)?\s*years?",
        value,
    )

    if not match:
        match = re.search(
            r"(\d+(?:\.\d+)?)\s*\+?\s*years?",
            value,
        )

    return float(match.group(1)) if match else None


def _education_level(value):
    """Return the highest recognizable education level."""
    text = _as_text(value).casefold()

    patterns = [
        (5, r"\b(ph\.?\s*d\.?|doctorate|doctoral)\b"),
        (4, r"\b(m\.?\s*sc\.?|m\.?\s*tech\.?|m\.?\s*e\.?|"
            r"mca|mba|master(?:'s)?|postgraduate)\b"),
        (3, r"\b(b\.?\s*sc\.?|b\.?\s*tech\.?|b\.?\s*e\.?|"
            r"bca|bachelor(?:'s)?|undergraduate)\b"),
        (2, r"\b(diploma|polytechnic)\b"),
        (1, r"\b(high school|higher secondary|12th|secondary school)\b"),
    ]

    for level, pattern in patterns:
        if re.search(pattern, text):
            return level

    return None


def _score_skills(required_skills, candidate_skills):
    required = _split_skills(required_skills)
    candidate = _split_skills(candidate_skills)

    if not required:
        return Decimal("100.00"), [], []

    candidate_normalized = {
        _normalize_skill(skill) for skill in candidate
    }

    matched = [
        skill for skill in required
        if _normalize_skill(skill) in candidate_normalized
    ]
    missing = [
        skill for skill in required
        if _normalize_skill(skill) not in candidate_normalized
    ]

    score = Decimal(len(matched)) * Decimal("100") / Decimal(len(required))
    return score.quantize(Decimal("0.01")), matched, missing


def calculate_ats_score(application):
    """
    Calculate a transparent, weighted ATS score for an application.

    Returns component scores, total percentage and match details.
    """
    job = application.job
    resume = _get_resume_data(application)

    skills_score, matched, missing = _score_skills(
        job.required_skills,
        resume["skills"],
    )

    candidate_years = resume["experience_years"]
    required_years = _required_experience(job)

    if required_years is None or required_years == 0:
        experience_score = Decimal("100.00")
    elif candidate_years is None:
        experience_score = Decimal("0.00")
    else:
        experience_score = min(
            Decimal(str(candidate_years))
            * Decimal("100")
            / Decimal(str(required_years)),
            Decimal("100"),
        ).quantize(Decimal("0.01"))

    # The Job model has no dedicated education requirement field.
    # Look for a recognizable degree requirement in the job description.
    job_education_level = _education_level(job.description)
    candidate_education_level = _education_level(resume["education"])

    if job_education_level is None:
        education_score = Decimal("100.00")
    elif candidate_education_level is None:
        education_score = Decimal("0.00")
    elif candidate_education_level >= job_education_level:
        education_score = Decimal("100.00")
    else:
        education_score = (
            Decimal(candidate_education_level)
            * Decimal("100")
            / Decimal(job_education_level)
        ).quantize(Decimal("0.01"))

    total = (
        skills_score * WEIGHTS["skills"]
        + experience_score * WEIGHTS["experience"]
        + education_score * WEIGHTS["education"]
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "score": total,
        "skills_score": skills_score,
        "experience_score": experience_score,
        "education_score": education_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "candidate_experience_years": candidate_years,
        "required_experience_years": required_years,
        "candidate_education_level": candidate_education_level,
        "required_education_level": job_education_level,
    }
