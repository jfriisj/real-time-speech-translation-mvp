from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from .audio import encode_wav


@dataclass(frozen=True)
class SynthesizedAudio:
    audio_bytes: bytes
    sample_rate_hz: int
    duration_ms: int
    model_name: str


class Synthesizer(Protocol):
    def synthesize(self, text: str, *, speaker_id: str | None, speed: float) -> SynthesizedAudio:
        ...


class MockSynthesizer:
    def __init__(self, *, sample_rate_hz: int, model_name: str) -> None:
        self.sample_rate_hz = sample_rate_hz
        self.model_name = model_name

    def synthesize(self, text: str, *, speaker_id: str | None, speed: float) -> SynthesizedAudio:
        duration_seconds = max(0.2, min(2.0, 0.02 * max(1, len(text))))
        length = int(self.sample_rate_hz * duration_seconds)
        audio = np.zeros(length, dtype=np.float32)
        audio_bytes = encode_wav(audio, self.sample_rate_hz)
        duration_ms = int(duration_seconds * 1000)
        return SynthesizedAudio(
            audio_bytes=audio_bytes,
            sample_rate_hz=self.sample_rate_hz,
            duration_ms=duration_ms,
            model_name=self.model_name,
        )
