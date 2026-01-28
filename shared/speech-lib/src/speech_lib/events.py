from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any, Dict, Optional
from uuid import uuid4

from .constants import AUDIO_PAYLOAD_MAX_BYTES


@dataclass(frozen=True)
class AudioInputPayload:
    audio_bytes: Optional[bytes]
    audio_format: str
    sample_rate_hz: int
    audio_uri: Optional[str] = None
    language_hint: Optional[str] = None
    speaker_reference_bytes: Optional[bytes] = None
    speaker_id: Optional[str] = None

    def validate(self) -> None:
        has_bytes = isinstance(self.audio_bytes, (bytes, bytearray)) and bool(self.audio_bytes)
        has_uri = isinstance(self.audio_uri, str) and bool(self.audio_uri.strip())
        if has_bytes == has_uri:
            raise ValueError("exactly one of audio_bytes or audio_uri must be set")
        if has_bytes and len(self.audio_bytes or b"") > AUDIO_PAYLOAD_MAX_BYTES:
            raise ValueError(
                f"audio_bytes exceeds {AUDIO_PAYLOAD_MAX_BYTES} bytes (MVP limit)"
            )
        if self.audio_format != "wav":
            raise ValueError("audio_format must be 'wav' for MVP")
        if self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")


@dataclass(frozen=True)
class TextRecognizedPayload:
    text: str
    language: str
    confidence: float
    speaker_reference_bytes: Optional[bytes] = None
    speaker_id: Optional[str] = None


@dataclass(frozen=True)
class TextTranslatedPayload:
    text: str
    source_language: str
    target_language: str
    quality_score: Optional[float] = None
    speaker_reference_bytes: Optional[bytes] = None
    speaker_id: Optional[str] = None


@dataclass(frozen=True)
class SpeechSegmentPayload:
    segment_id: str
    segment_index: int
    start_ms: int
    end_ms: int
    audio_bytes: Optional[bytes]
    sample_rate_hz: int
    segment_uri: Optional[str] = None
    audio_format: str = "wav"
    speaker_reference_bytes: Optional[bytes] = None
    speaker_id: Optional[str] = None

    def validate(self) -> None:
        if not self.segment_id:
            raise ValueError("segment_id is required")
        if self.segment_index < 0:
            raise ValueError("segment_index must be non-negative")
        if self.start_ms < 0 or self.end_ms <= self.start_ms:
            raise ValueError("start_ms/end_ms are invalid")
        has_bytes = isinstance(self.audio_bytes, (bytes, bytearray)) and bool(self.audio_bytes)
        has_uri = isinstance(self.segment_uri, str) and bool(self.segment_uri.strip())
        if has_bytes == has_uri:
            raise ValueError("exactly one of audio_bytes or segment_uri must be set")
        if has_bytes and len(self.audio_bytes or b"") > AUDIO_PAYLOAD_MAX_BYTES:
            raise ValueError(
                f"audio_bytes exceeds {AUDIO_PAYLOAD_MAX_BYTES} bytes (MVP limit)"
            )
        if self.audio_format != "wav":
            raise ValueError("audio_format must be 'wav' for MVP")
        if self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")


@dataclass(frozen=True)
class AudioSynthesisPayload:
    audio_bytes: Optional[bytes]
    audio_uri: Optional[str]
    duration_ms: int
    sample_rate_hz: int
    audio_format: str = "wav"
    content_type: str = "audio/wav"
    model_name: Optional[str] = None
    speaker_id: Optional[str] = None
    speaker_reference_bytes: Optional[bytes] = None
    text_snippet: Optional[str] = None
    audio_sha256: Optional[str] = None
    audio_size_bytes: Optional[int] = None

    def validate(self) -> None:
        has_bytes = isinstance(self.audio_bytes, (bytes, bytearray)) and bool(self.audio_bytes)
        has_uri = isinstance(self.audio_uri, str) and bool(self.audio_uri.strip())
        if has_bytes == has_uri:
            raise ValueError("exactly one of audio_bytes or audio_uri must be set")
        if has_bytes and len(self.audio_bytes or b"") > AUDIO_PAYLOAD_MAX_BYTES:
            raise ValueError(
                f"audio_bytes exceeds {AUDIO_PAYLOAD_MAX_BYTES} bytes (MVP limit)"
            )
        if self.audio_format != "wav":
            raise ValueError("audio_format must be 'wav' for MVP")
        if self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")
        if self.duration_ms <= 0:
            raise ValueError("duration_ms must be positive")
        if self.audio_size_bytes is not None and self.audio_size_bytes <= 0:
            raise ValueError("audio_size_bytes must be positive when provided")


@dataclass(frozen=True)
class BaseEvent:
    event_type: str
    correlation_id: str
    source_service: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: int = field(default_factory=lambda: int(time() * 1000))

    def validate(self) -> None:
        missing = [
            name
            for name in ("event_type", "correlation_id", "source_service")
            if not getattr(self, name)
        ]
        if missing:
            raise ValueError(f"Missing required envelope fields: {', '.join(missing)}")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "source_service": self.source_service,
            "payload": self.payload,
        }
