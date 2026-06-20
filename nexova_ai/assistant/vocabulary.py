from __future__ import annotations

import re
from difflib import SequenceMatcher


PHRASE_GROUPS: dict[str, tuple[str, ...]] = {
    "navigation": (
        "open",
        "go to",
        "goto",
        "navigate",
        "take me to",
        "show me",
        "kholo",
        "khol do",
        "open karo",
        "le chalo",
        "\u06a9\u06be\u0648\u0644\u0648",
        "\u062c\u0627\u0624",
    ),
    "knowledge": (
        "knowledge",
        "policy",
        "sop",
        "manual",
        "document",
        "docs",
        "\u062f\u0633\u062a\u0627\u0648\u06cc\u0632",
        "\u067e\u0627\u0644\u06cc\u0633\u06cc",
    ),
    "list": (
        "show",
        "list",
        "find",
        "search",
        "recent",
        "latest",
        "dikhao",
        "dikhado",
        "dekhao",
        "\u062f\u06a9\u06be\u0627\u0624",
    ),
    "count": (
        "count",
        "how many",
        "number of",
        "total records",
        "kitne",
        "kitni",
        "kitna",
        "\u06a9\u062a\u0646\u06d2",
        "\u06a9\u062a\u0646\u06cc",
    ),
    "sales": ("sale", "sales", "selling", "farokht", "faroukht", "\u0641\u0631\u0648\u062e\u062a", "\u0633\u06cc\u0644", "\u0628\u06a9\u0631\u06cc"),
    "purchase": ("purchase", "purchases", "buying", "khareed", "\u062e\u0631\u06cc\u062f", "\u067e\u0631\u0686\u06cc\u0632"),
    "receivables": (
        "receivable",
        "receivables",
        "receiveable",
        "receiveables",
        "recievable",
        "recievables",
        "outstanding",
        "unpaid",
        "amount due",
        "customer due",
        "pending receivables",
        "wasooli",
        "wasool",
        "\u0648\u0635\u0648\u0644",
        "\u0628\u0642\u0627\u06cc\u0627\u062c\u0627\u062a",
    ),
    "payables": (
        "payable",
        "payables",
        "supplier due",
        "vendor due",
        "unpaid purchase",
        "wajib ul ada",
        "wajib ada",
        "\u0648\u0627\u062c\u0628 \u0627\u0644\u0627\u062f\u0627",
    ),
    "stock": (
        "stock",
        "inventory",
        "on hand",
        "available stock",
        "stock balance",
        "maal",
        "godam",
        "\u06af\u0648\u062f\u0627\u0645",
        "\u0627\u0633\u0679\u0627\u06a9",
    ),
    "customer": (
        "customer",
        "customers",
        "client",
        "clients",
        "buyer",
        "party",
        "parties",
        "gahak",
        "gahaak",
        "\u06af\u0627\u06c1\u06a9",
        "\u06a9\u0633\u0679\u0645\u0631",
    ),
    "supplier": (
        "supplier",
        "suppliers",
        "vendor",
        "vendors",
        "seller",
        "party",
        "parties",
        "\u0633\u067e\u0644\u0627\u0626\u0631",
    ),
    "item": (
        "item",
        "items",
        "product",
        "products",
        "sku",
        "maal",
        "\u0622\u0626\u0679\u0645",
        "\u0645\u0635\u0646\u0648\u0639\u0627\u062a",
    ),
    "quotation": ("quotation", "quotations", "quote", "quotes", "\u06a9\u0648\u0679\u06cc\u0634\u0646"),
    "sales_order": ("sales order", "sale order", "customer order"),
    "purchase_order": ("purchase order", "buying order", "supplier order"),
    "invoice": ("invoice", "invoices", "bill", "bills", "\u0627\u0646\u0648\u0627\u0626\u0633"),
    "top": ("top", "highest", "largest", "best", "zyada", "sab se zyada"),
    "profit_loss": (
        "profit and loss",
        "p and l",
        "pnl",
        "income statement",
        "profit loss",
        "nafa nuqsan",
        "\u0646\u0641\u0639",
        "\u0646\u0642\u0635\u0627\u0646",
    ),
    "cash_bank": (
        "cash",
        "bank",
        "cash balance",
        "bank balance",
        "cash and bank",
        "cash bank",
        "\u06a9\u06cc\u0634",
        "\u0628\u06cc\u0646\u06a9",
    ),
    "account_balance": (
        "account balance",
        "balance of account",
        "ledger balance",
        "hisab balance",
        "khata balance",
        "\u062d\u0633\u0627\u0628",
        "\u06a9\u06be\u0627\u062a\u0627",
    ),
    "party_ledger": (
        "party ledger",
        "customer ledger",
        "supplier ledger",
        "ledger by party",
        "party ka ledger",
        "customer ka ledger",
        "\u0644\u06cc\u062c\u0631",
    ),
    "item_sales": (
        "item wise sales",
        "item sales",
        "product wise sales",
        "sales by item",
        "kis item ki sales",
        "\u0622\u0626\u0679\u0645 \u0648\u0627\u0626\u0632",
    ),
    "customer_sales": (
        "customer wise sales",
        "sales by customer",
        "customer sales",
        "client wise sales",
        "customer ki sales",
    ),
    "low_stock": (
        "low stock",
        "reorder",
        "reorder level",
        "short stock",
        "kam stock",
        "stock kam",
        "\u06a9\u0645 \u0627\u0633\u0679\u0627\u06a9",
    ),
    "slow_moving": (
        "slow moving",
        "dead stock",
        "not selling",
        "slow item",
        "slow inventory",
    ),
    "gross_profit": (
        "gross profit",
        "gp",
        "gross margin",
        "margin",
        "munafa",
        "\u0645\u0646\u0627\u0641\u0639",
    ),
    "expenses": (
        "expense",
        "expenses",
        "kharcha",
        "akhrajat",
        "\u062e\u0631\u0686",
        "\u0627\u062e\u0631\u0627\u062c\u0627\u062a",
    ),
    "payroll": ("payroll", "salary", "salaries", "wages", "tankhwa", "\u062a\u0646\u062e\u0648\u0627\u06c1"),
    "attendance": ("attendance", "present", "absent", "hazri", "\u062d\u0627\u0636\u0631\u06cc"),
    "manufacturing": ("manufacturing", "production", "work order", "bom", "banai", "\u067e\u0631\u0648\u0688\u06a9\u0634\u0646"),
    "crm": ("lead", "leads", "opportunity", "opportunities", "crm", "prospect"),
    "project": ("project", "projects", "task", "tasks", "milestone"),
    "asset": ("asset", "assets", "fixed asset", "اثاثہ", "\u0627\u062b\u0627\u062b\u06c1"),
    "tax": ("tax", "taxes", "vat", "gst", "sales tax", "\u0679\u06cc\u06a9\u0633"),
    "trend": ("trend", "compare", "comparison", "growth", "forecast", "pichle", "muqabla", "\u0645\u0648\u0627\u0632\u0646\u06c1"),
    "last": ("last", "latest", "recent", "akhri", "pichla", "\u0622\u062e\u0631\u06cc"),
}


