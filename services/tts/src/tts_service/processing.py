from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
from uuid import uuid4

from speech_lib import AudioSynthesisPayload, BaseEvent
from speech_lib.storage import ObjectStorage


@dataclass(frozen=True)
class TranslationRequest:
    correlation_id: str
    text: str
    speaker_reference_bytes: bytes | None
    speaker_id: str | None
    source_language: str
    target_language: str


def extract_translation_request(event: Dict[str, Any]) -> TranslationRequest:
    correlation_id = str(event.get("correlation_id", "")).strip()
    if not correlation_id:
        raise ValueError("missing correlation_id")

    payload = event.get("payload") or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        raise ValueError("missing payload.text")

    speaker_reference_bytes = payload.get("speaker_reference_bytes")
    speaker_id = payload.get("speaker_id")
    return TranslationRequest(
        correlation_id=correlation_id,
        text=text,
        speaker_reference_bytes=speaker_reference_bytes
        if isinstance(speaker_reference_bytes, (bytes, bytearray))
        else None,
        speaker_id=str(speaker_id).strip() if speaker_id else None,
        source_language=str(payload.get("source_language") or "").strip(),
        target_language=str(payload.get("target_language") or "").strip(),
    )


def enforce_text_limit(text: str, max_chars: int) -> None:
    if len(text) > max_chars:
        raise ValueError(f"Text exceeds {max_chars} char contract")


def select_audio_transport(
    *,
    audio_bytes: bytes,
    inline_limit_bytes: int,
    disable_storage: bool,
    storage: ObjectStorage | None,
    audio_uri_mode: str,
) -> tuple[bytes | None, str | None, str]:
    if len(audio_bytes) <= inline_limit_bytes:
        return audio_bytes, None, "inline"

    if disable_storage or storage is None:
        raise ValueError("audio_bytes exceeds inline limit and storage is disabled")

    key = f"{uuid4()}.wav"
    return_key = audio_uri_mode.lower() == "internal"
    audio_uri = storage.upload_bytes(
        key=key,
        data=audio_bytes,
        content_type="audio/wav",
        return_key=return_key,
    )
    return None, audio_uri, "uri"


def build_audio_payload(
    *,
    audio_bytes: bytes | None,
    audio_uri: str | None,
    duration_ms: int,
    sample_rate_hz: int,
    model_name: str | None,
    speaker_reference_bytes: bytes | None,
    speaker_id: str | None,
    text_snippet: str | None,
) -> AudioSynthesisPayload:
    payload = AudioSynthesisPayload(
        audio_bytes=audio_bytes,
        audio_uri=audio_uri,
        duration_ms=duration_ms,
        sample_rate_hz=sample_rate_hz,
        model_name=model_name,
        speaker_id=speaker_id,
        speaker_reference_bytes=speaker_reference_bytes,
        text_snippet=text_snippet,
    )
    payload.validate()
    return payload


def build_output_event(
    *,
    correlation_id: str,
    payload: AudioSynthesisPayload,
) -> BaseEvent:
    return BaseEvent(
        event_type="AudioSynthesisEvent",
        correlation_id=correlation_id,
        source_service="tts-service",
        payload={
            "audio_bytes": payload.audio_bytes,
            "audio_uri": payload.audio_uri,
            "duration_ms": payload.duration_ms,
            "sample_rate_hz": payload.sample_rate_hz,
            "audio_format": payload.audio_format,
            "content_type": payload.content_type,
            "model_name": payload.model_name,
            "speaker_id": payload.speaker_id,
            "speaker_reference_bytes": payload.speaker_reference_bytes,
            "text_snippet": payload.text_snippet,
        },
    )
