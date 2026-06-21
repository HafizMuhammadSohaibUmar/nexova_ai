from __future__ import annotations

from typing import Any

import frappe

from nexova_ai.assistant.contracts import response
from nexova_ai.assistant.discovery import find_readable_doctype, safe_list_fields
from nexova_ai.assistant.intent import normalize_text
from nexova_ai.assistant.query_engine import execute_query_plan, plan_dynamic_query
from nexova_ai.assistant.settings import get_settings
from nexova_ai.assistant.vocabulary import contains_any_phrase

MAX_COUNT_SCAN = 500


def can_try_dynamic_query(question: str) -> bool:
    text = normalize_text(question)
    dynamic_terms = (
        "total",
        "sum",
        "amount",
        "balance",
        "recent",
        "latest",
        "last",
        "top",
        "wise",
        "unpaid",
        "pending",
        "submitted",
        "draft",
        "cancelled",
        "today",
        "this month",
        "last 30 days",
        "kitna",
        "kitne",
        "dikhao",
        "batao",
    )
    return contains_any_phrase(question, ("list", "count", "navigation")) or any(
        term in text for term in dynamic_terms
    )


def answer_dynamic_query(question: str):
    query_plan = plan_dynamic_query(question)
    if query_plan:
        return execute_query_plan(query_plan)

    doctype = find_readable_doctype(question)
    if not doctype:
        return None

    text = normalize_text(question)
    fields = safe_list_fields(doctype["name"])
    settings = get_settings()
    max_dynamic_rows = max(1, min(settings.max_dynamic_rows, 100))

    if contains_any_phrase(text, ("count",)):
        count = _count_readable(doctype["name"])
        return response(
            f"There are {count} readable {doctype['label']} record(s) in the bounded result.",
            intent="dynamic_count",
            tool_name="dynamic_doctype_count",
            data={
                "type": "dynamic_count",
                "doctype": doctype["name"],
                "count": count,
                "summary_cards": [{"label": "Readable Records", "value": count}],
            },
        )

    rows = frappe.get_list(
        doctype["name"],
        fields=fields,
        order_by="modified desc",
        limit_page_length=max_dynamic_rows,
    )

    return response(
        f"Showing {len(rows)} recent readable {doctype['label']} record(s).",
        intent="dynamic_list",
        tool_name="dynamic_doctype_list",
        data={
            "type": "dynamic_list",
            "doctype": doctype["name"],
            "count": len(rows),
            "summary_cards": [{"label": "Records", "value": len(rows)}],
            "table": _rows_table(doctype["label"], fields, rows),
        },
    )


def _rows_table(label: str, fields: list[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "title": f"Recent {label} Records",
        "columns": [field.replace("_", " ").title() for field in fields],
        "rows": [[row.get(field) or "" for field in fields] for row in rows[:10]],
    }


def _count_readable(doctype: str) -> int:
    settings = get_settings()
    return len(
        frappe.get_list(
            doctype,
            fields=["name"],
            limit_start=0,
            limit_page_length=max(1, min(settings.max_tool_rows, MAX_COUNT_SCAN)),
        )
    )
