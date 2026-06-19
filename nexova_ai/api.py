import frappe

from nexova_ai.assistant.orchestrator import ask
from nexova_ai.assistant.settings import get_settings
from nexova_ai.assistant.voice import get_voice_strategy


@frappe.whitelist()
def ask_ai(question: str | None = None, source: str = "Desk Page"):
    """Public Desk endpoint for the assistant."""
    return ask(question=question, source=source)


@frappe.whitelist()
def get_client_config():
    """Return non-secret client flags for the Desk page."""
    settings = get_settings()
    voice = get_voice_strategy(
        settings.voice_provider,
        settings.stt_provider,
        settings.tts_provider,
        settings.language_mode,
    )

    return {
        "navigation_enabled": settings.navigation_enabled,
        "live_data_enabled": settings.live_data_enabled,
        "voice_enabled": settings.voice_enabled,
        "rag_enabled": settings.rag_enabled,
        "language_mode": settings.language_mode,
        "voice": {
            "voice_provider": voice.voice_provider,
            "stt_provider": voice.stt_provider,
            "tts_provider": voice.tts_provider,
            "recognition_language": voice.recognition_language,
            "supports_server_stt": voice.supports_server_stt,
            "raw_audio_retention": voice.raw_audio_retention,
        },
    }
