from decimal import Decimal

from django.test import TestCase

from apps.core.models import (
    User,
    Employer,
    Candidate,
    Job,
    Application,
    ATSScore,
    ShortlistingRule,
    AICall,
)
from apps.core.services.call_eligibility import (
    check_ai_call_eligibility,
)
from apps.core.services.call_trigger import (
    create_ai_call_if_eligible,
)
from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone

from apps.core.tasks.call_tasks import queue_ai_call

class AICallEligibilityTests(TestCase):

    def setUp(self):
        # Create employer user and profile.
        self.employer_user = User.objects.create_user(
            username="ai_employer",
            email="ai_employer@example.com",
            password="Test@12345",
            role="employer",
        )

        self.employer = Employer.objects.get(
            user=self.employer_user
        )

        self.employer.company_name = "Test Company"
        self.employer.save()

        # Create candidate user and profile.
        self.candidate_user = User.objects.create_user(
            username="ai_candidate",
            email="ai_candidate@example.com",
            password="Test@12345",
            role="candidate",
        )

        self.candidate = Candidate.objects.get(
            user=self.candidate_user
        )

        self.candidate.full_name = "Test Candidate"
        self.candidate.email = "ai_candidate@example.com"
        self.candidate.ai_call_consent = True
        self.candidate.available_for_ai_call = True
        self.candidate.save()

        # Create an active job.
        self.job = Job.objects.create(
            employer=self.employer,
            title="Python Developer",
            description="Develop Django applications.",
            required_skills="Python, Django",
            experience="1 year",
            location="Kochi",
            status="active",
        )

        # Create a shortlisted application.
        self.application = Application.objects.create(
            job=self.job,
            candidate=self.candidate,
            status="shortlisted",
        )

        # Create ATS score.
        self.ats_score = ATSScore.objects.create(
            application=self.application,
            score=Decimal("85.00"),
        )

        # Configure the ATS threshold.
        self.shortlisting_rule = ShortlistingRule.objects.create(
            job=self.job,
            shortlist_threshold=Decimal("75.00"),
            reject_threshold=Decimal("40.00"),
        )

    def test_eligible_application(self):
        result = check_ai_call_eligibility(self.application)

        self.assertTrue(result["eligible"])
        self.assertEqual(result["ats_score"], 85.0)

    def test_rejects_application_not_shortlisted(self):
        self.application.status = "applied"
        self.application.save()

        result = check_ai_call_eligibility(self.application)

        self.assertFalse(result["eligible"])
        self.assertIn("not shortlisted", result["reason"])

    def test_rejects_inactive_job(self):
        self.job.status = "inactive"
        self.job.save()

        result = check_ai_call_eligibility(self.application)

        self.assertFalse(result["eligible"])
        self.assertIn("not active", result["reason"])

    def test_rejects_inactive_candidate(self):
        self.candidate.is_active = False
        self.candidate.save()

        result = check_ai_call_eligibility(self.application)

        self.assertFalse(result["eligible"])
        self.assertIn("inactive", result["reason"])

    def test_rejects_candidate_without_consent(self):
        self.candidate.ai_call_consent = False
        self.candidate.save()

        result = check_ai_call_eligibility(self.application)

        self.assertFalse(result["eligible"])
        self.assertIn("not consented", result["reason"])

    def test_rejects_unavailable_candidate(self):
        self.candidate.available_for_ai_call = False
        self.candidate.save()

        result = check_ai_call_eligibility(self.application)

        self.assertFalse(result["eligible"])
        self.assertIn("not available", result["reason"])

    def test_rejects_application_without_ats_score(self):
        ATSScore.objects.filter(
            application=self.application
        ).delete()

        self.application.refresh_from_db()

        result = check_ai_call_eligibility(self.application)

        self.assertFalse(result["eligible"])
        self.assertEqual(
            result["reason"],
            "ATS score has not been calculated."
        )

    def test_rejects_ats_score_below_threshold(self):
        self.ats_score.score = Decimal("60.00")
        self.ats_score.save()

        result = check_ai_call_eligibility(self.application)

        self.assertFalse(result["eligible"])
        self.assertIn("below", result["reason"])
        self.assertEqual(result["ats_score"], 60.0)

    def test_creates_ai_call_for_eligible_application(self):
        result = create_ai_call_if_eligible(
              self.application.id
        )

        self.assertTrue(result["created"])
        self.assertEqual(
            result["status"],
            AICall.Status.SCHEDULED,
        )

        self.assertTrue(
            AICall.objects.filter(
                application=self.application
            ).exists()
        )

    def test_does_not_create_call_without_consent(self):
        self.candidate.ai_call_consent = False
        self.candidate.save()

        result = create_ai_call_if_eligible(
            self.application.id
        )

        self.assertFalse(result["created"])
        self.assertIn("not consented", result["reason"])

        self.assertFalse(
            AICall.objects.filter(
                application=self.application
            ).exists()
        )

    def test_does_not_create_duplicate_ai_calls(self):
                first_result = create_ai_call_if_eligible(
                    self.application.id
                )

                second_result = create_ai_call_if_eligible(
                    self.application.id
                )

                self.assertTrue(first_result["created"])
                self.assertFalse(second_result["created"])

                self.assertEqual(
                    AICall.objects.filter(
                        application=self.application
                    ).count(),
                    1,
                )
     
     
     
     
                
    def test_queue_task_changes_scheduled_call_to_queued(self):
        call = AICall.objects.create(
            application=self.application,
            status=AICall.Status.SCHEDULED,
            scheduled_at=timezone.now() - timedelta(minutes=1),
        )

        result = queue_ai_call.run(call.id)

        call.refresh_from_db()

        self.assertEqual(
            call.status,
            AICall.Status.QUEUED,
        )
        self.assertEqual(
            result["status"],
            AICall.Status.QUEUED,
        )

    @patch("apps.core.tasks.call_tasks.queue_ai_call.apply_async")
    def test_future_call_is_not_queued_early(self, mock_apply_async):
        future_time = timezone.now() + timedelta(hours=2)

        call = AICall.objects.create(
            application=self.application,
            status=AICall.Status.SCHEDULED,
            scheduled_at=future_time,
        )

        result = queue_ai_call.run(call.id)

        call.refresh_from_db()

        self.assertEqual(
            call.status,
            AICall.Status.SCHEDULED,
        )
        self.assertIn("not due yet", result["message"])
        mock_apply_async.assert_called_once()

    def test_duplicate_queue_task_does_not_change_status(self):
        call = AICall.objects.create(
            application=self.application,
            status=AICall.Status.QUEUED,
            scheduled_at=timezone.now() - timedelta(minutes=1),
        )

        result = queue_ai_call.run(call.id)

        call.refresh_from_db()

        self.assertEqual(
            call.status,
            AICall.Status.QUEUED,
        )
        self.assertIn("already queued", result["message"])
        
    def test_marks_call_failed_after_max_retries(self):
        call = AICall.objects.create(
            application=self.application,
            status=AICall.Status.SCHEDULED,
            scheduled_at=timezone.now() + timedelta(hours=2),
            max_retries=3,
        )

        with patch(
            "apps.core.tasks.call_tasks.queue_ai_call.apply_async",
            side_effect=RuntimeError("Simulated scheduler failure"),
        ):
            result = queue_ai_call.apply(
                args=[call.id],
                retries=3,
                throw=True,
            ).get()

        call.refresh_from_db()

        self.assertEqual(
            call.status,
            AICall.Status.FAILED,
        )
        self.assertEqual(call.retry_count, 3)
        self.assertIn(
            "Simulated scheduler failure",
            call.failure_reason,
        )
        self.assertEqual(
            result["status"],
            AICall.Status.FAILED,
        )