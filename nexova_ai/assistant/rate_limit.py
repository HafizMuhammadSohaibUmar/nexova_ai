from __future__ import annotations

from datetime import datetime

import frappe

from nexova_ai.assistant.settings import AssistantSettings


def check_rate_limit(settings: AssistantSettings) -> tuple[bool, str]:
    if not settings.rate_limit_enabled:
        return True, ""

    user = frappe.session.user or "Guest"
    now = datetime.utcnow()
    minute_key = f"nexova_ai:rate:{frappe.local.site}:{user}:{now:%Y%m%d%H%M}"
    day_key = f"nexova_ai:rate:{frappe.local.site}:{user}:{now:%Y%m%d}"
    cache = frappe.cache()

    minute_count = cache.incr(minute_key)
    day_count = cache.incr(day_key)

    if minute_count == 1:
        cache.expire(minute_key, 90)
    if day_count == 1:
        cache.expire(day_key, 90000)

    if minute_count > settings.requests_per_minute:
        return False, "Rate limit reached. Please wait a minute and try again."

    if day_count > settings.requests_per_day:
        return False, "Daily assistant limit reached for this user."

    return True, ""
