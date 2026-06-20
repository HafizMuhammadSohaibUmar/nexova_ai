from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapability:
    name: str
    runs_locally: bool
    sends_client_data_to_cloud: bool
    supports_urdu: bool
    supports_english: bool
    recommended_for: str


STT_PROVIDERS: dict[str, ProviderCapability] = {
    "Browser": ProviderCapability(
        name="Browser",
        runs_locally=False,
        sends_client_data_to_cloud=True,
        supports_urdu=True,
        supports_english=True,
        recommended_for="Fast demo and low-cost cloud browser usage.",
    ),
    "Local Whisper": ProviderCapability(
        name="Local Whisper",
        runs_locally=True,
        sends_client_data_to_cloud=False,
        supports_urdu=True,
        supports_english=True,
        recommended_for="Privacy-first local Urdu and English speech recognition.",
    ),
    "Local Vosk": ProviderCapability(
        name="Local Vosk",
        runs_locally=True,
        sends_client_data_to_cloud=False,
        supports_urdu=False,
        supports_english=True,
        recommended_for="Very low-resource local English/Roman Urdu keyword capture.",
    ),
    "Cloud Deepgram": ProviderCapability(
        name="Cloud Deepgram",
        runs_locally=False,
        sends_client_data_to_cloud=True,
        supports_urdu=True,
        supports_english=True,
        recommended_for="Best cloud STT option when clients allow audio processing outside their site.",
    ),
}

LLM_PROVIDERS: dict[str, ProviderCapability] = {
    "Deterministic": ProviderCapability(
        name="Deterministic",
        runs_locally=True,
        sends_client_data_to_cloud=False,
        supports_urdu=True,
        supports_english=True,
        recommended_for="Lowest-cost approved command matching.",
    ),
    "Local Ollama": ProviderCapability(
        name="Local Ollama",
        runs_locally=True,
        sends_client_data_to_cloud=False,
        supports_urdu=True,
        supports_english=True,
        recommended_for="Offline intent understanding and clarification.",
    ),
    "Cloud Mistral": ProviderCapability(
        name="Cloud Mistral",
        runs_locally=False,
        sends_client_data_to_cloud=True,
        supports_urdu=True,
        supports_english=True,
        recommended_for="Cost-effective cloud intent routing and phrasing.",
    ),
    "Cloud OpenAI": ProviderCapability(
        name="Cloud OpenAI",
        runs_locally=False,
        sends_client_data_to_cloud=True,
        supports_urdu=True,
        supports_english=True,
        recommended_for="Highest quality cloud intent routing and language understanding.",
    ),
}


def provider_matrix() -> dict[str, list[dict[str, object]]]:
    return {
        "stt": [provider.__dict__ for provider in STT_PROVIDERS.values()],
        "llm": [provider.__dict__ for provider in LLM_PROVIDERS.values()],
    }
