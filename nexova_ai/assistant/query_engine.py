from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import frappe

from nexova_ai.assistant.contracts import response
from nexova_ai.assistant.metadata import DocTypeSummary, find_doctype_by_phrase, get_doctype_summary
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
    matches = find_doctype_by_phrase(question, limit=1)
    if not matches:
        return None

    summary = matches[0]
    if not summary.can_read:
        return None

    text = canonical_text(question)
    settings = get_settings()
    limit = max(1, min(settings.max_dynamic_rows, 100))

    if contains_any_phrase(text, ("count",)):
        return QueryPlan(
            doctype=summary.name,
            operation="count",
            fields=("name",),
            limit=limit,
        )

    aggregate_field = _pick_aggregate_field(text, summary)
    if aggregate_field and _asks_for_sum(text):
        return QueryPlan(
            doctype=summary.name,
            operation="sum",
            fields=(aggregate_field,),
            aggregate_field=aggregate_field,
            limit=limit,
        )

    group_by = _pick_group_field(text, summary)
    if group_by and aggregate_field:
        return QueryPlan(
            doctype=summary.name,
            operation="group_sum",
            fields=(group_by, aggregate_field),
            group_by=group_by,
            aggregate_field=aggregate_field,
            limit=limit,
        )

    return QueryPlan(
        doctype=summary.name,
        operation="list",
        fields=summary.safe_list_fields,
        limit=limit,
    )


def execute_query_plan(plan: QueryPlan):
    summary = get_doctype_summary(plan.doctype)
    if not summary.can_read:
        return response(
            "You do not have permission to read that data.",
            status="Blocked",
            intent="permission_denied",
        )

    if plan.operation == "count":
        count = len(frappe.get_list(plan.doctype, fields=["name"], limit_page_length=plan.limit))
        return response(
            f"There are {count} readable {summary.label} record(s) in the bounded result.",
            intent="dynamic_count",
            tool_name="dynamic_query_engine",
            data={"type": "dynamic_count", "query_plan": plan.as_dict(), "count": count},
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
    return any(term in text for term in ("sum", "total", "amount", "balance", "kitna", "kul"))


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


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
