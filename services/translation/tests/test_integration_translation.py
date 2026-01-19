from __future__ import annotations

import os
from pathlib import Path
import time

import pytest

from speech_lib import (
    BaseEvent,
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    TOPIC_ASR_TEXT,
    TOPIC_TRANSLATION_TEXT,
    load_schema,
)


pytestmark = pytest.mark.integration


def test_translation_pipeline_integration() -> None:
    if os.getenv("RUN_TRANSLATION_INTEGRATION") != "1":
        pytest.skip("Set RUN_TRANSLATION_INTEGRATION=1 to run integration test")

    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:29092")
    registry_url = os.getenv("SCHEMA_REGISTRY_URL", "http://127.0.0.1:8081")

    schema_dir_env = os.getenv("SCHEMA_DIR")
    if schema_dir_env:
        schema_dir = Path(schema_dir_env)
    else:
        schema_dir = Path(__file__).resolve().parents[3] / "shared" / "schemas" / "avro"

    input_schema = load_schema("TextRecognizedEvent.avsc", schema_dir=schema_dir)
    output_schema = load_schema("TextTranslatedEvent.avsc", schema_dir=schema_dir)

    registry = SchemaRegistryClient(registry_url)
    registry.register_schema(f"{TOPIC_ASR_TEXT}-value", input_schema)
    registry.register_schema(f"{TOPIC_TRANSLATION_TEXT}-value", output_schema)

    producer = KafkaProducerWrapper.from_confluent(bootstrap)
    consumer = KafkaConsumerWrapper.from_confluent(
        bootstrap, group_id="translation-integration", topics=[TOPIC_TRANSLATION_TEXT]
    )

    event = BaseEvent(
        event_type="TextRecognizedEvent",
        correlation_id="translation-integration-001",
        source_service="integration-test",
        payload={"text": "hello", "language": "en", "confidence": 0.99},
    )

    producer.publish_event(TOPIC_ASR_TEXT, event, input_schema)

    deadline = time.time() + 180
    received = None
    while time.time() < deadline and received is None:
        received = consumer.poll(output_schema, timeout=1.0)

    assert received is not None
    assert received.get("correlation_id") == "translation-integration-001"
    assert received.get("payload", {}).get("text")
    assert received.get("payload", {}).get("source_language")
    assert received.get("payload", {}).get("target_language")
