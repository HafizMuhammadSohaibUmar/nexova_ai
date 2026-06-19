from __future__ import annotations

import re
from time import perf_counter
from typing import Any

import frappe
from frappe.utils import flt, getdate, nowdate


@frappe.whitelist()
def ask_ai(question: str | None = None) -> dict[str, Any]:
    """Return a supported ERPNext answer using permission-aware Frappe APIs only."""
    started_at = perf_counter()
    clean_question = (question or "").strip()
    normalized = _normalize_question(clean_question)
    intent = "unknown"
    status = "Success"
    settings = _get_settings()

    try:
        if not settings["enabled"]:
            status = "Blocked"
            intent = "disabled"
            response = _response("Nexova AI is currently disabled.")
        elif settings["subscription_status"] != "Active":
            status = "Blocked"
            intent = "subscription"
            response = _response("Nexova AI is currently not active for this site.")
        elif not _has_role(settings["required_role"]):
            status = "Blocked"
            intent = "permission_denied"
            response = _permission_denied_response()
        elif not clean_question:
            intent = "empty"
            response = _response("Please ask about today's sales, stock balance, or pending receivables.")
        else:
            intent = _detect_intent(normalized)

            if intent == "today_sales":
                response = _today_sales()
            elif intent == "stock_balance":
                response = _stock_balance(clean_question)
            elif intent == "pending_receivables":
                response = _pending_receivables()
            else:
                response = _response(
                    "I can answer supported questions about today's sales, stock balance, and pending receivables."
                )
    except frappe.PermissionError:
        status = "Blocked"
        intent = "permission_denied"
        response = _permission_denied_response()
    except Exception:
        status = "Error"
        intent = "error"
        frappe.log_error(title="Nexova AI Error", message=frappe.get_traceback())
        response = _response("Something went wrong while asking ERPNext.")

    _safe_log_audit(
        settings=settings,
        question=clean_question,
        normalized_question=normalized,
        intent=intent,
        status=status,
        response=response,
        latency_ms=int((perf_counter() - started_at) * 1000),
    )

    return response


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


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def _normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", question.lower())).strip()


def _detect_intent(text: str) -> str:
    if _is_today_sales_intent(text):
        return "today_sales"

    if _is_stock_balance_intent(text):
        return "stock_balance"

    if _is_pending_receivables_intent(text):
        return "pending_receivables"

    return "unknown"


def _is_today_sales_intent(text: str) -> bool:
    return _contains_any(text, ("sale", "sales", "invoice", "invoices")) and _contains_any(
        text,
        ("today", "todays", "today s", "daily"),
    )


def _is_stock_balance_intent(text: str) -> bool:
    return _matches(text, ("stock", "balance")) or _contains_any(
        text,
        ("inventory", "on hand", "available stock"),
    )


def _is_pending_receivables_intent(text: str) -> bool:
    receivable_words = (
        "receivable",
        "receivables",
        "receiveable",
        "receiveables",
        "recievable",
        "recievables",
        "outstanding",
        "unpaid",
        "amount due",
    )

    return _contains_any(text, receivable_words)


def _has_role(role: str) -> bool:
    return role in set(frappe.get_roles())


def _get_settings() -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "enabled": True,
        "required_role": "System Manager",
        "log_questions": True,
        "log_responses": True,
        "subscription_status": "Active",
    }

    try:
        if not frappe.db.exists("DocType", "Nexova AI Settings"):
            return defaults

        settings = frappe.get_single("Nexova AI Settings")
    except Exception:
        return defaults

    defaults.update(
        {
            "enabled": _enabled_by_default(settings.enabled),
            "required_role": settings.required_role or "System Manager",
            "log_questions": _enabled_by_default(settings.log_questions),
            "log_responses": _enabled_by_default(settings.log_responses),
            "subscription_status": settings.subscription_status or "Active",
        }
    )

    return defaults


def _enabled_by_default(value: Any) -> bool:
    if value is None:
        return True

    return bool(value)


def _safe_log_audit(
    *,
    settings: dict[str, Any],
    question: str,
    normalized_question: str,
    intent: str,
    status: str,
    response: dict[str, Any],
    latency_ms: int,
) -> None:
    if not settings["log_questions"] and not settings["log_responses"]:
        return

    try:
        if not frappe.db.exists("DocType", "Nexova AI Audit Log"):
            return

        frappe.get_doc(
            {
                "doctype": "Nexova AI Audit Log",
                "user": frappe.session.user,
                "status": status,
                "intent": intent,
                "source": "Desk Page",
                "latency_ms": latency_ms,
                "question": question[:4000] if settings["log_questions"] else "",
                "normalized_question": normalized_question[:140] if settings["log_questions"] else "",
                "response_summary": response.get("message", "")[:4000]
                if settings["log_responses"]
                else "",
            }
        ).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(title="Nexova AI Audit Log Error", message=frappe.get_traceback())


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
