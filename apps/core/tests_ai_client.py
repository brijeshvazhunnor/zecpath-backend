from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from apps.core.services.ai_client import AIServiceError, generate_text


@override_settings(
    AI_ENABLED=True,
    AI_API_KEY="test-key",
    AI_API_BASE_URL="https://example.test/v1",
    AI_MODEL="test-model",
    AI_REQUEST_TIMEOUT=5,
)
class AIClientTests(SimpleTestCase):

    @override_settings(AI_ENABLED=False)
    def test_disabled_by_default(self):
        with self.assertRaisesMessage(AIServiceError, "disabled"):
            generate_text("Summarize this job description.")

    @override_settings(AI_API_KEY="")
    def test_missing_api_key(self):
        with self.assertRaisesMessage(AIServiceError, "not configured"):
            generate_text("Test prompt")

    def test_empty_prompt_is_rejected(self):
        with self.assertRaisesMessage(AIServiceError, "empty"):
            generate_text("   ")

    @patch("apps.core.services.ai_client.requests.post")
    def test_successful_response(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [
                {"message": {"content": "  AI response  "}}
            ]
        }
        mock_post.return_value = response

        result = generate_text("Explain the role.")

        self.assertEqual(result, "AI response")
        mock_post.assert_called_once()

        kwargs = mock_post.call_args.kwargs
        self.assertEqual(kwargs["timeout"], 5)
        self.assertEqual(
            kwargs["headers"]["Authorization"],
            "Bearer test-key",
        )
        self.assertEqual(
            mock_post.call_args.args[0],
            "https://example.test/v1/chat/completions",
        )

    @patch("apps.core.services.ai_client.requests.post")
    def test_provider_failure_is_handled(self, mock_post):
        import requests

        mock_post.side_effect = requests.Timeout("simulated timeout")

        with self.assertRaisesMessage(AIServiceError, "request failed"):
            generate_text("Test prompt")

    @patch("apps.core.services.ai_client.requests.post")
    def test_invalid_provider_response_is_handled(self, mock_post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {}
        mock_post.return_value = response

        with self.assertRaisesMessage(AIServiceError, "invalid response"):
            generate_text("Test prompt")
