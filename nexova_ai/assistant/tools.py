from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from time import perf_counter
from typing import Any

import frappe
from frappe.utils import flt, getdate, nowdate

from nexova_ai.assistant.audit import log_tool_execution
from nexova_ai.assistant.contracts import ToolSpec, response
from nexova_ai.assistant.permissions import can_read_doctype
from nexova_ai.assistant.settings import get_settings
from nexova_ai.assistant.vocabulary import canonical_text, contains_phrase

MAX_ROWS_CAP = 500


@dataclass(frozen=True)
class QueryContext:
    filters: dict[str, Any]
    label: str
    filters_applied: dict[str, Any]


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
    context = _invoice_context(
        question,
        party_field="customer",
        party_markers=(" customer ", " client ", " for customer ", " for client "),
    )

    fields = ["grand_total", "currency", "customer"]
    rows = _get_rows(
        "Sales Invoice",
        filters=context.filters,
        fields=fields,
        order_by="posting_date desc, posting_time desc, creation desc",
    )
    totals = _sum_by_currency(rows, "grand_total")
    message = _summary_message(f"{context.label} submitted sales", totals, len(rows), "invoice")

    top_customers = []
    if _is_top_request(question, ("customer", "customers", "client", "clients")):
        top_customers = _top_party_totals(rows, "customer", "grand_total")
        if top_customers:
            message += " Top customers: " + _format_top_totals(top_customers)

    return response(
        message,
        intent="sales_summary",
        tool_name="sales_summary",
        data={
            "type": "sales_summary",
            "count": len(rows),
            "totals_by_currency": totals,
            "filters_applied": context.filters_applied,
            "summary_cards": _summary_cards(len(rows), totals, "Invoices"),
            "table": _party_table("Top Customers", "Customer", top_customers),
        },
    ).as_dict()


def purchase_summary(question: str) -> dict[str, Any]:
    context = _invoice_context(
        question,
        party_field="supplier",
        party_markers=(" supplier ", " vendor ", " for supplier ", " for vendor "),
    )
    rows = _get_rows(
        "Purchase Invoice",
        filters=context.filters,
        fields=["grand_total", "currency", "supplier"],
        order_by="posting_date desc, creation desc",
    )
    totals = _sum_by_currency(rows, "grand_total")
    top_suppliers = []
    if _is_top_request(question, ("supplier", "suppliers", "vendor", "vendors")):
        top_suppliers = _top_party_totals(rows, "supplier", "grand_total")

    return response(
        _summary_message(f"{context.label} submitted purchases", totals, len(rows), "invoice")
        + ((" Top suppliers: " + _format_top_totals(top_suppliers)) if top_suppliers else ""),
        intent="purchase_summary",
        tool_name="purchase_summary",
        data={
            "type": "purchase_summary",
            "count": len(rows),
            "totals_by_currency": totals,
            "filters_applied": context.filters_applied,
            "summary_cards": _summary_cards(len(rows), totals, "Invoices"),
            "table": _party_table("Top Suppliers", "Supplier", top_suppliers),
        },
    ).as_dict()


def stock_balance(question: str) -> dict[str, Any]:
    item_code = _extract_after_marker(question, (" for ", " item ", " item code "))
    warehouse = _extract_after_marker(question, (" warehouse ", " in warehouse ", " at warehouse "))
    filters: dict[str, Any] = {}

    if item_code:
        filters["item_code"] = item_code
    if warehouse:
        filters["warehouse"] = warehouse

    rows = _get_rows(
        "Bin",
        filters=filters,
        fields=["actual_qty", "item_code", "warehouse"],
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
            "warehouse": warehouse,
            "total_actual_qty": total_actual,
            "count": len(rows),
            "filters_applied": _compact_filters(filters),
            "summary_cards": [
                {"label": "Warehouse Bins", "value": len(rows)},
                {"label": "Actual Qty", "value": _format_float(total_actual)},
            ],
            "table": {
                "title": "Top Stock Bins",
                "columns": ["Item", "Warehouse", "Actual Qty"],
                "rows": [
                    [
                        row.get("item_code") or "",
                        row.get("warehouse") or "",
                        _format_float(flt(row.get("actual_qty"))),
                    ]
                    for row in rows[:10]
                ],
            },
        },
    ).as_dict()


