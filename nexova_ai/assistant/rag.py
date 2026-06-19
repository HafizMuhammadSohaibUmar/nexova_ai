from __future__ import annotations

from nexova_ai.assistant.contracts import response
from nexova_ai.assistant.settings import AssistantSettings


def answer_knowledge_question(question: str, settings: AssistantSettings):
    if not settings.rag_enabled:
        return response(
            "Knowledge search is not enabled for this site yet.",
            status="Blocked",
            intent="knowledge",
            data={"type": "knowledge", "enabled": False},
        )

    return response(
        "Knowledge search is configured, but no retrieval provider is active yet.",
        status="Blocked",
        intent="knowledge",
        data={"type": "knowledge", "enabled": True, "provider_ready": False},
    )
