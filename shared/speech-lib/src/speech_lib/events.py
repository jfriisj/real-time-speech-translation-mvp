from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any, Dict, Optional
from uuid import uuid4

from .constants import AUDIO_PAYLOAD_MAX_BYTES


@dataclass(frozen=True)
class AudioInputPayload:
    audio_bytes: bytes
    audio_format: str
    sample_rate_hz: int
    language_hint: Optional[str] = None

    def validate(self) -> None:
        if len(self.audio_bytes) > AUDIO_PAYLOAD_MAX_BYTES:
            raise ValueError(
                f"audio_bytes exceeds {AUDIO_PAYLOAD_MAX_BYTES} bytes (MVP limit)"
            )


@dataclass(frozen=True)
class TextRecognizedPayload:
    text: str
    language: str
    confidence: float


@dataclass(frozen=True)
class TextTranslatedPayload:
    text: str
    source_language: str
    target_language: str
    quality_score: Optional[float] = None


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