def receivables_summary(question: str) -> dict[str, Any]:
    context = _invoice_context(
        question,
        party_field="customer",
        party_markers=(" customer ", " client ", " for customer ", " for client "),
    )
    context.filters["outstanding_amount"] = [">", 0]
    rows = _get_rows(
        "Sales Invoice",
        filters=context.filters,
        fields=["outstanding_amount", "currency", "customer"],
        order_by="due_date asc, posting_date asc",
    )
    totals = _sum_by_currency(rows, "outstanding_amount")
    top_customers = _top_party_totals(rows, "customer", "outstanding_amount")

    return response(
        _summary_message("Pending receivables", totals, len(rows), "invoice"),
        intent="receivables_summary",
        tool_name="receivables_summary",
        data={
            "type": "receivables_summary",
            "count": len(rows),
            "totals_by_currency": totals,
            "filters_applied": context.filters_applied,
            "summary_cards": _summary_cards(len(rows), totals, "Invoices"),
            "table": _party_table("Top Outstanding Customers", "Customer", top_customers),
        },
    ).as_dict()


def payables_summary(question: str) -> dict[str, Any]:
    context = _invoice_context(
        question,
        party_field="supplier",
        party_markers=(" supplier ", " vendor ", " for supplier ", " for vendor "),
    )
    context.filters["outstanding_amount"] = [">", 0]
    rows = _get_rows(
        "Purchase Invoice",
        filters=context.filters,
        fields=["outstanding_amount", "currency", "supplier"],
        order_by="due_date asc, posting_date asc",
    )
    totals = _sum_by_currency(rows, "outstanding_amount")
    top_suppliers = _top_party_totals(rows, "supplier", "outstanding_amount")

    return response(
        _summary_message("Pending payables", totals, len(rows), "invoice"),
        intent="payables_summary",
        tool_name="payables_summary",
        data={
            "type": "payables_summary",
            "count": len(rows),
            "totals_by_currency": totals,
            "filters_applied": context.filters_applied,
            "summary_cards": _summary_cards(len(rows), totals, "Invoices"),
            "table": _party_table("Top Outstanding Suppliers", "Supplier", top_suppliers),
        },
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
        data={
            "type": "item_lookup",
            "count": len(rows),
            "items": rows[:5],
            "summary_cards": [{"label": "Matches", "value": len(rows)}],
            "table": {
                "title": "Matching Items",
                "columns": ["Item", "Item Name", "Disabled"],
                "rows": [
                    [
                        row.get("name") or "",
                        row.get("item_name") or "",
                        "Yes" if row.get("disabled") else "No",
                    ]
                    for row in rows[:10]
                ],
            },
        },
    ).as_dict()


def quotation_summary(question: str) -> dict[str, Any]:
    return _document_count_summary(question, "Quotation", "quotation_summary", "Quotation")


def sales_order_summary(question: str) -> dict[str, Any]:
    return _document_count_summary(question, "Sales Order", "sales_order_summary", "Sales order")


def purchase_order_summary(question: str) -> dict[str, Any]:
    return _document_count_summary(question, "Purchase Order", "purchase_order_summary", "Purchase order")


def invoice_summary(question: str) -> dict[str, Any]:
    if contains_phrase(question, "purchase"):
        return purchase_summary(question)
    return sales_summary(question)


def profit_and_loss(question: str) -> dict[str, Any]:
    context = _document_context(question, date_field="posting_date")
    income = _gl_total(("Income",), context.filters)
    expense = _gl_total(("Expense",), context.filters)
    profit = income - expense
    currency = frappe.defaults.get_global_default("currency") or "Currency"
    return response(
        f"Bounded profit and loss estimate: income {_money(income, currency)}, expenses {_money(expense, currency)}, net {_money(profit, currency)}. Use the official Profit and Loss Statement for audited reporting.",
        intent="profit_and_loss",
        tool_name="profit_and_loss",
        data={
            "type": "profit_and_loss",
            "filters_applied": context.filters_applied,
            "summary_cards": [
                {"label": "Income", "value": _money(income, currency)},
                {"label": "Expenses", "value": _money(expense, currency)},
                {"label": "Net", "value": _money(profit, currency)},
            ],
            "report_route": ["query-report", "Profit and Loss Statement"],
        },
    ).as_dict()


