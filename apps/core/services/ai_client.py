import requests
from django.conf import settings


class AIServiceError(Exception):
    """Raised when the optional AI service cannot complete a request."""


def generate_text(prompt, system_prompt="You are a helpful recruitment assistant."):
    """
    Generate text through an OpenAI-compatible chat-completions API.

    AI is opt-in. Never log API credentials or send candidate data unless
    the caller has deliberately selected and authorized that data.
    """
    if not getattr(settings, "AI_ENABLED", False):
        raise AIServiceError("AI integration is disabled.")

    api_key = getattr(settings, "AI_API_KEY", "")
    if not api_key:
        raise AIServiceError("AI API key is not configured.")

    if not isinstance(prompt, str) or not prompt.strip():
        raise AIServiceError("Prompt must not be empty.")

    base_url = settings.AI_API_BASE_URL.rstrip("/")
    endpoint = f"{base_url}/chat/completions"

    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    try:
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=settings.AI_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        if not isinstance(content, str) or not content.strip():
            raise AIServiceError("AI provider returned empty content.")

        return content.strip()

    except AIServiceError:
        raise
    except requests.RequestException as exc:
        raise AIServiceError("AI provider request failed.") from exc
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise AIServiceError("AI provider returned an invalid response.") from exc
