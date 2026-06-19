from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]+", " ", (text or "").lower(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


def contains_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def detect_language(text: str) -> str:
    if re.search(r"[\u0600-\u06ff]", text):
        return "ur"

    roman_urdu_terms = ("mera", "meri", "kitna", "kitni", "kholo", "dikhao", "hisab")
    if contains_any(normalize_text(text), roman_urdu_terms):
        return "ur-roman"

    return "en"


def detect_intent(question: str) -> str:
    text = normalize_text(question)

    if contains_any(text, ("open", "go to", "navigate", "kholo", "جاؤ", "کھولو")):
        return "navigation"

    if contains_any(text, ("knowledge", "policy", "sop", "manual", "document", "دستاویز", "پالیسی")):
        return "knowledge"

    if contains_any(text, ("purchase", "buying", "khareed", "خرید")):
        return "purchase_summary"

    if contains_any(text, ("payable", "payables", "supplier due", "unpaid purchase", "ادا", "واجب الادا")):
        return "payables_summary"

    if contains_any(text, ("receivable", "receivables", "receiveable", "receiveables", "recievable", "recievables", "outstanding", "unpaid", "amount due", "وصول", "بقایاجات")):
        return "receivables_summary"

    if contains_any(text, ("stock", "inventory", "on hand", "available stock", "maal", "گودام", "اسٹاک")):
        return "stock_balance"

    if contains_any(text, ("customer", "customers", "client", "گاہک", "کسٹمر")):
        return "customer_summary"

    if contains_any(text, ("supplier", "vendor", "سپلائر")):
        return "supplier_summary"

    if contains_any(text, ("item", "product", "sku", "مصنوعات", "آئٹم")):
        return "item_lookup"

    if contains_any(text, ("quotation", "quote", "کوٹیشن")):
        return "quotation_summary"

    if contains_any(text, ("sales order", "sale order")):
        return "sales_order_summary"

    if contains_any(text, ("purchase order",)):
        return "purchase_order_summary"

    if contains_any(text, ("invoice", "bill", "انوائس")):
        return "invoice_summary"

    if contains_any(text, ("sale", "sales", "farokht", "فروخت")):
        return "sales_summary"

    return "unknown"