def cash_bank_balance(question: str) -> dict[str, Any]:
    if not _doctype_exists("Account"):
        return _missing_doctype("Account", "cash_bank_balance")

    accounts = frappe.get_list(
        "Account",
        filters={"account_type": ["in", ["Cash", "Bank"]]},
        fields=["name", "account_name", "account_type"],
        limit_page_length=_configured_max_rows(),
    )
    rows = []
    total = 0.0
    for account in accounts:
        balance = _account_balance(account["name"])
        total += balance
        rows.append([account.get("account_name") or account["name"], account.get("account_type") or "", _money(balance)])

    return response(
        f"Cash and bank bounded balance is {_money(total)} across {len(accounts)} readable account(s).",
        intent="cash_bank_balance",
        tool_name="cash_bank_balance",
        data={
            "type": "cash_bank_balance",
            "count": len(accounts),
            "summary_cards": [{"label": "Accounts", "value": len(accounts)}, {"label": "Balance", "value": _money(total)}],
            "table": {"title": "Cash and Bank Accounts", "columns": ["Account", "Type", "Balance"], "rows": rows[:10]},
        },
    ).as_dict()


def account_balance(question: str) -> dict[str, Any]:
    account = _extract_after_marker(question, (" account ", " khata ", " hisab "))
    if not account:
        return response(
            "Please specify the account name for account balance.",
            status="Blocked",
            intent="account_balance",
            tool_name="account_balance",
            data={"type": "clarify", "missing": "account"},
        ).as_dict()

    rows = frappe.get_list("Account", filters={"name": ["like", f"%{account}%"]}, fields=["name"], limit_page_length=2)
    if len(rows) != 1:
        return response(
            "I found no account or more than one matching account. Please give the exact account name.",
            status="Blocked",
            intent="account_balance",
            tool_name="account_balance",
            data={"type": "clarify", "matches": [row["name"] for row in rows]},
        ).as_dict()

    balance = _account_balance(rows[0]["name"])
    return response(
        f"Account balance for {rows[0]['name']} is {_money(balance)}.",
        intent="account_balance",
        tool_name="account_balance",
        data={"type": "account_balance", "account": rows[0]["name"], "summary_cards": [{"label": "Balance", "value": _money(balance)}]},
    ).as_dict()


def party_ledger(question: str) -> dict[str, Any]:
    return _report_intent_response(
        "party_ledger",
        "I can open the party ledger report. Please include the exact customer or supplier if you want it filtered.",
        ["query-report", "General Ledger"],
    )


def item_wise_sales(question: str) -> dict[str, Any]:
    context = _document_context(question, date_field="posting_date")
    rows = _get_rows(
        "Sales Invoice Item",
        filters={},
        fields=["item_code", "item_name", "amount"],
        order_by="modified desc",
    )
    totals: dict[str, float] = {}
    for row in rows:
        item = row.get("item_code") or row.get("item_name") or "Unknown"
        totals[item] = totals.get(item, 0.0) + flt(row.get("amount"))
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:10]
    return response(
        f"Showing top {len(ranked)} item-wise sales rows in the bounded result.",
        intent="item_wise_sales",
        tool_name="item_wise_sales",
        data={
            "type": "item_wise_sales",
            "filters_applied": context.filters_applied,
            "summary_cards": [{"label": "Items", "value": len(ranked)}],
            "table": {"title": "Item-wise Sales", "columns": ["Item", "Amount"], "rows": [[name, _money(total)] for name, total in ranked]},
        },
    ).as_dict()


def customer_wise_sales(question: str) -> dict[str, Any]:
    return sales_summary("top customer " + question)


def low_stock(question: str) -> dict[str, Any]:
    rows = _get_rows(
        "Bin",
        filters={"actual_qty": ["<=", 0]},
        fields=["item_code", "warehouse", "actual_qty"],
        order_by="actual_qty asc",
    )
    return response(
        f"There are {len(rows)} readable low or zero stock bin(s) in the bounded result.",
        intent="low_stock",
        tool_name="low_stock",
        data={
            "type": "low_stock",
            "count": len(rows),
            "summary_cards": [{"label": "Low Stock Bins", "value": len(rows)}],
            "table": {"title": "Low Stock", "columns": ["Item", "Warehouse", "Actual Qty"], "rows": [[r.get("item_code") or "", r.get("warehouse") or "", _format_float(flt(r.get("actual_qty")))] for r in rows[:10]]},
        },
    ).as_dict()


