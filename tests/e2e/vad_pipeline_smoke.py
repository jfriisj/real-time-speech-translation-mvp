from __future__ import annotations

import math
import struct
import time
import wave
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from speech_lib import (
    BaseEvent,
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    TOPIC_AUDIO_INGRESS,
    TOPIC_ASR_TEXT,
    TOPIC_SPEECH_SEGMENT,
    TOPIC_TRANSLATION_TEXT,
    load_schema,
)


def _make_wav_bytes(sample_rate: int = 16000) -> bytes:
    silence_seconds = 0.3
    speech_seconds = 0.3
    pattern = [
        (silence_seconds, 0.0),
        (speech_seconds, 0.2),
        (silence_seconds, 0.0),
        (speech_seconds, 0.2),
    ]

    frames = bytearray()
    for seconds, amplitude in pattern:
        n_samples = int(sample_rate * seconds)
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


def _resolve_schema_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "shared" / "schemas" / "avro"


def _register_schemas(registry: SchemaRegistryClient, schema_dir: Path) -> dict[str, dict]:
    schemas = {
        "audio": load_schema("AudioInputEvent.avsc", schema_dir=schema_dir),
        "segment": load_schema("SpeechSegmentEvent.avsc", schema_dir=schema_dir),
        "asr": load_schema("TextRecognizedEvent.avsc", schema_dir=schema_dir),
        "translation": load_schema("TextTranslatedEvent.avsc", schema_dir=schema_dir),
    }
    registry.register_schema(f"{TOPIC_AUDIO_INGRESS}-value", schemas["audio"])
    registry.register_schema(f"{TOPIC_SPEECH_SEGMENT}-value", schemas["segment"])
    registry.register_schema(f"{TOPIC_ASR_TEXT}-value", schemas["asr"])
    registry.register_schema(f"{TOPIC_TRANSLATION_TEXT}-value", schemas["translation"])
    return schemas


def _await_event(
    consumer: KafkaConsumerWrapper,
    schema: dict,
    correlation_id: str,
    timeout_seconds: float,
    topic_label: str,
) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        event = consumer.poll(schema, timeout=0.5)
        if event is None:
            continue
        if event.get("correlation_id") != correlation_id:
            continue
        return event
    raise TimeoutError(f"Timed out waiting for {topic_label} event")


def main() -> int:
    schema_dir = _resolve_schema_dir()
    registry = SchemaRegistryClient("http://127.0.0.1:8081")
    schemas = _register_schemas(registry, schema_dir)

    producer = KafkaProducerWrapper.from_confluent("127.0.0.1:29092")
    segment_consumer = KafkaConsumerWrapper.from_confluent(
        "127.0.0.1:29092",
        group_id=f"vad-segment-qa-{int(time.time())}",
        topics=[TOPIC_SPEECH_SEGMENT],
        config={"enable.auto.commit": False},
    )
    asr_consumer = KafkaConsumerWrapper.from_confluent(
        "127.0.0.1:29092",
        group_id=f"vad-asr-qa-{int(time.time())}",
        topics=[TOPIC_ASR_TEXT],
        config={"enable.auto.commit": False},
    )
    translation_consumer = KafkaConsumerWrapper.from_confluent(
        "127.0.0.1:29092",
        group_id=f"vad-translation-qa-{int(time.time())}",
        topics=[TOPIC_TRANSLATION_TEXT],
        config={"enable.auto.commit": False},
    )

    correlation_id = f"vad-smoke-{uuid4()}"
    wav_bytes = _make_wav_bytes()
    event = BaseEvent(
        event_type="AudioInputEvent",
        correlation_id=correlation_id,
        source_service="vad-smoke-test",
        payload={
            "audio_bytes": wav_bytes,
            "audio_format": "wav",
            "sample_rate_hz": 16000,
            "language_hint": None,
        },
    )

    producer.publish_event(TOPIC_AUDIO_INGRESS, event, schemas["audio"])

    segments = []
    deadline = time.time() + 45
    while time.time() < deadline and len(segments) < 2:
        polled = segment_consumer.poll(schemas["segment"], timeout=0.5)
        if polled is None:
            continue
        if polled.get("correlation_id") != correlation_id:
            continue
        segments.append(polled)

    if not segments:
        raise SystemExit("No SpeechSegmentEvent received")

    segment_indices = [seg.get("payload", {}).get("segment_index") for seg in segments]
    if segment_indices != sorted(segment_indices):
        raise SystemExit("Segment ordering violated")

    _await_event(asr_consumer, schemas["asr"], correlation_id, 120, "TextRecognizedEvent")
    _await_event(
        translation_consumer,
        schemas["translation"],
        correlation_id,
        180,
        "TextTranslatedEvent",
    )

    print("PASS: VAD -> ASR -> Translation pipeline produced outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
