from __future__ import annotations

from io import BytesIO
import math
import struct
import wave

from vad_service.processing import (
    build_segments,
    decode_wav,
    resample_audio,
    validate_audio_payload,
)


def _make_wav_bytes(
    sample_rate: int = 16000,
    seconds: float = 1.0,
    silence: bool = False,
) -> bytes:
    n_samples = int(sample_rate * seconds)
    frames = bytearray()
    amplitude = 0.0 if silence else 0.2
    for i in range(n_samples):
        t = i / sample_rate
        value = int(32767 * amplitude * math.sin(2 * math.pi * 440.0 * t))
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
    audio_bytes, sample_rate, audio_format = validate_audio_payload(payload)
    assert audio_bytes == b"\x00\x01"
    assert sample_rate == 16000
    assert audio_format == "wav"


def _make_composite_wav_bytes(sample_rate: int = 16000) -> bytes:
    silence_samples = int(sample_rate * 0.2)
    speech_samples = int(sample_rate * 0.3)
    frames = bytearray()
    for i in range(silence_samples + speech_samples):
        t = i / sample_rate
        amplitude = 0.0 if i < silence_samples else 0.2
        value = int(32767 * amplitude * math.sin(2 * math.pi * 440.0 * t))
        frames += struct.pack("<h", value)

    buffer = BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(frames)

    return buffer.getvalue()


def test_build_segments_detects_speech() -> None:
    wav_bytes = _make_composite_wav_bytes()

    audio, rate = decode_wav(wav_bytes, 16000)
    audio, rate = resample_audio(audio, rate, 16000)

    segments = build_segments(
        audio=audio,
        sample_rate_hz=rate,
        window_ms=30,
        hop_ms=10,
        speech_threshold=0.5,
        energy_threshold=0.01,
        min_speech_ms=50,
        min_silence_ms=100,
        padding_ms=0,
        speech_probabilities=None,
    )

    assert segments, "expected at least one speech segment"
    segment = segments[0]
    assert 0 <= segment.start_ms < segment.end_ms
    assert isinstance(segment.audio_bytes, (bytes, bytearray))


def test_build_segments_skips_silence_only() -> None:
    wav_bytes = _make_wav_bytes(seconds=0.3, silence=True)
    audio, rate = decode_wav(wav_bytes, 16000)
    audio, rate = resample_audio(audio, rate, 16000)

    segments = build_segments(
        audio=audio,
        sample_rate_hz=rate,
        window_ms=30,
        hop_ms=10,
        speech_threshold=0.5,
        energy_threshold=0.05,
        min_speech_ms=50,
        min_silence_ms=100,
        padding_ms=0,
        speech_probabilities=None,
    )

    assert segments == []
