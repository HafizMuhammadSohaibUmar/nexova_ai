from __future__ import annotations

from datetime import date, timedelta
from dataclasses import dataclass, field
from typing import Any

import frappe

from nexova_ai.assistant.contracts import response
from nexova_ai.assistant.metadata import DocTypeSummary, find_doctype_matches, get_doctype_summary
from nexova_ai.assistant.settings import get_settings
from nexova_ai.assistant.vocabulary import contains_any_phrase, canonical_text


@dataclass(frozen=True)
class QueryPlan:
    doctype: str
    operation: str
    fields: tuple[str, ...]
    filters: dict[str, Any] = field(default_factory=dict)
    group_by: str | None = None
    aggregate_field: str | None = None
    limit: int = 20

    def as_dict(self) -> dict[str, Any]:
        return {
            "doctype": self.doctype,
            "operation": self.operation,
            "fields": list(self.fields),
            "filters": self.filters,
            "group_by": self.group_by,
            "aggregate_field": self.aggregate_field,
            "limit": self.limit,
        }


def plan_dynamic_query(question: str) -> QueryPlan | None:
    matches = find_doctype_matches(question, limit=3)
    if not matches:
        return None

    if len(matches) > 1 and matches[1][0] >= matches[0][0] - 12:
        labels = ", ".join(summary.label for _, summary in matches[:3])
        return QueryPlan(
            doctype="",
            operation="clarify",
            fields=(),
            filters={"matches": labels},
        )

    summary = matches[0][1]
    if not summary.can_read:
        return None

    text = canonical_text(question)
    settings = get_settings()
    limit = max(1, min(settings.max_dynamic_rows, 100))
    filters = _build_filters(text, summary)

    if contains_any_phrase(text, ("count",)):
        return QueryPlan(
            doctype=summary.name,
            operation="count",
            fields=("name",),
            filters=filters,
            limit=limit,
        )

    aggregate_field = _pick_aggregate_field(text, summary)
    group_by = _pick_group_field(text, summary)
    if group_by and aggregate_field and _asks_for_grouping(text):
        return QueryPlan(
            doctype=summary.name,
            operation="group_sum",
            fields=(group_by, aggregate_field),
            filters=filters,
            group_by=group_by,
            aggregate_field=aggregate_field,
            limit=limit,
        )

    if aggregate_field and _asks_for_sum(text):
        return QueryPlan(
            doctype=summary.name,
            operation="sum",
            fields=(aggregate_field,),
            filters=filters,
            aggregate_field=aggregate_field,
            limit=limit,
        )

    return QueryPlan(
        doctype=summary.name,
        operation="list",
        fields=summary.safe_list_fields,
        filters=filters,
        limit=limit,
    )


def execute_query_plan(plan: QueryPlan):
    if plan.operation == "clarify":
        return response(
            f"I found multiple readable ERPNext areas: {plan.filters.get('matches')}. Please be more specific.",
            status="Blocked",
            intent="dynamic_clarify",
            tool_name="dynamic_query_engine",
            data={"type": "dynamic_clarify", "query_plan": plan.as_dict()},
        )

    summary = get_doctype_summary(plan.doctype)
    if not summary.can_read:
        return response(
            "You do not have permission to read that data.",
            status="Blocked",
            intent="permission_denied",
        )

    if plan.operation == "count":
        count = len(
            frappe.get_list(
                plan.doctype,
                fields=["name"],
                filters=plan.filters,
                limit_page_length=plan.limit,
            )
        )
        return response(
            f"There are {count} readable {summary.label} record(s) in the bounded result.",
            intent="dynamic_count",
            tool_name="dynamic_query_engine",
            data={"type": "dynamic_count", "query_plan": plan.as_dict(), "count": count},
        )

    if plan.operation == "group_sum" and plan.group_by and plan.aggregate_field:
        rows = frappe.get_list(
            plan.doctype,
            fields=[plan.group_by, plan.aggregate_field],
            filters=plan.filters,
            limit_page_length=plan.limit,
        )
        grouped: dict[str, float] = {}
        for row in rows:
            key = str(row.get(plan.group_by) or "Not Set")
            grouped[key] = grouped.get(key, 0.0) + _to_float(row.get(plan.aggregate_field))

        sorted_rows = sorted(grouped.items(), key=lambda item: item[1], reverse=True)[:10]
        return response(
            f"Showing bounded {summary.label} totals by {plan.group_by.replace('_', ' ')}.",
            intent="dynamic_group_sum",
            tool_name="dynamic_query_engine",
            data={
                "type": "dynamic_group_sum",
                "query_plan": plan.as_dict(),
                "count": len(rows),
                "table": {
                    "title": f"{summary.label} By {plan.group_by.replace('_', ' ').title()}",
                    "columns": [plan.group_by.replace("_", " ").title(), plan.aggregate_field.replace("_", " ").title()],
                    "rows": [[key, f"{value:.2f}"] for key, value in sorted_rows],
                },
            },
        )

    if plan.operation == "sum" and plan.aggregate_field:
        rows = frappe.get_list(
            plan.doctype,
            fields=[plan.aggregate_field],
            filters=plan.filters,
            limit_page_length=plan.limit,
        )
        total = sum(_to_float(row.get(plan.aggregate_field)) for row in rows)
        return response(
            f"The bounded total for {plan.aggregate_field.replace('_', ' ')} is {total:.2f}.",
            intent="dynamic_sum",
            tool_name="dynamic_query_engine",
            data={"type": "dynamic_sum", "query_plan": plan.as_dict(), "total": total, "count": len(rows)},
        )

    rows = frappe.get_list(
        plan.doctype,
        fields=list(plan.fields),
        filters=plan.filters,
        order_by="modified desc",
        limit_page_length=plan.limit,
    )
    return response(
        f"Showing {len(rows)} readable {summary.label} record(s).",
        intent="dynamic_list",
        tool_name="dynamic_query_engine",
        data={
            "type": "dynamic_list",
            "query_plan": plan.as_dict(),
            "count": len(rows),
            "table": {
                "title": f"Readable {summary.label} Records",
                "columns": [field.replace("_", " ").title() for field in plan.fields],
                "rows": [[row.get(field) or "" for field in plan.fields] for row in rows[:10]],
            },
        },
    )


