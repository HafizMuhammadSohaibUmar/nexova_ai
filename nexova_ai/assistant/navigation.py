from __future__ import annotations

from nexova_ai.assistant.contracts import NavigationTarget, response
from nexova_ai.assistant.intent import normalize_text
from nexova_ai.assistant.permissions import can_read_doctype


NAVIGATION_REGISTRY: tuple[NavigationTarget, ...] = (
    NavigationTarget(
        name="nexova_ai_assistant",
        label="Nexova AI Assistant",
        route=("nexova-ai-assistant",),
        category="page",
        required_doctype=None,
        aliases=("nexova", "assistant", "invoxia", "ai assistant"),
    ),
    NavigationTarget(
        name="sales_invoice_list",
        label="Sales Invoice List",
        route=("List", "Sales Invoice"),
        category="list",
        required_doctype="Sales Invoice",
        aliases=("sales invoice", "sale invoice", "invoices", "انوائس"),
    ),
    NavigationTarget(
        name="purchase_invoice_list",
        label="Purchase Invoice List",
        route=("List", "Purchase Invoice"),
        category="list",
        required_doctype="Purchase Invoice",
        aliases=("purchase invoice", "buying invoice"),
    ),
    NavigationTarget(
        name="customer_list",
        label="Customer List",
        route=("List", "Customer"),
        category="list",
        required_doctype="Customer",
        aliases=("customer", "customers", "client", "گاہک"),
    ),
    NavigationTarget(
        name="supplier_list",
        label="Supplier List",
        route=("List", "Supplier"),
        category="list",
        required_doctype="Supplier",
        aliases=("supplier", "suppliers", "vendor", "سپلائر"),
    ),
    NavigationTarget(
        name="item_list",
        label="Item List",
        route=("List", "Item"),
        category="list",
        required_doctype="Item",
        aliases=("item", "items", "product", "آئٹم"),
    ),
    NavigationTarget(
        name="stock_balance_report",
        label="Stock Balance Report",
        route=("query-report", "Stock Balance"),
        category="report",
        required_doctype="Bin",
        aliases=("stock balance", "inventory report", "اسٹاک"),
    ),
    NavigationTarget(
        name="accounts_receivable_report",
        label="Accounts Receivable Report",
        route=("query-report", "Accounts Receivable"),
        category="report",
        required_doctype="Sales Invoice",
        aliases=("accounts receivable", "receivables report", "outstanding receivable"),
    ),
    NavigationTarget(
        name="accounts_payable_report",
        label="Accounts Payable Report",
        route=("query-report", "Accounts Payable"),
        category="report",
        required_doctype="Purchase Invoice",
        aliases=("accounts payable", "payables report", "outstanding payable"),
    ),
    NavigationTarget(
        name="general_ledger_report",
        label="General Ledger Report",
        route=("query-report", "General Ledger"),
        category="report",
        required_doctype="GL Entry",
        aliases=("general ledger", "ledger", "gl report"),
    ),
)


def resolve_navigation(question: str):
    text = normalize_text(question)
    matches = [
        target
        for target in NAVIGATION_REGISTRY
        if any(alias in text for alias in target.aliases)
    ]

    if not matches:
        return response(
            "I can navigate to approved ERPNext lists, reports, and Nexova AI pages. Please name the area you want to open.",
            status="Blocked",
            intent="navigation",
            data={"type": "navigation", "action": "clarify"},
        )

    readable = [
        target
        for target in matches
        if target.required_doctype is None or can_read_doctype(target.required_doctype)
    ]

    if not readable:
        return response(
            "You do not have permission to open that area.",
            status="Blocked",
            intent="navigation",
            data={"type": "navigation", "action": "denied"},
        )

    if len(readable) > 1:
        labels = ", ".join(target.label for target in readable[:5])
        return response(
            f"I found multiple matching areas: {labels}. Please be more specific.",
            intent="navigation",
            data={"type": "navigation", "action": "clarify", "matches": [target.name for target in readable]},
        )

    target = readable[0]
    return response(
        f"Opening {target.label}.",
        intent="navigation",
        data={
            "type": "navigation",
            "action": "navigate",
            "route": list(target.route),
            "label": target.label,
        },
    )
