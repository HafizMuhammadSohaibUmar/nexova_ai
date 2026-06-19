from __future__ import annotations

from datetime import timedelta

import frappe
from frappe.utils import now_datetime

from nexova_ai.assistant.settings import get_settings


def cleanup_audit_logs() -> None:
    """Delete old assistant logs according to site settings."""
    settings = get_settings()

    _delete_old_logs("Nexova AI Audit Log", settings.audit_log_retention_days)
    _delete_old_logs("Nexova AI Tool Execution Log", settings.tool_log_retention_days)


def _delete_old_logs(doctype: str, retention_days: int) -> None:
    if retention_days <= 0:
        return

    try:
        if not frappe.db.exists("DocType", doctype):
            return

        cutoff = now_datetime() - timedelta(days=retention_days)
        frappe.db.delete(doctype, {"creation": ["<", cutoff]})
    except Exception:
        frappe.log_error(
            title=f"{doctype} Retention Cleanup Error",
            message=frappe.get_traceback(),
        )
