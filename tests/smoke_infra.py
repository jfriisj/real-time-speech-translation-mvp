"""Smoke test for Schema Registry + Kafka.

Requires confluent-kafka and a running docker-compose stack.
"""

from time import time, sleep

from speech_lib import (
    BaseEvent,
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    load_schema,
)

SCHEMA_REGISTRY_URL = "http://localhost:8081"
BOOTSTRAP_SERVERS = "127.0.0.1:29092"
TOPIC = "speech.asr.text"


def main() -> None:
    schema = load_schema("TextRecognizedEvent.avsc")
    registry = SchemaRegistryClient(SCHEMA_REGISTRY_URL)
    schema_id = registry.register_schema(f"{TOPIC}-value", schema)

    producer = KafkaProducerWrapper.from_confluent(BOOTSTRAP_SERVERS)
    consumer = KafkaConsumerWrapper.from_confluent(
        BOOTSTRAP_SERVERS,
        group_id="speech-smoke",
        topics=[TOPIC],
        schema_registry=registry,
    )

    event = BaseEvent(
        event_type="TextRecognizedEvent",
        correlation_id="smoke-001",
        source_service="smoke-test",
        payload={"text": "hello", "language": "en", "confidence": 0.99},
    )

    producer.publish_event(TOPIC, event, schema, schema_id=schema_id)

    received = None
    deadline = time() + 15
    while time() < deadline and received is None:
        received = consumer.poll(schema, timeout=1.0)
        if received is None:
            sleep(0.2)

    if not received:
        raise SystemExit("No event received from Kafka")

    print("Received event:", received)


if __name__ == "__main__":
    main()