VOICE_CORRECTIONS: tuple[tuple[str, str], ...] = (
    ("receiveables", "receivables"),
    ("receiveable", "receivable"),
    ("recievables", "receivables"),
    ("recievable", "receivable"),
    ("reciepts", "receipts"),
    ("sale invoice", "sales invoice"),
    ("sale order", "sales order"),
    ("next ova", "invoxia"),
    ("nex over", "invoxia"),
    ("pending receiveables", "pending receivables"),
)


DOMAIN_ALIASES: dict[str, tuple[str, ...]] = {
    "sales invoice": ("invoice", "bill", "customer invoice", "sales bill"),
    "purchase invoice": ("purchase bill", "supplier invoice", "vendor bill"),
    "customer": PHRASE_GROUPS["customer"],
    "supplier": PHRASE_GROUPS["supplier"],
    "item": PHRASE_GROUPS["item"],
    "bin": ("stock bin", "stock balance", "warehouse stock", "inventory"),
    "warehouse": ("godown", "godam", "store", "stock location"),
    "payment entry": ("payment", "receipt", "voucher"),
    "journal entry": ("journal", "gl entry", "voucher"),
    "general ledger": ("ledger", "gl", "account ledger"),
    "accounts receivable": ("receivables", "customer outstanding", "customer dues"),
    "accounts payable": ("payables", "supplier outstanding", "supplier dues"),
    "profit and loss": PHRASE_GROUPS["profit_loss"],
    "cash flow": ("cash", "bank", "cash flow"),
    "trial balance": ("trial", "account balance"),
    "dashboard": ("dashboard", "overview", "analytics"),
    "lead": PHRASE_GROUPS["crm"],
    "project": PHRASE_GROUPS["project"],
    "asset": PHRASE_GROUPS["asset"],
}


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]+", " ", (text or "").casefold(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


def canonical_text(text: str) -> str:
    normalized = normalize_text(text)

    for wrong, correct in VOICE_CORRECTIONS:
        normalized = _replace_phrase(normalized, wrong, correct)

    return normalized


def contains_phrase(text: str, group: str) -> bool:
    normalized = canonical_text(text)
    return any(_phrase_in_text(normalized, phrase) for phrase in PHRASE_GROUPS.get(group, ()))


def contains_any_phrase(text: str, groups: tuple[str, ...]) -> bool:
    return any(contains_phrase(text, group) for group in groups)


def business_aliases_for_label(label: str) -> tuple[str, ...]:
    normalized = canonical_text(label)
    compact = normalized.replace(" ", "")
    singular = normalized[:-1] if normalized.endswith("s") else normalized
    aliases = {normalized, compact, singular}

    for key, key_aliases in DOMAIN_ALIASES.items():
        if key in normalized or normalized in key:
            aliases.update(canonical_text(alias) for alias in key_aliases)

    words = normalized.split()
    aliases.update(word for word in words if len(word) > 2)
    return tuple(alias for alias in aliases if alias)


def fuzzy_match_score(text: str, label: str, aliases: tuple[str, ...]) -> int:
    normalized_text = canonical_text(text)
    normalized_label = canonical_text(label)
    candidates = {normalized_label, *[canonical_text(alias) for alias in aliases if alias]}

    best = 0
    for candidate in candidates:
        if not candidate:
            continue

        if _phrase_in_text(normalized_text, candidate):
            best = max(best, 100 + len(candidate))
            continue

        candidate_tokens = set(candidate.split())
        text_tokens = set(normalized_text.split())
        if candidate_tokens and candidate_tokens <= text_tokens:
            best = max(best, 80 + len(candidate_tokens))
            continue

        overlap = len(candidate_tokens & text_tokens)
        if overlap:
            best = max(best, 45 + (overlap * 8))

        ratio = SequenceMatcher(None, normalized_text, candidate).ratio()
        if ratio >= 0.72:
            best = max(best, int(40 + (ratio * 40)))

    return best


def _replace_phrase(text: str, wrong: str, correct: str) -> str:
    return re.sub(rf"\b{re.escape(wrong)}\b", correct, text)


def _phrase_in_text(text: str, phrase: str) -> bool:
    normalized_phrase = canonical_text(phrase)
    if not normalized_phrase:
        return False

    return re.search(rf"\b{re.escape(normalized_phrase)}\b", text) is not None
