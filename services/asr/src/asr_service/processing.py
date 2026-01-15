from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Tuple
import logging

import librosa
import numpy as np
import soundfile as sf

from speech_lib.constants import AUDIO_PAYLOAD_MAX_BYTES

LOGGER = logging.getLogger(__name__)
TARGET_SAMPLE_RATE_HZ = 16000


def validate_audio_payload(payload: Dict[str, Any]) -> Tuple[bytes, int]:
    audio_bytes = payload.get("audio_bytes")
    audio_format = payload.get("audio_format")
    sample_rate_hz = payload.get("sample_rate_hz")

    if not isinstance(audio_bytes, (bytes, bytearray)) or not audio_bytes:
        raise ValueError("audio_bytes missing or empty")

    if len(audio_bytes) > AUDIO_PAYLOAD_MAX_BYTES:
        raise ValueError(f"audio_bytes exceeds {AUDIO_PAYLOAD_MAX_BYTES} bytes (MVP limit)")

    if audio_format != "wav":
        raise ValueError(f"audio_format must be 'wav' for MVP (got {audio_format!r})")

    if not isinstance(sample_rate_hz, int) or sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz missing or invalid")

    return bytes(audio_bytes), sample_rate_hz


def decode_wav(audio_bytes: bytes, sample_rate_hz: int) -> Tuple[np.ndarray, int]:
    data, actual_rate = sf.read(BytesIO(audio_bytes), dtype="float32")
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    if actual_rate != sample_rate_hz:
        LOGGER.warning(
            "Sample rate metadata mismatch (payload=%s, wav=%s). Using wav rate.",
            sample_rate_hz,
            actual_rate,
        )

    effective_rate = actual_rate
    if effective_rate != TARGET_SAMPLE_RATE_HZ:
        data = librosa.resample(data, orig_sr=effective_rate, target_sr=TARGET_SAMPLE_RATE_HZ)
        effective_rate = TARGET_SAMPLE_RATE_HZ

    return data, effective_rate
