from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Tuple
import logging

import librosa
import numpy as np
import soundfile as sf

from speech_lib.constants import AUDIO_PAYLOAD_MAX_BYTES
from speech_lib.storage import ObjectStorage

LOGGER = logging.getLogger(__name__)
TARGET_SAMPLE_RATE_HZ = 16000


def validate_audio_payload(
    payload: Dict[str, Any],
    storage: ObjectStorage | None,
) -> Tuple[bytes, int]:
    audio_bytes = payload.get("audio_bytes")
    audio_uri = payload.get("audio_uri") or payload.get("segment_uri")
    audio_format = payload.get("audio_format")
    sample_rate_hz = payload.get("sample_rate_hz")

    has_bytes = isinstance(audio_bytes, (bytes, bytearray)) and bool(audio_bytes)
    has_uri = isinstance(audio_uri, str) and bool(str(audio_uri).strip())
    if has_bytes == has_uri:
        raise ValueError("exactly one of audio_bytes or audio_uri/segment_uri must be set")
    if has_uri:
        if storage is None:
            raise ValueError("audio_uri provided but storage unavailable")
        audio_bytes = storage.download_bytes(uri=str(audio_uri))
    if not isinstance(audio_bytes, (bytes, bytearray)) or not audio_bytes:
        raise ValueError("audio_bytes missing or empty")

    if not has_uri and len(audio_bytes) > AUDIO_PAYLOAD_MAX_BYTES:
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
