from __future__ import annotations

import logging
from typing import Any, Dict

from speech_lib import (
    BaseEvent,
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    TOPIC_ASR_TEXT,
    TOPIC_AUDIO_INGRESS,
    load_schema,
)

from .config import Settings
from .processing import decode_wav, validate_audio_payload
from .transcriber import Transcriber


LOGGER = logging.getLogger(__name__)


def register_schemas(registry: SchemaRegistryClient, input_schema: Dict[str, Any], output_schema: Dict[str, Any]) -> None:
    registry.register_schema(f"{TOPIC_AUDIO_INGRESS}-value", input_schema)
    registry.register_schema(f"{TOPIC_ASR_TEXT}-value", output_schema)


def build_output_event(result: Dict[str, Any], correlation_id: str) -> BaseEvent:
    text = str(result.get("text", "")).strip()
    language = result.get("language") or "en"
    confidence = result.get("confidence", 1.0)
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        confidence_value = 1.0

    return BaseEvent(
        event_type="TextRecognizedEvent",
        correlation_id=correlation_id,
        source_service="asr-service",
        payload={
            "text": text,
            "language": language,
            "confidence": confidence_value,
        },
    )


def process_event(
    event: Dict[str, Any],
    transcriber: Transcriber,
    producer: KafkaProducerWrapper,
    output_schema: Dict[str, Any],
) -> None:
    correlation_id = str(event.get("correlation_id", ""))
    payload = event.get("payload") or {}

    audio_bytes, sample_rate_hz = validate_audio_payload(payload)
    audio, effective_rate = decode_wav(audio_bytes, sample_rate_hz)

    result = transcriber.transcribe(audio, effective_rate)
    output_event = build_output_event(result, correlation_id)
    if not output_event.payload["text"]:
        raise ValueError("transcription result is empty")

    producer.publish_event(TOPIC_ASR_TEXT, output_event, output_schema)
    LOGGER.info("Published TextRecognizedEvent correlation_id=%s", correlation_id)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    settings = Settings.from_env()

    input_schema = load_schema("AudioInputEvent.avsc", schema_dir=settings.schema_dir)
    output_schema = load_schema("TextRecognizedEvent.avsc", schema_dir=settings.schema_dir)

    registry = SchemaRegistryClient(settings.schema_registry_url)
    register_schemas(registry, input_schema, output_schema)

    consumer = KafkaConsumerWrapper.from_confluent(
        settings.kafka_bootstrap_servers,
        group_id=settings.consumer_group_id,
        topics=[TOPIC_AUDIO_INGRESS],
    )
    producer = KafkaProducerWrapper.from_confluent(settings.kafka_bootstrap_servers)
    transcriber = Transcriber(settings.model_name)

    LOGGER.info("ASR service started; consuming from %s", TOPIC_AUDIO_INGRESS)

    try:
        while True:
            event = consumer.poll(input_schema, timeout=settings.poll_timeout_seconds)
            if event is None:
                continue
            try:
                process_event(event, transcriber, producer, output_schema)
            except ValueError as exc:
                LOGGER.warning("Dropping event: %s", exc)
            except Exception:  # pragma: no cover - safety net for runtime errors
                LOGGER.exception("Unexpected error while processing event")
    except KeyboardInterrupt:
        LOGGER.info("ASR service shutting down")


if __name__ == "__main__":
    main()
