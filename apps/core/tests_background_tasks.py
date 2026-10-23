from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.core.models import Application, Job, NotificationLog, Resume
from apps.core.tasks.background import (
    generate_interview_questions_async,
    parse_resume_async,
    periodic_queue_health_check,
)


class ResumeParsingTaskTests(SimpleTestCase):
    @patch("apps.core.tasks.background.extract_skills")
    @patch("apps.core.tasks.background.extract_resume_text")
    @patch("apps.core.tasks.background.Resume.objects.get")
    def test_parse_resume_returns_summary_without_resume_text(
        self, get_resume, extract_text, extract_skills
    ):
        stored_file = MagicMock()
        stored_file.read.return_value = b"fake resume bytes"

        resume = SimpleNamespace(
            file=stored_file,
            original_filename="resume.pdf",
        )
        get_resume.return_value = resume
        extract_text.return_value = {
            "file_type": "PDF",
            "raw_text": "Private resume content",
            "cleaned_text": "Python Django SQL",
        }
        extract_skills.return_value = ["Python", "Django", "SQL"]

        result = parse_resume_async.run(123)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["resume_id"], 123)
        self.assertEqual(result["file_type"], "PDF")
        self.assertEqual(result["skills_count"], 3)
        self.assertNotIn("raw_text", result)
        self.assertNotIn("cleaned_text", result)
        extract_text.assert_called_once()


class AIInterviewTaskTests(SimpleTestCase):
    @patch(
        "apps.core.services.interview_questions.generate_interview_questions"
    )
    @patch("apps.core.tasks.background.Job.objects.get")
    def test_ai_task_returns_generated_questions(
        self, get_job, generate_questions
    ):
        get_job.return_value = SimpleNamespace(
            title="Python Developer",
            description="Build Django REST APIs",
            required_skills="Python, Django, REST API",
        )
        generate_questions.return_value = [
            {"question": "What is a Django model?"},
            {"question": "Explain REST API authentication."},
        ]

        result = generate_interview_questions_async.run(
            7,
            question_count=2,
            difficulty="mixed",
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["job_id"], 7)
        self.assertEqual(result["question_count"], 2)
        self.assertEqual(len(result["questions"]), 2)
        generate_questions.assert_called_once_with(
            job_title="Python Developer",
            job_description="Build Django REST APIs",
            required_skills="Python, Django, REST API",
            question_count=2,
            difficulty="mixed",
        )


class PeriodicHealthCheckTaskTests(SimpleTestCase):
    @patch("apps.core.tasks.background.NotificationLog.objects.count")
    @patch("apps.core.tasks.background.Application.objects.count")
    @patch("apps.core.tasks.background.Job.objects.count")
    def test_health_check_returns_aggregate_counts(
        self, job_count, application_count, notification_count
    ):
        job_count.return_value = 4
        application_count.return_value = 4
        notification_count.return_value = 3

        result = periodic_queue_health_check.run()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["jobs_count"], 4)
        self.assertEqual(result["applications_count"], 4)
        self.assertEqual(result["notification_logs_count"], 3)
        self.assertIn("checked_at", result)
