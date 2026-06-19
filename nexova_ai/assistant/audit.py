from __future__ import annotations

from typing import Any

import frappe

from nexova_ai.assistant.contracts import AssistantResult
from nexova_ai.assistant.settings import AssistantSettings


def log_request(
    *,
    settings: AssistantSettings,
    question: str,
    normalized_question: str,
    result: AssistantResult,
    latency_ms: int,
    source: str,
    language: str,
) -> None:
    if not settings.log_questions and not settings.log_responses:
        return

    try:
        if not frappe.db.exists("DocType", "Nexova AI Audit Log"):
            return

        frappe.get_doc(
            {
                "doctype": "Nexova AI Audit Log",
                "user": frappe.session.user,
                "status": result.status,
                "intent": result.intent,
                "tool_name": result.tool_name,
                "source": source,
                "language": language,
                "latency_ms": latency_ms,
                "question": question[:4000] if settings.log_questions else "",
                "normalized_question": normalized_question[:140]
                if settings.log_questions
                else "",
                "response_summary": result.message[:4000] if settings.log_responses else "",
            }
        ).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(title="Nexova AI Audit Log Error", message=frappe.get_traceback())


def log_tool_execution(
    *,
    tool_name: str,
    status: str,
    row_count: int,
    duration_ms: int,
    metadata: dict[str, Any] | None = None,
) -> None:
    try:
        if not frappe.db.exists("DocType", "Nexova AI Tool Execution Log"):
            return

        frappe.get_doc(
            {
                "doctype": "Nexova AI Tool Execution Log",
                "user": frappe.session.user,
                "tool_name": tool_name,
                "status": status,
                "row_count": row_count,
                "duration_ms": duration_ms,
                "metadata_json": frappe.as_json(metadata or {}),
            }
        ).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(title="Nexova AI Tool Log Error", message=frappe.get_traceback())
