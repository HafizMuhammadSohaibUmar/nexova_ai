from __future__ import annotations

from time import perf_counter
from typing import Any

import frappe

from nexova_ai.assistant.audit import log_request
from nexova_ai.assistant.contracts import AssistantResult, response
from nexova_ai.assistant.dynamic_tools import answer_dynamic_query, can_try_dynamic_query
from nexova_ai.assistant.intent import detect_intent, detect_language, normalize_text
from nexova_ai.assistant.license import evaluate_configured_license
from nexova_ai.assistant.llm import suggest_intent_with_llm
from nexova_ai.assistant.navigation import resolve_navigation
from nexova_ai.assistant.permissions import has_required_role
from nexova_ai.assistant.rag import answer_knowledge_question
from nexova_ai.assistant.rate_limit import check_rate_limit
from nexova_ai.assistant.registry import get_tool
from nexova_ai.assistant.safety import broad_request_message, is_broad_or_sensitive_request
from nexova_ai.assistant.settings import get_settings
from nexova_ai.assistant.subscription import evaluate_subscription
from nexova_ai.assistant.tools import execute_tool


def ask(question: str | None = None, source: str = "Desk Page") -> dict[str, Any]:
    started_at = perf_counter()
    clean_question = (question or "").strip()
    normalized = normalize_text(clean_question)
    language = detect_language(clean_question)
    settings = get_settings()

    try:
        result = _handle_question(clean_question, normalized, settings)
    except frappe.PermissionError:
        result = response(
            "You do not have permission to access this information.",
            status="Blocked",
            intent="permission_denied",
        )
    except Exception:
        frappe.log_error(title="Invoxia AI Error", message=frappe.get_traceback())
        result = response(
            "Something went wrong while asking ERPNext.",
            status="Error",
            intent="error",
        )

    log_request(
        settings=settings,
        question=clean_question,
        normalized_question=normalized,
        result=result,
        latency_ms=int((perf_counter() - started_at) * 1000),
        source=source,
        language=language,
    )

    return result.as_dict()


def _handle_question(clean_question: str, normalized: str, settings) -> AssistantResult:
    if not settings.enabled:
        return response("Invoxia AI is currently disabled.", status="Blocked", intent="disabled")

    license_decision = evaluate_configured_license(settings)
    if not license_decision.ai_enabled:
        return response(
            license_decision.message or "Invoxia AI is not available for this license.",
            status="Blocked",
            intent="license",
        )

    subscription = evaluate_subscription(
        settings.subscription_status,
        settings.subscription_enforcement_enabled,
        grace_period_days=settings.subscription_grace_period_days,
    )
    if not subscription.allowed:
        return response(
            subscription.message,
            status="Blocked",
            intent="subscription",
        )

    if not has_required_role(settings.required_role):
        return response(
            "You do not have permission to access this information.",
            status="Blocked",
            intent="permission_denied",
        )

    allowed, message = check_rate_limit(settings)
    if not allowed:
        return response(message, status="Blocked", intent="rate_limit")

    if not clean_question:
        return response(
            "Please ask about sales, purchases, stock, receivables, payables, customers, suppliers, items, orders, invoices, navigation, or knowledge.",
            intent="empty",
        )

    if is_broad_or_sensitive_request(clean_question):
        return response(
            broad_request_message(),
            status="Blocked",
            intent="blocked_broad_request",
        )

    intent = detect_intent(clean_question)
    if intent == "unknown":
        suggestion = suggest_intent_with_llm(
            question=clean_question,
            provider=settings.llm_provider,
            endpoint=settings.local_llm_endpoint,
            model=settings.local_llm_model,
        )
        if suggestion:
            if suggestion.needs_clarification:
                return response(
                    "I understood the request, but need one more detail before using ERPNext data. Please be more specific.",
                    status="Blocked",
                    intent="clarification",
                    data={"type": "clarification", "suggested_intent": suggestion.intent},
                )
            intent = suggestion.intent

    if intent == "navigation":
        if not settings.navigation_enabled:
            return response("Navigation assistant is disabled for this site.", status="Blocked", intent=intent)

        return resolve_navigation(clean_question)

    if intent == "dynamic_query":
        if not settings.live_data_enabled:
            return response("Live data assistant is disabled for this site.", status="Blocked", intent=intent)

        dynamic_result = answer_dynamic_query(clean_question)
        if dynamic_result:
            return dynamic_result

        return response(
            "I could not find a readable ERPNext area for that query. Please name the DocType, report, customer, supplier, item, or account.",
            status="Blocked",
            intent="dynamic_query",
        )

    if intent == "knowledge":
        return answer_knowledge_question(clean_question, settings)

    if not settings.live_data_enabled:
        return response("Live data assistant is disabled for this site.", status="Blocked", intent=intent)

    dynamic_first_intents = {
        "customer_summary",
        "supplier_summary",
        "item_lookup",
        "quotation_summary",
        "sales_order_summary",
        "purchase_order_summary",
        "unknown",
    }

    if intent in dynamic_first_intents and can_try_dynamic_query(clean_question):
        dynamic_result = answer_dynamic_query(clean_question)
        if dynamic_result:
            return dynamic_result

    tool = get_tool(intent)
    if tool:
        tool_response = execute_tool(tool, clean_question)
        return response(
            tool_response.get("message", ""),
            data=tool_response.get("data", {}),
            intent=intent,
            tool_name=tool.name,
        )

    if can_try_dynamic_query(clean_question):
        dynamic_result = answer_dynamic_query(clean_question)
        if dynamic_result:
            return dynamic_result

    return response(
        "I can help with ERP navigation, readable lists and counts, sales, purchases, stock, receivables, payables, customers, suppliers, items, orders, invoices, and approved knowledge sources.",
        intent="unknown",
    )
