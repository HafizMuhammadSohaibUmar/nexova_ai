from __future__ import annotations

from time import perf_counter
from typing import Any

import frappe
from frappe.utils import flt, getdate, nowdate

from nexova_ai.assistant.audit import log_tool_execution
from nexova_ai.assistant.contracts import ToolSpec, response
from nexova_ai.assistant.permissions import can_read_doctype

MAX_ROWS = 500


def execute_tool(tool: ToolSpec, question: str) -> dict[str, Any]:
    started_at = perf_counter()
    result = tool.handler(question)
    row_count = int(result.get("data", {}).get("count") or result.get("data", {}).get("row_count") or 0)
    log_tool_execution(
        tool_name=tool.name,
        status="Success",
        row_count=row_count,
        duration_ms=int((perf_counter() - started_at) * 1000),
        metadata={"category": tool.category, "risk_level": tool.risk_level},
    )
    return result


def sales_summary(question: str) -> dict[str, Any]:
    today_only = "today" in question.lower() or "daily" in question.lower()
    filters: dict[str, Any] = {"docstatus": 1}

    if today_only:
        filters["posting_date"] = getdate(nowdate())

    rows = _get_rows(
        "Sales Invoice",
        filters=filters,
        fields=["grand_total", "currency"],
        order_by="posting_date desc, posting_time desc, creation desc",
    )
    totals = _sum_by_currency(rows, "grand_total")
    label = "Today's submitted sales" if today_only else "Submitted sales"
    message = _summary_message(label, totals, len(rows), "invoice")

    return response(
        message,
        intent="sales_summary",
        tool_name="sales_summary",
        data={"type": "sales_summary", "count": len(rows), "totals_by_currency": totals},
    ).as_dict()


def purchase_summary(question: str) -> dict[str, Any]:
    rows = _get_rows(
        "Purchase Invoice",
        filters={"docstatus": 1},
        fields=["grand_total", "currency"],
        order_by="posting_date desc, creation desc",
    )
    totals = _sum_by_currency(rows, "grand_total")

    return response(
        _summary_message("Submitted purchases", totals, len(rows), "invoice"),
        intent="purchase_summary",
        tool_name="purchase_summary",
        data={"type": "purchase_summary", "count": len(rows), "totals_by_currency": totals},
    ).as_dict()


def stock_balance(question: str) -> dict[str, Any]:
    item_code = _extract_after_marker(question, (" for ", " item ", " item code "))
    filters: dict[str, Any] = {}

    if item_code:
        filters["item_code"] = item_code

    rows = _get_rows(
        "Bin",
        filters=filters,
        fields=["actual_qty"],
        order_by="actual_qty desc",
    )
    total_actual = sum(flt(row.get("actual_qty")) for row in rows)

    if item_code:
        message = f"Stock balance for {item_code} is {_format_float(total_actual)} unit(s) across {len(rows)} warehouse bin(s)."
    else:
        message = f"Current stock balance is {_format_float(total_actual)} unit(s) across {len(rows)} warehouse bin(s)."

    return response(
        message,
        intent="stock_balance",
        tool_name="stock_balance",
        data={
            "type": "stock_balance",
            "item_code": item_code,
            "total_actual_qty": total_actual,
            "count": len(rows),
        },
    ).as_dict()


def receivables_summary(question: str) -> dict[str, Any]:
    rows = _get_rows(
        "Sales Invoice",
        filters={"docstatus": 1, "outstanding_amount": [">", 0]},
        fields=["outstanding_amount", "currency"],
        order_by="due_date asc, posting_date asc",
    )
    totals = _sum_by_currency(rows, "outstanding_amount")

    return response(
        _summary_message("Pending receivables", totals, len(rows), "invoice"),
        intent="receivables_summary",
        tool_name="receivables_summary",
        data={"type": "receivables_summary", "count": len(rows), "totals_by_currency": totals},
    ).as_dict()


def payables_summary(question: str) -> dict[str, Any]:
    rows = _get_rows(
        "Purchase Invoice",
        filters={"docstatus": 1, "outstanding_amount": [">", 0]},
        fields=["outstanding_amount", "currency"],
        order_by="due_date asc, posting_date asc",
    )
    totals = _sum_by_currency(rows, "outstanding_amount")

    return response(
        _summary_message("Pending payables", totals, len(rows), "invoice"),
        intent="payables_summary",
        tool_name="payables_summary",
        data={"type": "payables_summary", "count": len(rows), "totals_by_currency": totals},
    ).as_dict()


