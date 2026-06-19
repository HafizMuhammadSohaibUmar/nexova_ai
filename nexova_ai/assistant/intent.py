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

    if contains_phrase(text, "navigation"):
        return "navigation"

    if contains_phrase(text, "knowledge"):
        return "knowledge"

    if contains_phrase(text, "payables"):
        return "payables_summary"

    if contains_phrase(text, "receivables"):
        return "receivables_summary"

    if contains_phrase(text, "purchase"):
        return "purchase_summary"

    if contains_phrase(text, "stock"):
        return "stock_balance"

    if contains_phrase(text, "top") and contains_phrase(text, "customer"):
        return "sales_summary"

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

    return "unknown"
