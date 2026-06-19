from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import frappe


@dataclass(frozen=True)
class AssistantSettings:
    enabled: bool = True
    required_role: str = "System Manager"
    navigation_enabled: bool = True
    live_data_enabled: bool = True
    voice_enabled: bool = True
    rag_enabled: bool = False
    subscription_enforcement_enabled: bool = True
    subscription_status: str = "Active"
    language_mode: str = "English and Urdu"
    llm_provider: str = "Deterministic"
    voice_provider: str = "Browser"
    stt_provider: str = "Browser"
    tts_provider: str = "Browser"
    log_questions: bool = True
    log_responses: bool = True
    rate_limit_enabled: bool = True
    requests_per_minute: int = 30
    requests_per_day: int = 500
    audit_log_retention_days: int = 90
    tool_log_retention_days: int = 90
    max_tool_rows: int = 500
    max_dynamic_rows: int = 20
    max_response_characters: int = 4000


def get_settings() -> AssistantSettings:
    try:
        if not frappe.db.exists("DocType", "Nexova AI Settings"):
            return AssistantSettings()

        doc = frappe.get_single("Nexova AI Settings")
    except Exception:
        return AssistantSettings()

    return AssistantSettings(
        enabled=_enabled(doc.enabled),
        required_role=doc.required_role or "System Manager",
        navigation_enabled=_enabled(getattr(doc, "navigation_enabled", 1)),
        live_data_enabled=_enabled(getattr(doc, "live_data_enabled", 1)),
        voice_enabled=_enabled(getattr(doc, "voice_enabled", 1)),
        rag_enabled=bool(getattr(doc, "rag_enabled", 0)),
        subscription_enforcement_enabled=_enabled(
            getattr(doc, "subscription_enforcement_enabled", 1)
        ),
        subscription_status=doc.subscription_status or "Active",
        language_mode=getattr(doc, "language_mode", None) or "English and Urdu",
        llm_provider=doc.llm_provider or "Deterministic",
        voice_provider=getattr(doc, "voice_provider", None) or "Browser",
        stt_provider=getattr(doc, "stt_provider", None) or "Browser",
        tts_provider=getattr(doc, "tts_provider", None) or "Browser",
        log_questions=_enabled(doc.log_questions),
        log_responses=_enabled(doc.log_responses),
        rate_limit_enabled=_enabled(getattr(doc, "rate_limit_enabled", 1)),
        requests_per_minute=_positive_int(getattr(doc, "requests_per_minute", 30), 30),
        requests_per_day=_positive_int(getattr(doc, "requests_per_day", 500), 500),
        audit_log_retention_days=_non_negative_int(
            getattr(doc, "audit_log_retention_days", 90),
            90,
        ),
        tool_log_retention_days=_non_negative_int(
            getattr(doc, "tool_log_retention_days", 90),
            90,
        ),
        max_tool_rows=_positive_int(getattr(doc, "max_tool_rows", 500), 500),
        max_dynamic_rows=_positive_int(getattr(doc, "max_dynamic_rows", 20), 20),
        max_response_characters=_positive_int(
            getattr(doc, "max_response_characters", 4000),
            4000,
        ),
    )


def _enabled(value: Any) -> bool:
    if value is None:
        return True

    return bool(value)


def _positive_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback

    return parsed if parsed > 0 else fallback


def _non_negative_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback

    return parsed if parsed >= 0 else fallback