def customer_summary(question: str) -> dict[str, Any]:
    count = _count_readable("Customer")
    return response(
        f"There are {count} readable customer record(s).",
        intent="customer_summary",
        tool_name="customer_summary",
        data={"type": "customer_summary", "count": count},
    ).as_dict()


def supplier_summary(question: str) -> dict[str, Any]:
    count = _count_readable("Supplier")
    return response(
        f"There are {count} readable supplier record(s).",
        intent="supplier_summary",
        tool_name="supplier_summary",
        data={"type": "supplier_summary", "count": count},
    ).as_dict()


def item_lookup(question: str) -> dict[str, Any]:
    item_code = _extract_after_marker(question, (" for ", " item ", " product "))
    filters: dict[str, Any] = {}

    if item_code:
        filters["name"] = ["like", f"%{item_code}%"]

    rows = _get_rows(
        "Item",
        filters=filters,
        fields=["name", "item_name", "disabled"],
        order_by="modified desc",
        page_length=20,
    )

    names = [row.get("item_name") or row.get("name") for row in rows[:5]]
    if names:
        message = "Top matching item(s): " + ", ".join(names)
    else:
        message = "No readable matching items found."

    return response(
        message,
        intent="item_lookup",
        tool_name="item_lookup",
        data={"type": "item_lookup", "count": len(rows), "items": rows[:5]},
    ).as_dict()


def quotation_summary(question: str) -> dict[str, Any]:
    return _document_count_summary("Quotation", "quotation_summary", "Quotation")


def sales_order_summary(question: str) -> dict[str, Any]:
    return _document_count_summary("Sales Order", "sales_order_summary", "Sales order")


def purchase_order_summary(question: str) -> dict[str, Any]:
    return _document_count_summary("Purchase Order", "purchase_order_summary", "Purchase order")


def invoice_summary(question: str) -> dict[str, Any]:
    if "purchase" in question.lower():
        return purchase_summary(question)
    return sales_summary(question)


def _document_count_summary(doctype: str, intent: str, label: str) -> dict[str, Any]:
    rows = _get_rows(
        doctype,
        filters={},
        fields=["name", "status"],
        order_by="modified desc",
        page_length=MAX_ROWS,
    )
    return response(
        f"There are {len(rows)} readable {label.lower()} record(s) in the current bounded result.",
        intent=intent,
        tool_name=intent,
        data={"type": intent, "count": len(rows), "row_count": len(rows)},
    ).as_dict()


def _get_rows(
    doctype: str,
    *,
    filters: dict[str, Any],
    fields: list[str],
    order_by: str | None = None,
    page_length: int = MAX_ROWS,
) -> list[dict[str, Any]]:
    if not can_read_doctype(doctype):
        raise frappe.PermissionError

    return frappe.get_list(
        doctype,
        filters=filters,
        fields=fields,
        order_by=order_by,
        limit_start=0,
        limit_page_length=min(page_length, MAX_ROWS),
    )


def _count_readable(doctype: str) -> int:
    if not can_read_doctype(doctype):
        raise frappe.PermissionError

    return len(
        frappe.get_list(
            doctype,
            fields=["name"],
            limit_start=0,
            limit_page_length=MAX_ROWS,
        )
    )


def _sum_by_currency(rows: list[dict[str, Any]], amount_field: str) -> dict[str, float]:
    fallback_currency = frappe.defaults.get_global_default("currency") or "Currency"
    totals: dict[str, float] = {}

    for row in rows:
        currency = row.get("currency") or fallback_currency
        totals[currency] = totals.get(currency, 0.0) + flt(row.get(amount_field))

    return totals


def _summary_message(label: str, totals_by_currency: dict[str, float], count: int, noun: str) -> str:
    if not totals_by_currency:
        return f"There are no matching submitted {noun}(s)."

    totals_text = _format_currency_totals(totals_by_currency)
    return f"{label} are {totals_text} across {count} {noun}(s)."


def _format_currency_totals(totals_by_currency: dict[str, float]) -> str:
    formatted = []

    for currency, total in sorted(totals_by_currency.items()):
        formatted.append(
            frappe.format_value(total, {"fieldtype": "Currency", "options": currency})
        )

    return ", ".join(formatted)


def _format_float(value: float) -> str:
    return frappe.format_value(value, {"fieldtype": "Float"})


def _extract_after_marker(question: str, markers: tuple[str, ...]) -> str | None:
    lowered = question.lower()

    for marker in markers:
        if marker in lowered:
            value = question[lowered.rfind(marker) + len(marker) :].strip()
            return value[:140] or None

    return None
