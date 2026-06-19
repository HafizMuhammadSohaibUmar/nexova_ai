from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceProviderStrategy:
    voice_provider: str
    stt_provider: str
    tts_provider: str
    recognition_language: str
    supports_server_stt: bool
    raw_audio_retention: str = "Do not store raw audio by default"


def get_voice_strategy(
    voice_provider: str,
    stt_provider: str,
    tts_provider: str,
    language_mode: str = "English and Urdu",
) -> VoiceProviderStrategy:
    return VoiceProviderStrategy(
        voice_provider=voice_provider,
        stt_provider=stt_provider,
        tts_provider=tts_provider,
        recognition_language=_recognition_language(language_mode, stt_provider),
        supports_server_stt=stt_provider in {"Cloud", "Local"},
    )


def _recognition_language(language_mode: str, stt_provider: str) -> str:
    if stt_provider == "Disabled":
        return ""

    if language_mode == "Urdu":
        return "ur-PK"

    return "en-PK"
