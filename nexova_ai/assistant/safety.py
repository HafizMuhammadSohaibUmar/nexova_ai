from __future__ import annotations

from nexova_ai.assistant.intent import normalize_text


BROAD_REQUEST_TERMS = (
    "export",
    "download",
    "dump",
    "all records",
    "all data",
    "entire database",
    "raw table",
    "sql",
    "payroll",
    "salary",
    "bank account",
    "bank details",
    "unrestricted ledger",
)


def is_broad_or_sensitive_request(question: str) -> bool:
    text = normalize_text(question)
    return any(term in text for term in BROAD_REQUEST_TERMS)


def broad_request_message() -> str:
    return (
        "I cannot provide unrestricted exports, raw tables, payroll, bank details, "
        "or database dumps. Please ask for a specific summary, document, customer, "
        "supplier, item, or bounded date range."
    )
