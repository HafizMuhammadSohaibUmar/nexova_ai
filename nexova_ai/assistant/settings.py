from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import frappe


@dataclass(frozen=True)
class AssistantSettings:
    enabled: bool = True
    required_role: str = "System Manager"
    deployment_mode: str = "Cloud Hosted"
    license_mode: str = "Online Subscription"
    license_key: str = ""
    site_id: str = ""
    company_id: str = ""
    license_server_url: str = "https://license.invoxia.sohaib.systems"
    license_verification_secret: str = ""
    offline_license_payload: str = ""
    offline_license_signature: str = ""
    license_plan: str = ""
    license_expires_on: str = ""
    license_last_checked_on: str = ""
    license_next_check_on: str = ""
    past_due_since: str = ""
    navigation_enabled: bool = True
    live_data_enabled: bool = True
    voice_enabled: bool = True
    rag_enabled: bool = False
    safe_actions_enabled: bool = False
    subscription_enforcement_enabled: bool = True
    subscription_status: str = "Active"
    subscription_grace_period_days: int = 7
    language_mode: str = "English and Urdu"
    llm_provider: str = "Deterministic"
    rag_provider: str = "Disabled"
    voice_provider: str = "Browser"
    stt_provider: str = "Browser"
    tts_provider: str = "Browser"
    local_stt_endpoint: str = "http://127.0.0.1:9000"
    local_llm_endpoint: str = "http://127.0.0.1:11434"
    local_llm_model: str = "qwen3:8b"
    local_rag_endpoint: str = "local"
    cloud_stt_provider: str = "Deepgram"
    cloud_llm_provider: str = "Mistral"
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
        deployment_mode=getattr(doc, "deployment_mode", None) or "Cloud Hosted",
        license_mode=getattr(doc, "license_mode", None) or "Online Subscription",
        license_key=getattr(doc, "license_key", None) or "",
        site_id=getattr(doc, "site_id", None) or "",
        company_id=getattr(doc, "company_id", None) or "",
        license_server_url=getattr(doc, "license_server_url", None)
        or "https://license.invoxia.sohaib.systems",
        license_verification_secret=_password(doc, "license_verification_secret"),
        offline_license_payload=getattr(doc, "offline_license_payload", None) or "",
        offline_license_signature=getattr(doc, "offline_license_signature", None) or "",
        license_plan=getattr(doc, "license_plan", None) or "",
        license_expires_on=str(getattr(doc, "license_expires_on", None) or ""),
        license_last_checked_on=str(getattr(doc, "license_last_checked_on", None) or ""),
        license_next_check_on=str(getattr(doc, "license_next_check_on", None) or ""),
        past_due_since=str(getattr(doc, "past_due_since", None) or ""),
        navigation_enabled=_enabled(getattr(doc, "navigation_enabled", 1)),
        live_data_enabled=_enabled(getattr(doc, "live_data_enabled", 1)),
        voice_enabled=_enabled(getattr(doc, "voice_enabled", 1)),
        rag_enabled=bool(getattr(doc, "rag_enabled", 0)),
        safe_actions_enabled=bool(getattr(doc, "safe_actions_enabled", 0)),
        subscription_enforcement_enabled=_enabled(
            getattr(doc, "subscription_enforcement_enabled", 1)
        ),
        subscription_status=doc.subscription_status or "Active",
        subscription_grace_period_days=_positive_int(
            getattr(doc, "subscription_grace_period_days", 7),
            7,
        ),
        language_mode=getattr(doc, "language_mode", None) or "English and Urdu",
        llm_provider=doc.llm_provider or "Deterministic",
        rag_provider=getattr(doc, "rag_provider", None) or "Disabled",
        voice_provider=getattr(doc, "voice_provider", None) or "Browser",
        stt_provider=getattr(doc, "stt_provider", None) or "Browser",
        tts_provider=getattr(doc, "tts_provider", None) or "Browser",
        local_stt_endpoint=getattr(doc, "local_stt_endpoint", None) or "http://127.0.0.1:9000",
        local_llm_endpoint=getattr(doc, "local_llm_endpoint", None) or "http://127.0.0.1:11434",
        local_llm_model=getattr(doc, "local_llm_model", None) or "qwen3:8b",
        local_rag_endpoint=getattr(doc, "local_rag_endpoint", None) or "local",
        cloud_stt_provider=getattr(doc, "cloud_stt_provider", None) or "Deepgram",
        cloud_llm_provider=getattr(doc, "cloud_llm_provider", None) or "Mistral",
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


def _password(doc: Any, fieldname: str) -> str:
    try:
        value = doc.get_password(fieldname)
    except Exception:
        value = getattr(doc, fieldname, None)

    return value or ""


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