def _asks_for_sum(text: str) -> bool:
    return any(term in text for term in ("sum", "total", "amount", "balance", "kitna", "kul", "how much"))


def _asks_for_grouping(text: str) -> bool:
    return any(term in text for term in (" by ", "wise", "top", "highest", "largest", "per "))


def _pick_aggregate_field(text: str, summary: DocTypeSummary) -> str | None:
    preferred = (
        "grand_total",
        "base_grand_total",
        "outstanding_amount",
        "paid_amount",
        "debit",
        "credit",
        "balance",
        "amount",
        "actual_qty",
        "qty",
    )
    for fieldname in preferred:
        if fieldname in summary.safe_numeric_fields:
            return fieldname

    return summary.safe_numeric_fields[0] if summary.safe_numeric_fields else None


def _pick_group_field(text: str, summary: DocTypeSummary) -> str | None:
    preferred = ("customer", "supplier", "item_code", "warehouse", "company", "status")
    for fieldname in preferred:
        if fieldname in summary.safe_filter_fields and fieldname in text:
            return fieldname

    return None


def _build_filters(text: str, summary: DocTypeSummary) -> dict[str, Any]:
    filters: dict[str, Any] = {}

    if "docstatus" in summary.safe_filter_fields:
        if any(term in text for term in ("submitted", "submit", "final")):
            filters["docstatus"] = 1
        elif any(term in text for term in ("draft", "unsubmitted")):
            filters["docstatus"] = 0
        elif any(term in text for term in ("cancelled", "canceled")):
            filters["docstatus"] = 2

    if "outstanding_amount" in summary.safe_filter_fields:
        if any(term in text for term in ("unpaid", "pending", "outstanding", "receivable", "payable")):
            filters["outstanding_amount"] = [">", 0]
        elif "paid" in text and "unpaid" not in text:
            filters["outstanding_amount"] = ["<=", 0]

    date_filter = _date_filter(text)
    if date_filter:
        date_field = _pick_date_field(summary)
        if date_field:
            filters[date_field] = date_filter

    status = _status_filter(text, summary)
    if status:
        filters["status"] = status

    return filters


def _pick_date_field(summary: DocTypeSummary) -> str | None:
    for fieldname in ("posting_date", "transaction_date", "attendance_date", "start_date", "creation", "modified"):
        if fieldname in summary.safe_filter_fields:
            return fieldname
    return None


def _date_filter(text: str):
    today = date.today()
    if "today" in text or "aaj" in text:
        return today.isoformat()

    if "this month" in text or "is month" in text or "current month" in text:
        start = today.replace(day=1)
        return ["between", [start.isoformat(), today.isoformat()]]

    if "last 30 days" in text or "pichle 30 din" in text:
        return [">=", (today - timedelta(days=30)).isoformat()]

    if "this year" in text or "current year" in text:
        start = today.replace(month=1, day=1)
        return ["between", [start.isoformat(), today.isoformat()]]

    return None


def _status_filter(text: str, summary: DocTypeSummary) -> str | None:
    if "status" not in summary.safe_filter_fields:
        return None

    status_terms = {
        "open": "Open",
        "closed": "Closed",
        "overdue": "Overdue",
        "unpaid": "Unpaid",
        "paid": "Paid",
        "completed": "Completed",
        "cancelled": "Cancelled",
        "canceled": "Cancelled",
    }
    for term, value in status_terms.items():
        if term in text:
            return value

    return None


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
