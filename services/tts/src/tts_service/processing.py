from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Dict

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
    correlation_id: str,
) -> tuple[bytes | None, str | None, str]:
    force_uri = os.getenv("FORCE_AUDIO_URI", "0") == "1"
    if not force_uri and len(audio_bytes) <= inline_limit_bytes:
        return audio_bytes, None, "inline"

    if disable_storage or storage is None:
        raise ValueError("Payload too large for inline and storage disabled")

    key = f"tts/{correlation_id}.wav"
    return_key = audio_uri_mode.lower() == "internal"
    try:
        audio_uri = storage.upload_bytes(
            key=key,
            data=audio_bytes,
            content_type="audio/wav",
            return_key=return_key,
        )
    except Exception as exc:  # pragma: no cover - storage failure guard
        raise ValueError("Payload too large for inline and storage disabled") from exc

    if return_key:
        if audio_uri.startswith("s3://"):
            bucket_key = audio_uri.replace("s3://", "", 1)
            _bucket, resolved_key = bucket_key.split("/", 1)
            return None, resolved_key, "uri"
        return None, audio_uri, "uri"

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


def compute_rtf(duration_ms: int, latency_ms: float) -> float | None:
    if latency_ms <= 0:
        return None
    return (duration_ms / 1000.0) / (latency_ms / 1000.0)
