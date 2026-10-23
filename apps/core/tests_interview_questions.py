import json
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.core.services.ai_client import AIServiceError
from apps.core.services.interview_questions import (
    generate_interview_questions,
)


VALID_QUESTIONS = [
    {
        "question": "How does Django middleware work?",
        "difficulty": "intermediate",
        "skill": "Django",
        "expected_topics": [
            "Request-response lifecycle",
            "Middleware order",
        ],
    },
    {
        "question": "What is a Python dictionary?",
        "difficulty": "beginner",
        "skill": "Python",
        "expected_topics": [
            "Key-value pairs",
            "Hashable keys",
        ],
    },
]


class InterviewQuestionServiceTests(SimpleTestCase):

    def setUp(self):
        self.job_data = {
            "job_title": "Python Developer",
            "job_description": "Build and maintain Django REST APIs.",
            "required_skills": ["Python", "Django", "REST API"],
            "question_count": 2,
            "difficulty": "mixed",
        }

    @patch(
        "apps.core.services.interview_questions.generate_text",
        return_value=json.dumps(VALID_QUESTIONS),
    )
    def test_generates_valid_questions(self, mock_generate):
        result = generate_interview_questions(**self.job_data)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["skill"], "Django")
        mock_generate.assert_called_once()

    @patch("apps.core.services.interview_questions.generate_text")
    def test_rejects_missing_job_title(self, mock_generate):
        self.job_data["job_title"] = " "

        with self.assertRaises(ValueError):
            generate_interview_questions(**self.job_data)

        mock_generate.assert_not_called()

    @patch("apps.core.services.interview_questions.generate_text")
    def test_rejects_invalid_question_count(self, mock_generate):
        self.job_data["question_count"] = 100

        with self.assertRaises(ValueError):
            generate_interview_questions(**self.job_data)

        mock_generate.assert_not_called()

    @patch("apps.core.services.interview_questions.generate_text")
    def test_rejects_invalid_difficulty(self, mock_generate):
        self.job_data["difficulty"] = "expert"

        with self.assertRaises(ValueError):
            generate_interview_questions(**self.job_data)

        mock_generate.assert_not_called()

    @patch(
        "apps.core.services.interview_questions.generate_text",
        return_value="This is not JSON",
    )
    def test_rejects_malformed_provider_response(self, mock_generate):
        with self.assertRaisesMessage(
            AIServiceError, "invalid question data"
        ):
            generate_interview_questions(**self.job_data)

    @patch(
        "apps.core.services.interview_questions.generate_text",
        return_value=json.dumps(VALID_QUESTIONS[:1]),
    )
    def test_rejects_wrong_question_count(self, mock_generate):
        with self.assertRaisesMessage(
            AIServiceError, "unexpected number"
        ):
            generate_interview_questions(**self.job_data)

    @patch(
        "apps.core.services.interview_questions.generate_text",
        side_effect=AIServiceError("AI integration is disabled."),
    )
    def test_propagates_ai_service_errors(self, mock_generate):
        with self.assertRaisesMessage(AIServiceError, "disabled"):
            generate_interview_questions(**self.job_data)