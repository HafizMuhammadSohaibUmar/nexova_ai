from __future__ import annotations

from nexova_ai.assistant.license import evaluate_license
from nexova_ai.assistant.settings import get_settings


WRITE_OPERATIONS = {"create", "write", "delete", "submit", "cancel", "amend"}
ALWAYS_ALLOWED_BACKUP_DOCTYPES = {
    "Nexova AI Audit Log",
    "Nexova AI Tool Execution Log",
}


def is_write_allowed(doctype: str, operation: str) -> tuple[bool, str]:
    settings = get_settings()
    decision = evaluate_license(
        subscription_status=settings.subscription_status,
        license_mode=settings.license_mode,
        enforcement_enabled=settings.subscription_enforcement_enabled,
        grace_period_days=settings.subscription_grace_period_days,
    )

    if operation not in WRITE_OPERATIONS:
        return True, ""

    if decision.erp_read_only and doctype not in ALWAYS_ALLOWED_BACKUP_DOCTYPES:
        return False, decision.message or "This site is in read-only mode."

    return True, ""
