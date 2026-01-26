from __future__ import annotations

from typing import cast

from speech_lib import BaseEvent
from tts_service.main import build_output_event, process_event  # type: ignore[import-not-found]


class _Synthesizer:
    def __init__(self, audio_bytes: bytes, sample_rate_hz: int, duration_ms: int) -> None:
        self._audio_bytes = audio_bytes
        self._sample_rate_hz = sample_rate_hz
        self._duration_ms = duration_ms
        self.calls: list[tuple[str, bytes | None]] = []

    def synthesize(self, text: str, speaker_reference_bytes: bytes | None, speaker_id: str | None = None):
        self.calls.append((text, speaker_reference_bytes))
        _ = speaker_id
        return self._audio_bytes, self._sample_rate_hz, self._duration_ms


class _RecordingProducer:
    def __init__(self) -> None:
        self.published: list[tuple[str, object, dict, str | None]] = []

    def publish_event(self, topic: str, event: object, schema: dict, key: str | None = None) -> None:
        self.published.append((topic, event, schema, key))


class _Storage:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, bytes, str]] = []

    def upload_bytes(self, *, key: str, data: bytes, content_type: str) -> str:
        self.uploads.append((key, data, content_type))
        return f"http://minio/tts-audio/{key}"


def test_build_output_event_sets_payload() -> None:
    event = build_output_event(
        correlation_id="corr-1",
        audio_bytes=b"\x00\x01",
        audio_uri=None,
        duration_ms=500,
        sample_rate_hz=16000,
        speaker_id="speaker-1",
        model_name="kokoro-82m-onnx",
    )
    payload = event.to_dict()["payload"]
    assert payload["audio_bytes"] == b"\x00\x01"
    assert payload["audio_uri"] is None
    assert payload["duration_ms"] == 500
    assert payload["sample_rate_hz"] == 16000
    assert payload["audio_format"] == "wav"
    assert payload["content_type"] == "audio/wav"
    assert payload["speaker_id"] == "speaker-1"
    assert payload["model_name"] == "kokoro-82m-onnx"


def test_process_event_emits_inline_audio() -> None:
    audio_bytes = b"\x00\x01"
    synthesizer = _Synthesizer(audio_bytes, 16000, 100)
    producer = _RecordingProducer()
    storage = _Storage()

    process_event(
        event={
            "correlation_id": "corr-2",
            "payload": {"text": "hello", "speaker_id": "speaker-2"},
        },
        synthesizer=synthesizer,
        storage=storage,
        producer=producer,
        output_schema={},
        inline_max_bytes=1024 * 1024,
        model_name="kokoro-82m-onnx",
    )

    assert producer.published
    _topic, event, _schema, key = producer.published[0]
    payload = cast(BaseEvent, event).to_dict()["payload"]
    assert key == "corr-2"
    assert payload["audio_bytes"] is not None
    assert payload["audio_uri"] is None
    assert payload["speaker_id"] == "speaker-2"
    assert payload["model_name"] == "kokoro-82m-onnx"


def test_process_event_emits_uri_when_too_large() -> None:
    audio_bytes = b"\x00\x01"
    synthesizer = _Synthesizer(audio_bytes, 16000, 100)
    producer = _RecordingProducer()
    storage = _Storage()

    process_event(
        event={
            "correlation_id": "corr-3",
            "payload": {"text": "hello"},
        },
        synthesizer=synthesizer,
        storage=storage,
        producer=producer,
        output_schema={},
        inline_max_bytes=1,
        model_name=None,
    )

    _topic, event, _schema, _key = producer.published[0]
    payload = cast(BaseEvent, event).to_dict()["payload"]
    assert payload["audio_bytes"] is None
    assert payload["audio_uri"].startswith("http://minio/")
