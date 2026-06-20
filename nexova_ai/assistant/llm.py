from __future__ import annotations

from dataclasses import dataclass

from nexova_ai.assistant.intent import normalize_text
from nexova_ai.assistant.registry import TOOL_REGISTRY
from nexova_ai.assistant.vocabulary import fuzzy_match_score


@dataclass(frozen=True)
class IntentSuggestion:
    intent: str
    confidence: int
    reason: str


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
