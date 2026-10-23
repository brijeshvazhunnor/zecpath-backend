
from unittest.mock import patch

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.models import User, Employer, Job
from apps.core.services.ai_client import AIServiceError


class AIInterviewQuestionsAPITests(APITestCase):
    def setUp(self):
        self.employer_user = User.objects.create_user(
            username="employer1",
            email="employer1@example.com",
            password="TestPassword123!",
            role=User.Role.EMPLOYER,
        )
        self.employer = Employer.objects.get(
            user=self.employer_user,
        )
        self.employer.company_name = "Test Company"
        self.employer.save()

        self.other_user = User.objects.create_user(
            username="employer2",
            email="employer2@example.com",
            password="TestPassword123!",
            role=User.Role.EMPLOYER,
        )
        self.other_employer = Employer.objects.get(
            user=self.other_user,
        )
        self.other_employer.company_name = "Other Company"
        self.other_employer.save()

        self.job = Job.objects.create(
            employer=self.employer,
            title="Python Backend Developer",
            description="Build Django REST APIs.",
            required_skills="Python\nDjango\nREST API",
            experience="Entry level",
            location="Kochi",
            job_type=Job.JobType.FULL_TIME,
            status=Job.Status.ACTIVE,
        )

        self.url = (
            f"/api/employer/jobs/{self.job.pk}/interview-questions/"
        )

    @override_settings(AI_ENABLED=True)
    @patch(
        "apps.core.views.generate_interview_questions",
        return_value=[
            {
                "question": "What is a Python dictionary?",
                "difficulty": "intermediate",
                "skill": "Python",
                "expected_topics": ["Key-value pairs", "Hashable keys"],
            }
        ],
    )
    def test_employer_can_generate_questions(self, mock_generate):
        self.client.force_authenticate(user=self.employer_user)

        response = self.client.post(
            self.url,
            {"question_count": 1, "difficulty": "intermediate"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["job_id"], self.job.pk)
        self.assertEqual(response.data["question_count"], 1)
        mock_generate.assert_called_once()

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.post(
            self.url,
            {"question_count": 1},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    @override_settings(AI_ENABLED=True)
    @patch("apps.core.views.generate_interview_questions")
    def test_other_employer_cannot_manage_job(self, mock_generate):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            self.url,
            {"question_count": 1},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        mock_generate.assert_not_called()

    @override_settings(AI_ENABLED=False)
    @patch("apps.core.views.generate_interview_questions")
    def test_disabled_ai_returns_503(self, mock_generate):
        self.client.force_authenticate(user=self.employer_user)

        response = self.client.post(
            self.url,
            {"question_count": 1},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        mock_generate.assert_not_called()

    @override_settings(AI_ENABLED=True)
    @patch("apps.core.views.generate_interview_questions")
    def test_invalid_question_count_returns_400(self, mock_generate):
        self.client.force_authenticate(user=self.employer_user)

        response = self.client.post(
            self.url,
            {"question_count": 0, "difficulty": "intermediate"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        mock_generate.assert_not_called()

    @override_settings(AI_ENABLED=True)
    @patch(
        "apps.core.views.generate_interview_questions",
        side_effect=AIServiceError("Simulated provider failure."),
    )
    def test_provider_failure_returns_502(self, mock_generate):
        self.client.force_authenticate(user=self.employer_user)

        response = self.client.post(
            self.url,
            {"question_count": 1, "difficulty": "intermediate"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_502_BAD_GATEWAY,
        )