def slow_moving_items(question: str) -> dict[str, Any]:
    return _report_intent_response(
        "slow_moving_items",
        "Slow-moving item analysis needs movement history and ageing rules. I can open Stock Ledger or show recent item/stock data for review.",
        ["query-report", "Stock Ledger"],
    )


def gross_profit(question: str) -> dict[str, Any]:
    return _report_intent_response(
        "gross_profit",
        "Gross profit should be verified from ERPNext's Gross Profit report because valuation and returns affect the calculation.",
        ["query-report", "Gross Profit"],
    )


def expenses_summary(question: str) -> dict[str, Any]:
    context = _document_context(question, date_field="posting_date")
    total = _gl_total(("Expense",), context.filters)
    return response(
        f"Bounded expense total is {_money(total)}.",
        intent="expenses_summary",
        tool_name="expenses_summary",
        data={"type": "expenses_summary", "filters_applied": context.filters_applied, "summary_cards": [{"label": "Expenses", "value": _money(total)}]},
    ).as_dict()


def payroll_summary(question: str) -> dict[str, Any]:
    return _doctype_count_summary("Salary Slip", "payroll_summary", "Payroll")


def attendance_summary(question: str) -> dict[str, Any]:
    return _doctype_count_summary("Attendance", "attendance_summary", "Attendance")


def manufacturing_summary(question: str) -> dict[str, Any]:
    return _doctype_count_summary("Work Order", "manufacturing_summary", "Manufacturing work orders")


def crm_summary(question: str) -> dict[str, Any]:
    lead_count = _safe_count("Lead")
    opportunity_count = _safe_count("Opportunity")
    return response(
        f"CRM bounded summary: {lead_count} readable lead(s), {opportunity_count} readable opportunit(ies).",
        intent="crm_summary",
        tool_name="crm_summary",
        data={"type": "crm_summary", "summary_cards": [{"label": "Leads", "value": lead_count}, {"label": "Opportunities", "value": opportunity_count}]},
    ).as_dict()


def project_summary(question: str) -> dict[str, Any]:
    return _doctype_count_summary("Project", "project_summary", "Projects")


def asset_summary(question: str) -> dict[str, Any]:
    return _doctype_count_summary("Asset", "asset_summary", "Assets")


def tax_summary(question: str) -> dict[str, Any]:
    return _report_intent_response(
        "tax_summary",
        "Tax answers depend on local configuration and tax templates. I can open ERPNext tax reports or show invoice tax rows after exact filters are provided.",
        ["query-report", "Sales Register"],
    )


def trend_analysis(question: str) -> dict[str, Any]:
    return _report_intent_response(
        "trend_analysis",
        "Trend and forecasting answers need a defined metric and period. Please ask for a specific comparison, such as monthly sales trend or customer-wise sales this month.",
        ["query-report", "Sales Analytics"],
    )


def _document_count_summary(question: str, doctype: str, intent: str, label: str) -> dict[str, Any]:
    context = _document_context(question, date_field="transaction_date")
    rows = _get_rows(
        doctype,
        filters=context.filters,
        fields=["name", "status"],
        order_by="modified desc",
        page_length=_configured_max_rows(),
    )
    return response(
        f"There are {len(rows)} readable {label.lower()} record(s) in the current bounded result.",
        intent=intent,
        tool_name=intent,
        data={
            "type": intent,
            "count": len(rows),
            "row_count": len(rows),
            "filters_applied": context.filters_applied,
            "summary_cards": [{"label": "Records", "value": len(rows)}],
            "table": {
                "title": f"Recent {label} Records",
                "columns": ["Name", "Status"],
                "rows": [[row.get("name") or "", row.get("status") or ""] for row in rows[:10]],
            },
        },
    ).as_dict()


def _doctype_count_summary(doctype: str, intent: str, label: str) -> dict[str, Any]:
    if not _doctype_exists(doctype):
        return _missing_doctype(doctype, intent)

    count = _count_readable(doctype)
    return response(
        f"There are {count} readable {label.lower()} record(s) in the bounded result.",
        intent=intent,
        tool_name=intent,
        data={"type": intent, "count": count, "summary_cards": [{"label": label, "value": count}]},
    ).as_dict()


