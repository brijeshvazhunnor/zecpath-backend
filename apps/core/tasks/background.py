from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from celery import shared_task

from apps.core.models import Application, Job, NotificationLog, Resume
from apps.core.services.resume_parser import (
    ResumeParsingError,
    extract_resume_text,
)
from apps.core.services.resume_nlp import extract_skills


@shared_task(bind=True, max_retries=3, name="core.parse_resume_async")
def parse_resume_async(self, resume_id):
    """
    Parse a stored resume asynchronously.

    Only summary metadata is returned; resume text is not placed in
    the Celery result backend.
    """
    try:
        resume = Resume.objects.get(pk=resume_id, is_active=True)

        if not resume.file:
            return {
                "status": "error",
                "resume_id": resume_id,
                "message": "Resume file is missing.",
            }

        resume.file.open("rb")
        try:
            content = resume.file.read()
        finally:
            resume.file.close()

        filename = resume.original_filename or "resume.pdf"
        content_type = (
            "application/pdf"
            if filename.lower().endswith(".pdf")
            else "application/vnd.openxmlformats-officedocument."
                 "wordprocessingml.document"
        )

        uploaded_file = SimpleUploadedFile(
            name=filename,
            content=content,
            content_type=content_type,
        )
        parsed = extract_resume_text(uploaded_file)
        skills = extract_skills(parsed["cleaned_text"])

        return {
            "status": "completed",
            "resume_id": resume_id,
            "file_type": parsed["file_type"],
            "character_count": len(parsed["cleaned_text"]),
            "skills_found": skills,
            "skills_count": len(skills),
        }

    except Resume.DoesNotExist:
        return {
            "status": "error",
            "resume_id": resume_id,
            "message": "Active resume not found.",
        }
    except ResumeParsingError as exc:
        return {
            "status": "error",
            "resume_id": resume_id,
            "message": str(exc),
        }


@shared_task(
    bind=True,
    max_retries=2,
    name="core.generate_interview_questions_async",
)
def generate_interview_questions_async(
    self,
    job_id,
    question_count=8,
    difficulty="mixed",
):
    """Generate interview questions in a worker, not the web request."""
    from apps.core.services.interview_questions import (
        generate_interview_questions,
    )

    try:
        job = Job.objects.get(pk=job_id)

        questions = generate_interview_questions(
            job_title=job.title,
            job_description=job.description,
            required_skills=job.required_skills,
            question_count=question_count,
            difficulty=difficulty,
        )

        return {
            "status": "completed",
            "job_id": job_id,
            "question_count": len(questions),
            "questions": questions,
        }

    except Job.DoesNotExist:
        return {
            "status": "error",
            "job_id": job_id,
            "message": "Job not found.",
        }


@shared_task(name="core.periodic_queue_health_check")
def periodic_queue_health_check():
    """
    Lightweight periodic task to verify scheduled jobs execute.

    Returns aggregate counts only; no candidate information is returned.
    """
    return {
        "status": "ok",
        "checked_at": timezone.now().isoformat(),
        "jobs_count": Job.objects.count(),
        "applications_count": Application.objects.count(),
        "notification_logs_count": NotificationLog.objects.count(),
    }
