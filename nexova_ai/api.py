from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt, getdate, nowdate


@frappe.whitelist()
def ask_ai(question: str | None = None) -> dict[str, Any]:
    """Return an MVP ERPNext answer using permission-aware Frappe APIs only."""
    clean_question = (question or "").strip()
    normalized = clean_question.lower()

    if not clean_question:
        return _response("Please ask about today's sales, stock balance, or pending receivables.")

    if _matches(normalized, ("today", "sale")) or _matches(normalized, ("sales",)):
        return _today_sales()

    if _matches(normalized, ("stock", "balance")) or _matches(normalized, ("inventory",)):
        return _stock_balance(clean_question)

    if _matches(normalized, ("pending", "receivable")) or _matches(normalized, ("outstanding",)):
        return _pending_receivables()

    return _response(
        "I can answer MVP questions about today's sales, stock balance, and pending receivables."
    )


def _today_sales() -> dict[str, Any]:
    today = getdate(nowdate())
    invoices = frappe.get_list(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "posting_date": today,
        },
        fields=["name", "customer", "grand_total", "currency"],
        order_by="posting_time desc, creation desc",
        limit_page_length=100,
    )

    total = sum(flt(row.get("grand_total")) for row in invoices)
    currency = _first_value(invoices, "currency") or frappe.defaults.get_global_default("currency")

    message = f"Today's submitted sales are {frappe.format_value(total, {'fieldtype': 'Currency', 'options': currency})} across {len(invoices)} invoice(s)."

    return _response(
        message,
        data={
            "type": "todays_sales",
            "date": str(today),
            "total": total,
            "currency": currency,
            "count": len(invoices),
            "invoices": invoices[:10],
        },
    )


def _stock_balance(question: str) -> dict[str, Any]:
    item_code = _extract_item_code(question)
    filters: dict[str, Any] = {}

    if item_code:
        filters["item_code"] = item_code

    bins = frappe.get_list(
        "Bin",
        filters=filters,
        fields=["item_code", "warehouse", "actual_qty", "projected_qty", "reserved_qty"],
        order_by="actual_qty desc",
        limit_page_length=100,
    )

    total_actual = sum(flt(row.get("actual_qty")) for row in bins)

    if item_code:
        message = f"Stock balance for {item_code} is {frappe.format_value(total_actual, {'fieldtype': 'Float'})} unit(s) across {len(bins)} warehouse bin(s)."
    else:
        message = f"Current stock balance is {frappe.format_value(total_actual, {'fieldtype': 'Float'})} unit(s) across {len(bins)} warehouse bin(s)."

    return _response(
        message,
        data={
            "type": "stock_balance",
            "item_code": item_code,
            "total_actual_qty": total_actual,
            "count": len(bins),
            "bins": bins[:20],
        },
    )


def _pending_receivables() -> dict[str, Any]:
    invoices = frappe.get_list(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "outstanding_amount": [">", 0],
        },
        fields=["name", "customer", "posting_date", "due_date", "outstanding_amount", "currency"],
        order_by="due_date asc, posting_date asc",
        limit_page_length=100,
    )

    total = sum(flt(row.get("outstanding_amount")) for row in invoices)
    currency = _first_value(invoices, "currency") or frappe.defaults.get_global_default("currency")

    message = f"Pending receivables are {frappe.format_value(total, {'fieldtype': 'Currency', 'options': currency})} across {len(invoices)} invoice(s)."

    return _response(
        message,
        data={
            "type": "pending_receivables",
            "total": total,
            "currency": currency,
            "count": len(invoices),
            "invoices": invoices[:20],
        },
    )


def _matches(text: str, words: tuple[str, ...]) -> bool:
    return all(word in text for word in words)


def _extract_item_code(question: str) -> str | None:
    lowered = question.lower()
    markers = (" for ", " item ", " item code ")

    for marker in markers:
        if marker in lowered:
            value = question[lowered.rfind(marker) + len(marker) :].strip()
            return value[:140] or None

    return None


def _first_value(rows: list[dict[str, Any]], key: str) -> Any:
    for row in rows:
        value = row.get(key)
        if value:
            return value
    return None


def _response(message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "message": message,
        "data": data or {},
    }
