from __future__ import annotations

from io import BytesIO
import math
import os
from pathlib import Path
import struct
import time
import wave

import pytest

from speech_lib import (
    BaseEvent,
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    TOPIC_ASR_TEXT,
    TOPIC_AUDIO_INGRESS,
    load_schema,
)


pytestmark = pytest.mark.integration


def _make_wav_bytes(sample_rate: int = 16000, seconds: float = 1.0) -> bytes:
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


def test_asr_pipeline_integration() -> None:
    if os.getenv("RUN_ASR_INTEGRATION") != "1":
        pytest.skip("Set RUN_ASR_INTEGRATION=1 to run integration test")

    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:29092")
    registry_url = os.getenv("SCHEMA_REGISTRY_URL", "http://127.0.0.1:8081")

    schema_dir = Path(os.getenv("SCHEMA_DIR", ""))
    if not str(schema_dir):
        schema_dir = Path(__file__).resolve().parents[3] / "shared" / "schemas" / "avro"

    input_schema = load_schema("AudioInputEvent.avsc", schema_dir=schema_dir)
    output_schema = load_schema("TextRecognizedEvent.avsc", schema_dir=schema_dir)

    registry = SchemaRegistryClient(registry_url)
    registry.register_schema(f"{TOPIC_AUDIO_INGRESS}-value", input_schema)
    registry.register_schema(f"{TOPIC_ASR_TEXT}-value", output_schema)

    producer = KafkaProducerWrapper.from_confluent(bootstrap)
    consumer = KafkaConsumerWrapper.from_confluent(
        bootstrap, group_id="asr-integration", topics=[TOPIC_ASR_TEXT]
    )

    payload = {
        "audio_bytes": _make_wav_bytes(seconds=1.0),
        "audio_format": "wav",
        "sample_rate_hz": 16000,
        "language_hint": None,
    }
    event = BaseEvent(
        event_type="AudioInputEvent",
        correlation_id="asr-integration-001",
        source_service="integration-test",
        payload=payload,
    )

    producer.publish_event(TOPIC_AUDIO_INGRESS, event, input_schema)

    deadline = time.time() + 30
    received = None
    while time.time() < deadline and received is None:
        received = consumer.poll(output_schema, timeout=1.0)

    assert received is not None
    assert received.get("correlation_id") == "asr-integration-001"
    assert received.get("payload", {}).get("text")
