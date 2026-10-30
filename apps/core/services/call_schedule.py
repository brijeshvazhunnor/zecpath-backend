from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone


def get_next_ai_call_time(now=None):
    """
    Return the next permitted AI calling time.
    """

    call_timezone = ZoneInfo(settings.AI_CALL_TIMEZONE)

    start_time = time.fromisoformat(
        settings.AI_CALL_WINDOW_START
    )
    end_time = time.fromisoformat(
        settings.AI_CALL_WINDOW_END
    )

    if start_time >= end_time:
        raise ValueError(
            "AI call window start must be earlier than its end."
        )

    if now is None:
        now = timezone.now()

    local_now = now.astimezone(call_timezone)

    window_start = datetime.combine(
        local_now.date(),
        start_time,
        tzinfo=call_timezone,
    )

    window_end = datetime.combine(
        local_now.date(),
        end_time,
        tzinfo=call_timezone,
    )

    if local_now < window_start:
        return window_start

    if local_now >= window_end:
        next_day = local_now.date() + timedelta(days=1)

        return datetime.combine(
            next_day,
            start_time,
            tzinfo=call_timezone,
        )

    return local_now