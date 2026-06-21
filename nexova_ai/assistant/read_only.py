from __future__ import annotations

import frappe

from nexova_ai.assistant.license import evaluate_configured_license
from nexova_ai.assistant.settings import get_settings


WRITE_OPERATIONS = {"create", "write", "delete", "submit", "cancel", "amend"}
ALWAYS_ALLOWED_READ_ONLY_DOCTYPES = {
    "Nexova AI Audit Log",
    "Nexova AI Settings",
    "Nexova AI Tool Execution Log",
    "Scheduled Job Log",
    "Error Log",
    "Activity Log",
    "Version",
}

METHOD_OPERATIONS = {
    "before_insert": "create",
    "before_save": "write",
    "before_submit": "submit",
    "before_cancel": "cancel",
    "on_trash": "delete",
}


def enforce_write_allowed(doc, method: str | None = None) -> None:
    if _system_operation_in_progress():
        return

    operation = METHOD_OPERATIONS.get(method or "", "write")
    allowed, message = is_write_allowed(getattr(doc, "doctype", ""), operation)
    if not allowed:
        frappe.throw(message)


def is_write_allowed(doctype: str, operation: str) -> tuple[bool, str]:
    settings = get_settings()
    decision = evaluate_configured_license(settings)

    if operation not in WRITE_OPERATIONS:
        return True, ""

    if decision.erp_read_only and doctype not in ALWAYS_ALLOWED_READ_ONLY_DOCTYPES:
        return False, decision.message or "This site is in read-only mode."

    return True, ""


def _system_operation_in_progress() -> bool:
    flags = getattr(frappe, "flags", None)
    if not flags:
        return False

    return any(
        bool(getattr(flags, flag, False))
        for flag in (
            "in_install",
            "in_migrate",
            "in_patch",
            "in_setup_wizard",
            "in_test",
            "ignore_nexova_read_only",
        )
    )
