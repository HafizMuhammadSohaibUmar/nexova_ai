from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceProviderStrategy:
    voice_provider: str
    stt_provider: str
    tts_provider: str
    raw_audio_retention: str = "Do not store raw audio by default"


def get_voice_strategy(voice_provider: str, stt_provider: str, tts_provider: str) -> VoiceProviderStrategy:
    return VoiceProviderStrategy(
        voice_provider=voice_provider,
        stt_provider=stt_provider,
        tts_provider=tts_provider,
    )
