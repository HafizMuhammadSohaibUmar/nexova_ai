from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from nexova_ai.assistant.intent import normalize_text
from nexova_ai.assistant.registry import TOOL_REGISTRY
from nexova_ai.assistant.vocabulary import fuzzy_match_score


BUILTIN_ROUTER_INTENTS = {"navigation", "dynamic_query", "knowledge", "unknown"}


@dataclass(frozen=True)
class IntentSuggestion:
    intent: str
    confidence: int
    reason: str
    arguments: dict[str, Any] | None = None
    needs_clarification: bool = False


SYSTEM_PROMPT = """You are Invoxia AI's ERPNext intent router.
Return JSON only. Do not explain.
Choose only one approved intent from the provided list.
Never invent tools. Never query ERPNext directly.
Use needs_clarification=true when the command is ambiguous.
Use dynamic_query for safe metadata-driven ERPNext list, count, sum, or group questions.
Use navigation for opening lists, reports, dashboards, workspaces, pages, or documents.
Schema:
{"intent":"tool_name","confidence":0.0,"arguments":{},"needs_clarification":false,"clarification_question":""}
"""


def suggest_intent(question: str, provider: str) -> IntentSuggestion | None:
    """Controlled LLM fallback seam.

    The current implementation stays local and deterministic. Cloud/local LLM
    providers must later return only approved tool names and bounded arguments.
    """

    if provider in {"Disabled", "Deterministic"}:
        return None

    text = normalize_text(question)
    candidates: list[IntentSuggestion] = []

    for tool in TOOL_REGISTRY.values():
        score = fuzzy_match_score(text, tool.label, tool.aliases)
        if score >= 60:
            candidates.append(
                IntentSuggestion(
                    intent=tool.name,
                    confidence=score,
                    reason=f"Matched approved tool aliases for {tool.label}.",
                )
            )

    if not candidates:
        return None

    return sorted(candidates, key=lambda candidate: candidate.confidence, reverse=True)[0]


def suggest_intent_with_llm(
    *,
    question: str,
    provider: str,
    endpoint: str,
    model: str,
    timeout_seconds: int = 30,
) -> IntentSuggestion | None:
    if provider != "Local Ollama":
        return suggest_intent(question, provider)

    payload = _ollama_payload(question=question, model=model)
    try:
        raw = _post_json(endpoint.rstrip("/") + "/api/chat", payload, timeout_seconds)
    except RuntimeError:
        return suggest_intent(question, provider)

    suggestion = parse_intent_response(raw)
    if suggestion:
        return suggestion

    return suggest_intent(question, provider)


def parse_intent_response(raw: str | dict[str, Any]) -> IntentSuggestion | None:
    if isinstance(raw, dict):
        content = raw.get("message", {}).get("content") or raw.get("response") or raw
    else:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw

        if isinstance(parsed, dict):
            content = parsed.get("message", {}).get("content") or parsed.get("response") or parsed
        else:
            content = parsed

    if isinstance(content, str):
        content = _extract_json_object(content)
        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError:
            return None
    elif isinstance(content, dict):
        parsed_content = content
    else:
        return None

    intent = str(parsed_content.get("intent") or "").strip()
    approved_intents = set(TOOL_REGISTRY) | BUILTIN_ROUTER_INTENTS
    if intent not in approved_intents:
        return None

    confidence = _confidence_to_int(parsed_content.get("confidence"))
    if confidence < 60:
        return None

    arguments = parsed_content.get("arguments")
    if arguments is not None and not isinstance(arguments, dict):
        return None

    return IntentSuggestion(
        intent=intent,
        confidence=confidence,
        reason="Validated Local Ollama intent JSON against the approved tool registry.",
        arguments=arguments or {},
        needs_clarification=bool(parsed_content.get("needs_clarification")),
    )


def _ollama_payload(question: str, model: str) -> dict[str, Any]:
    approved_tools = [
        {
            "name": tool.name,
            "label": tool.label,
            "description": tool.description,
            "aliases": list(tool.aliases),
        }
        for tool in TOOL_REGISTRY.values()
    ]
    approved_intents = approved_tools + [
        {
            "name": "navigation",
            "label": "ERPNext Navigation",
            "description": "Open ERPNext lists, reports, dashboards, workspaces, pages, modules, or documents.",
            "aliases": ["open", "go to", "kholo", "report open karo"],
        },
        {
            "name": "dynamic_query",
            "label": "Safe Dynamic ERPNext Query",
            "description": "Answer bounded permission-aware list, count, sum, and group questions using DocType metadata.",
            "aliases": ["show", "list", "count", "total", "by customer", "by item", "dikhao", "batao"],
        },
        {
            "name": "knowledge",
            "label": "Knowledge Question",
            "description": "Answer from approved knowledge sources, SOPs, policies, and guides.",
            "aliases": ["policy", "manual", "knowledge", "SOP"],
        },
        {
            "name": "unknown",
            "label": "Unknown Or Needs Clarification",
            "description": "Use when the request is unclear or unsafe.",
            "aliases": ["unclear", "ambiguous"],
        },
    ]
    return {
        "model": model or "qwen3:8b",
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question": question,
                        "approved_intents": approved_intents,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "options": {
            "temperature": 0,
        },
    }


def _post_json(url: str, payload: dict[str, Any], timeout_seconds: int) -> str:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")
    except URLError as exc:
        raise RuntimeError("Local Ollama service is not reachable.") from exc


def _extract_json_object(content: str) -> str:
    text = content.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start : end + 1]

    return text


def _confidence_to_int(value: Any) -> int:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0

    if confidence <= 1:
        confidence *= 100

    return int(confidence)
