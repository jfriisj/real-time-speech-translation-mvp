from __future__ import annotations

from io import BytesIO
import math
from pathlib import Path
import struct
import wave

from vad_service.main import process_event
from vad_service.config import Settings
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


class _RecordingProducer:
    def __init__(self) -> None:
        self.published: list[tuple[str, object, dict, str | None]] = []

    def publish_event(
        self,
        topic: str,
        event: object,
        schema: dict,
        key: str | None = None,
        schema_id: int | None = None,
    ) -> None:
        self.published.append((topic, event, schema, key))


def test_process_event_passes_speaker_context() -> None:
    wav_bytes = _make_composite_wav_bytes()
    settings = Settings(
        kafka_bootstrap_servers="localhost:9092",
        schema_registry_url="http://localhost:8081",
        consumer_group_id="vad-test",
        poll_timeout_seconds=0.1,
        schema_dir=Path("shared/schemas/avro"),
        target_sample_rate_hz=16000,
        window_ms=30,
        hop_ms=10,
        speech_threshold=0.5,
        energy_threshold=0.01,
        min_speech_ms=50,
        min_silence_ms=50,
        padding_ms=0,
        use_onnx=False,
        model_repo="",
        model_filename="",
    )
    producer = _RecordingProducer()

    process_event(
        event={
            "correlation_id": "corr-1",
            "payload": {
                "audio_bytes": wav_bytes,
                "audio_format": "wav",
                "sample_rate_hz": 16000,
                "speaker_reference_bytes": b"\x01",
                "speaker_id": "speaker-1",
            },
        },
        producer=producer,
        output_schema={},
        settings=settings,
        vad_model=None,
    )

    assert producer.published
    _topic, event, _schema, _key = producer.published[0]
    payload = event.to_dict()["payload"]
    assert payload["speaker_reference_bytes"] == b"\x01"
    assert payload["speaker_id"] == "speaker-1"
