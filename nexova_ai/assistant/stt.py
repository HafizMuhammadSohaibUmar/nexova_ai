from __future__ import annotations

import json
import mimetypes
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


MAX_AUDIO_BYTES = 10 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class TranscriptionResult:
    transcript: str
    provider: str
    language: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "transcript": self.transcript,
            "provider": self.provider,
            "language": self.language,
        }


def transcribe_audio_bytes(
    *,
    audio: bytes,
    filename: str,
    content_type: str | None,
    stt_provider: str,
    endpoint: str,
    language: str | None = None,
) -> TranscriptionResult:
    if not audio:
        raise ValueError("No audio was provided.")

    if len(audio) > MAX_AUDIO_BYTES:
        raise ValueError("Audio is too large. Please keep voice commands short.")

    if stt_provider != "Local Whisper":
        raise ValueError("Server-side transcription is only enabled for Local Whisper right now.")

    transcript = _call_whisper_cpp(
        endpoint=endpoint,
        audio=audio,
        filename=filename,
        content_type=content_type,
        language=language,
    )
    return TranscriptionResult(
        transcript=transcript,
        provider=stt_provider,
        language=language,
    )


def _call_whisper_cpp(
    *,
    endpoint: str,
    audio: bytes,
    filename: str,
    content_type: str | None,
    language: str | None,
) -> str:
    url = endpoint.rstrip("/") + "/inference"
    boundary = "----InvoxiaAI" + uuid.uuid4().hex
    body = _multipart_body(
        boundary=boundary,
        fields={
            "response_format": "json",
            "temperature": "0",
            **({"language": language.split("-")[0]} if language else {}),
        },
        files={
            "file": {
                "filename": filename or "voice.webm",
                "content_type": content_type or _guess_content_type(filename),
                "content": audio,
            }
        },
    )

    request = Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except URLError as exc:
        raise RuntimeError("Local Whisper service is not reachable.") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return raw.strip()

    transcript = (
        parsed.get("text")
        or parsed.get("transcript")
        or parsed.get("result")
        or ""
    )
    return str(transcript).strip()


def _multipart_body(
    *,
    boundary: str,
    fields: dict[str, str],
    files: dict[str, dict[str, Any]],
) -> bytes:
    chunks: list[bytes] = []

    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                str(value).encode(),
                b"\r\n",
            ]
        )

    for name, file_data in files.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{file_data["filename"]}"\r\n'
                ).encode(),
                f'Content-Type: {file_data["content_type"]}\r\n\r\n'.encode(),
                file_data["content"],
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks)


def _guess_content_type(filename: str) -> str:
    guessed, _ = mimetypes.guess_type(filename or "")
    return guessed or "audio/webm"
