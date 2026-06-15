from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt, getdate, nowdate


@frappe.whitelist()
def ask_ai(question: str | None = None) -> dict[str, Any]:
    """Return an MVP ERPNext answer using permission-aware Frappe APIs only."""
    try:
        if not frappe.has_role("System Manager"):
            return _permission_denied_response()

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
    except frappe.PermissionError:
        return _permission_denied_response()
    except Exception:
        frappe.log_error(title="Nexova AI Error", message=frappe.get_traceback())
        return _response("Something went wrong while asking ERPNext.")


def _today_sales() -> dict[str, Any]:
    today = getdate(nowdate())
    invoices = _get_all_permission_aware(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "posting_date": today,
        },
        fields=["grand_total", "currency"],
        order_by="posting_time desc, creation desc",
    )

    totals_by_currency = _sum_by_currency(invoices, "grand_total")

    if totals_by_currency:
        totals_text = _format_currency_totals(totals_by_currency)
        message = f"Today's submitted sales are {totals_text} across {len(invoices)} invoice(s)."
    else:
        message = "There are no submitted sales invoices for today."

    return _response(
        message,
        data={
            "type": "todays_sales",
            "date": str(today),
            "count": len(invoices),
            "totals_by_currency": totals_by_currency,
        },
    )


def _stock_balance(question: str) -> dict[str, Any]:
    item_code = _extract_item_code(question)
    filters: dict[str, Any] = {}

    if item_code:
        filters["item_code"] = item_code

    bins = _get_all_permission_aware(
        "Bin",
        filters=filters,
        fields=["actual_qty"],
        order_by="actual_qty desc",
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
        },
    )


def _pending_receivables() -> dict[str, Any]:
    invoices = _get_all_permission_aware(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "outstanding_amount": [">", 0],
        },
        fields=["outstanding_amount", "currency"],
        order_by="due_date asc, posting_date asc",
    )

    totals_by_currency = _sum_by_currency(invoices, "outstanding_amount")

    if totals_by_currency:
        totals_text = _format_currency_totals(totals_by_currency)
        message = f"Pending receivables are {totals_text} across {len(invoices)} invoice(s)."
    else:
        message = "There are no pending receivables."

    return _response(
        message,
        data={
            "type": "pending_receivables",
            "count": len(invoices),
            "totals_by_currency": totals_by_currency,
        },
    )


def _get_all_permission_aware(
    doctype: str,
    *,
    filters: dict[str, Any],
    fields: list[str],
    order_by: str | None = None,
    page_length: int = 500,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    start = 0

    while True:
        page = frappe.get_list(
            doctype,
            filters=filters,
            fields=fields,
            order_by=order_by,
            limit_start=start,
            limit_page_length=page_length,
        )
        rows.extend(page)

        if len(page) < page_length:
            return rows

        start += page_length


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


def _sum_by_currency(rows: list[dict[str, Any]], amount_field: str) -> dict[str, float]:
    fallback_currency = frappe.defaults.get_global_default("currency") or "Currency"
    totals: dict[str, float] = {}

    for row in rows:
        currency = row.get("currency") or fallback_currency
        totals[currency] = totals.get(currency, 0.0) + flt(row.get(amount_field))

    return totals


def _format_currency_totals(totals_by_currency: dict[str, float]) -> str:
    formatted = []

    for currency, total in sorted(totals_by_currency.items()):
        formatted.append(
            frappe.format_value(total, {"fieldtype": "Currency", "options": currency})
        )

    return ", ".join(formatted)


def _permission_denied_response() -> dict[str, Any]:
    return _response("You do not have permission to access this information.")


def _response(message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "message": message,
        "data": data or {},
    }