def _report_intent_response(intent: str, message: str, route: list[str]) -> dict[str, Any]:
    return response(
        message,
        intent=intent,
        tool_name=intent,
        data={"type": intent, "action": "navigate", "route": route},
    ).as_dict()


def _missing_doctype(doctype: str, intent: str) -> dict[str, Any]:
    return response(
        f"{doctype} is not available on this site or app configuration.",
        status="Blocked",
        intent=intent,
        tool_name=intent,
        data={"type": intent, "missing_doctype": doctype},
    ).as_dict()


def _get_rows(
    doctype: str,
    *,
    filters: dict[str, Any],
    fields: list[str],
    order_by: str | None = None,
    page_length: int = MAX_ROWS_CAP,
) -> list[dict[str, Any]]:
    if not can_read_doctype(doctype):
        raise frappe.PermissionError

    return frappe.get_list(
        doctype,
        filters=filters,
        fields=fields,
        order_by=order_by,
        limit_start=0,
        limit_page_length=min(page_length, _configured_max_rows()),
    )


def _count_readable(doctype: str) -> int:
    if not can_read_doctype(doctype):
        raise frappe.PermissionError

    return len(
        frappe.get_list(
            doctype,
            fields=["name"],
            limit_start=0,
            limit_page_length=_configured_max_rows(),
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
            value = _trim_extracted_value(value)
            return value[:140] or None

    return None


def _invoice_context(
    question: str,
    *,
    party_field: str,
    party_markers: tuple[str, ...],
) -> QueryContext:
    context = _document_context(question, date_field="posting_date")
    filters = dict(context.filters)
    filters["docstatus"] = 1
    filters_applied = dict(context.filters_applied)

    company = _extract_after_marker(question, (" company ", " for company ", " in company "))
    party = _extract_after_marker(question, party_markers)

    if company:
        filters["company"] = company
        filters_applied["company"] = company

    if party:
        filters[party_field] = party
        filters_applied[party_field] = party

    return QueryContext(filters=filters, label=context.label, filters_applied=filters_applied)


def _document_context(question: str, *, date_field: str) -> QueryContext:
    filters: dict[str, Any] = {}
    filters_applied: dict[str, Any] = {}
    date_range = _date_range_from_question(question)

    if date_range:
        label, start, end = date_range
        filters[date_field] = ["between", [start, end]]
        filters_applied["date_range"] = {
            "label": label,
            "from": str(start),
            "to": str(end),
        }
        return QueryContext(filters=filters, label=label, filters_applied=filters_applied)

    return QueryContext(filters=filters, label="Matching", filters_applied=filters_applied)


def _date_range_from_question(question: str) -> tuple[str, date, date] | None:
    text = canonical_text(question)
    today = getdate(nowdate())

    if any(term in text for term in ("today", "daily", "aaj", "آج")):
        return ("Today's", today, today)

    if any(term in text for term in ("yesterday", "kal", "گزشتہ روز")):
        target = today - timedelta(days=1)
        return ("Yesterday's", target, target)

    if any(term in text for term in ("this week", "current week", "is haftay", "اس ہفتے")):
        start = today - timedelta(days=today.weekday())
        return ("This week's", start, today)

    if any(term in text for term in ("last week", "previous week", "pichle haftay", "پچھلے ہفتے")):
        this_week_start = today - timedelta(days=today.weekday())
        start = this_week_start - timedelta(days=7)
        end = this_week_start - timedelta(days=1)
        return ("Last week's", start, end)

    if any(term in text for term in ("last month", "previous month", "pichle mahine", "پچھلے مہینے")):
        first_this_month = today.replace(day=1)
        end = first_this_month - timedelta(days=1)
        start = end.replace(day=1)
        return ("Last month's", start, end)

    if any(term in text for term in ("this month", "current month", "is mahine", "اس مہینے")):
        end_day = monthrange(today.year, today.month)[1]
        start = today.replace(day=1)
        end = today.replace(day=end_day)
        return ("This month's", start, end)

    return None


def _is_top_request(question: str, dimensions: tuple[str, ...]) -> bool:
    text = canonical_text(question)
    return contains_phrase(text, "top") and any(dimension in text for dimension in dimensions)


def _top_party_totals(
    rows: list[dict[str, Any]],
    party_field: str,
    amount_field: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    totals: dict[tuple[str, str], float] = {}
    fallback_currency = frappe.defaults.get_global_default("currency") or "Currency"

    for row in rows:
        party = row.get(party_field)
        if not party:
            continue

        currency = row.get("currency") or fallback_currency
        key = (party, currency)
        totals[key] = totals.get(key, 0.0) + flt(row.get(amount_field))

    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    return [
        {"name": party, "currency": currency, "total": total}
        for (party, currency), total in ranked[:limit]
    ]


def _format_top_totals(rows: list[dict[str, Any]]) -> str:
    parts = []

    for row in rows:
        total = frappe.format_value(
            row["total"],
            {"fieldtype": "Currency", "options": row["currency"]},
        )
        parts.append(f"{row['name']} ({total})")

    return ", ".join(parts)


def _summary_cards(count: int, totals_by_currency: dict[str, float], count_label: str) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = [{"label": count_label, "value": count}]

    for currency, total in sorted(totals_by_currency.items()):
        cards.append(
            {
                "label": currency,
                "value": frappe.format_value(
                    total,
                    {"fieldtype": "Currency", "options": currency},
                ),
            }
        )

    return cards


def _party_table(
    title: str,
    party_label: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not rows:
        return None

    return {
        "title": title,
        "columns": [party_label, "Currency", "Total"],
        "rows": [
            [
                row.get("name") or "",
                row.get("currency") or "",
                frappe.format_value(
                    row.get("total") or 0,
                    {"fieldtype": "Currency", "options": row.get("currency")},
                ),
            ]
            for row in rows
        ],
    }


def _compact_filters(filters: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in filters.items() if key != "docstatus"}


def _trim_extracted_value(value: str) -> str:
    stop_words = (
        " today",
        " yesterday",
        " this week",
        " last week",
        " this month",
        " last month",
        " company ",
        " customer ",
        " supplier ",
        " warehouse ",
    )
    lowered = value.lower()
    cut_at = len(value)

    for stop_word in stop_words:
        index = lowered.find(stop_word)
        if index >= 0:
            cut_at = min(cut_at, index)

    return value[:cut_at].strip(" .,;:")


def _configured_max_rows() -> int:
    try:
        configured = get_settings().max_tool_rows
    except Exception:
        configured = MAX_ROWS_CAP

    return max(1, min(configured, MAX_ROWS_CAP))


def _doctype_exists(doctype: str) -> bool:
    try:
        return bool(frappe.db.exists("DocType", doctype))
    except Exception:
        return False


def _safe_count(doctype: str) -> int:
    if not _doctype_exists(doctype) or not can_read_doctype(doctype):
        return 0

    return _count_readable(doctype)


def _account_balance(account: str) -> float:
    if not _doctype_exists("GL Entry") or not can_read_doctype("GL Entry"):
        raise frappe.PermissionError

    rows = frappe.get_list(
        "GL Entry",
        filters={"account": account, "is_cancelled": 0},
        fields=["debit", "credit"],
        limit_page_length=_configured_max_rows(),
    )
    return sum(flt(row.get("debit")) - flt(row.get("credit")) for row in rows)


def _gl_total(root_types: tuple[str, ...], filters: dict[str, Any]) -> float:
    if not _doctype_exists("GL Entry") or not can_read_doctype("GL Entry"):
        return 0.0

    gl_filters = dict(filters)
    gl_filters["is_cancelled"] = 0
    rows = frappe.get_list(
        "GL Entry",
        filters=gl_filters,
        fields=["account", "debit", "credit"],
        limit_page_length=_configured_max_rows(),
    )

    total = 0.0
    for row in rows:
        account_type = _account_root_type(row.get("account"))
        if account_type not in root_types:
            continue

        total += flt(row.get("credit")) - flt(row.get("debit"))

    return total


def _account_root_type(account: str | None) -> str:
    if not account:
        return ""

    try:
        account_doc = frappe.get_cached_doc("Account", account)
        return account_doc.root_type or account_doc.account_type or ""
    except Exception:
        return ""


def _money(value: float, currency: str | None = None) -> str:
    return frappe.format_value(
        value,
        {"fieldtype": "Currency", "options": currency or frappe.defaults.get_global_default("currency")},
    )
