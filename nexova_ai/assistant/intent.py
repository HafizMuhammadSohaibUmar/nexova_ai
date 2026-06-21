from __future__ import annotations

import re

from nexova_ai.assistant.vocabulary import (
    canonical_text,
    contains_any_phrase,
    contains_phrase,
)


def normalize_text(text: str) -> str:
    return canonical_text(text)


def contains_any(text: str, words: tuple[str, ...]) -> bool:
    normalized = normalize_text(text)
    return any(word in normalized for word in words)


def detect_language(text: str) -> str:
    if re.search(r"[\u0600-\u06ff]", text):
        return "ur"

    roman_urdu_terms = ("mera", "meri", "kitna", "kitni", "kitne", "kholo", "dikhao", "hisab", "wasooli")
    if contains_any(normalize_text(text), roman_urdu_terms):
        return "ur-roman"

    return "en"


def detect_intent(question: str) -> str:
    text = normalize_text(question)

    if _is_explicit_navigation(text):
        return "navigation"

    if contains_phrase(text, "knowledge"):
        return "knowledge"

    if contains_phrase(text, "profit_loss"):
        return "profit_and_loss"

    if contains_phrase(text, "cash_bank"):
        return "cash_bank_balance"

    if contains_phrase(text, "account_balance"):
        return "account_balance"

    if contains_phrase(text, "party_ledger"):
        return "party_ledger"

    if contains_phrase(text, "item_sales"):
        return "item_wise_sales"

    if contains_phrase(text, "customer_sales"):
        return "customer_wise_sales"

    if contains_phrase(text, "low_stock"):
        return "low_stock"

    if contains_phrase(text, "slow_moving"):
        return "slow_moving_items"

    if contains_phrase(text, "gross_profit"):
        return "gross_profit"

    if contains_phrase(text, "expenses"):
        return "expenses_summary"

    if contains_phrase(text, "payroll"):
        return "payroll_summary"

    if contains_phrase(text, "attendance"):
        return "attendance_summary"

    if contains_phrase(text, "manufacturing"):
        return "manufacturing_summary"

    if contains_phrase(text, "crm"):
        return "crm_summary"

    if contains_phrase(text, "project"):
        return "project_summary"

    if contains_phrase(text, "asset"):
        return "asset_summary"

    if contains_phrase(text, "tax"):
        return "tax_summary"

    if contains_phrase(text, "trend"):
        return "trend_analysis"

    if contains_phrase(text, "payables"):
        return "payables_summary"

    if contains_phrase(text, "receivables"):
        return "receivables_summary"

    if contains_phrase(text, "purchase"):
        return "purchase_summary"

    if contains_phrase(text, "stock"):
        return "stock_balance"

    if contains_phrase(text, "top") and contains_phrase(text, "customer"):
        return "customer_wise_sales"

    if contains_phrase(text, "top") and contains_phrase(text, "supplier"):
        return "purchase_summary"

    if contains_phrase(text, "customer"):
        return "customer_summary"

    if contains_phrase(text, "supplier"):
        return "supplier_summary"

    if contains_phrase(text, "item"):
        return "item_lookup"

    if contains_phrase(text, "quotation"):
        return "quotation_summary"

    if contains_phrase(text, "sales_order"):
        return "sales_order_summary"

    if contains_phrase(text, "purchase_order"):
        return "purchase_order_summary"

    if contains_phrase(text, "invoice"):
        return "invoice_summary"

    if contains_any_phrase(text, ("sales",)):
        return "sales_summary"

    if contains_phrase(text, "navigation"):
        return "navigation"

    return "unknown"


def _is_explicit_navigation(text: str) -> bool:
    return any(
        phrase in text
        for phrase in (
            "open",
            "go to",
            "goto",
            "navigate",
            "take me to",
            "kholo",
            "khol do",
            "open karo",
            "le chalo",
            "\u06a9\u06be\u0648\u0644\u0648",
            "\u062c\u0627\u0624",
        )
    )
