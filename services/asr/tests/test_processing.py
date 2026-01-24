from __future__ import annotations

from io import BytesIO
import math
import struct
import wave

import numpy as np
import pytest

from asr_service.main import resolve_input_schema_name
from asr_service.processing import decode_wav, validate_audio_payload
from speech_lib import TOPIC_AUDIO_INGRESS, TOPIC_SPEECH_SEGMENT
from speech_lib.constants import AUDIO_PAYLOAD_MAX_BYTES


def _make_wav_bytes(sample_rate: int = 16000, seconds: float = 0.1) -> bytes:
    n_samples = int(sample_rate * seconds)
    frames = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        value = int(32767 * 0.2 * math.sin(2 * math.pi * 440.0 * t))
        frames += struct.pack("<h", value)

    buffer = BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(frames)

    return buffer.getvalue()


def test_validate_audio_payload_accepts_valid_payload() -> None:
    payload = {
        "audio_bytes": b"\x00\x01",
        "audio_format": "wav",
        "sample_rate_hz": 16000,
    }
    audio_bytes, sample_rate = validate_audio_payload(payload)
    assert audio_bytes == b"\x00\x01"
    assert sample_rate == 16000


def test_validate_audio_payload_rejects_empty() -> None:
    payload = {"audio_bytes": b"", "audio_format": "wav", "sample_rate_hz": 16000}
    with pytest.raises(ValueError):
        validate_audio_payload(payload)


def test_validate_audio_payload_rejects_format() -> None:
    payload = {"audio_bytes": b"\x00", "audio_format": "mp3", "sample_rate_hz": 16000}
    with pytest.raises(ValueError):
        validate_audio_payload(payload)


def test_validate_audio_payload_rejects_oversize() -> None:
    payload = {
        "audio_bytes": b"0" * (AUDIO_PAYLOAD_MAX_BYTES + 1),
        "audio_format": "wav",
        "sample_rate_hz": 16000,
    }
    with pytest.raises(ValueError):
        validate_audio_payload(payload)


def test_decode_wav_returns_float32_audio() -> None:
    wav_bytes = _make_wav_bytes(sample_rate=16000, seconds=0.1)
    audio, sample_rate = decode_wav(wav_bytes, 16000)
    assert isinstance(audio, np.ndarray)
    assert sample_rate == 16000
    assert audio.dtype == np.float32


def test_resolve_input_schema_name() -> None:
    assert resolve_input_schema_name(TOPIC_AUDIO_INGRESS) == "AudioInputEvent.avsc"
    assert resolve_input_schema_name(TOPIC_SPEECH_SEGMENT) == "SpeechSegmentEvent.avsc"

    with pytest.raises(ValueError):
        resolve_input_schema_name("speech.audio.unknown")
