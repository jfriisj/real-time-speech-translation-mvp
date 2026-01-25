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
    TOPIC_SPEECH_SEGMENT,
    load_schema,
)

from .config import Settings
from .processing import decode_wav, validate_audio_payload
from .transcriber import Transcriber


LOGGER = logging.getLogger(__name__)


def register_schemas(
    registry: SchemaRegistryClient,
    input_schema: Dict[str, Any],
    output_schema: Dict[str, Any],
    input_topic: str,
) -> None:
    registry.register_schema(f"{input_topic}-value", input_schema)
    registry.register_schema(f"{TOPIC_ASR_TEXT}-value", output_schema)


def resolve_input_schema_name(input_topic: str) -> str:
    if input_topic == TOPIC_AUDIO_INGRESS:
        return "AudioInputEvent.avsc"
    if input_topic == TOPIC_SPEECH_SEGMENT:
        return "SpeechSegmentEvent.avsc"
    raise ValueError(f"Unsupported ASR input topic: {input_topic}")


def build_output_event(
    result: Dict[str, Any],
    correlation_id: str,
    speaker_reference_bytes: bytes | None,
    speaker_id: str | None,
) -> BaseEvent:
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
            "speaker_reference_bytes": speaker_reference_bytes,
            "speaker_id": speaker_id,
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
    speaker_reference_bytes = payload.get("speaker_reference_bytes")
    speaker_id = payload.get("speaker_id")

    audio_bytes, sample_rate_hz = validate_audio_payload(payload)
    audio, effective_rate = decode_wav(audio_bytes, sample_rate_hz)

    result = transcriber.transcribe(audio, effective_rate)
    output_event = build_output_event(
        result,
        correlation_id,
        speaker_reference_bytes
        if isinstance(speaker_reference_bytes, (bytes, bytearray))
        else None,
        str(speaker_id).strip() if speaker_id else None,
    )
    if not output_event.payload["text"]:
        raise ValueError("transcription result is empty")

    producer.publish_event(TOPIC_ASR_TEXT, output_event, output_schema)
    segment_index = payload.get("segment_index")
    if segment_index is not None:
        LOGGER.info(
            "Published TextRecognizedEvent correlation_id=%s segment_index=%s",
            correlation_id,
            segment_index,
        )
    else:
        LOGGER.info("Published TextRecognizedEvent correlation_id=%s", correlation_id)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    settings = Settings.from_env()

    input_schema_name = resolve_input_schema_name(settings.input_topic)
    input_schema = load_schema(input_schema_name, schema_dir=settings.schema_dir)
    output_schema = load_schema("TextRecognizedEvent.avsc", schema_dir=settings.schema_dir)

    registry = SchemaRegistryClient(settings.schema_registry_url)
    register_schemas(registry, input_schema, output_schema, settings.input_topic)

    consumer = KafkaConsumerWrapper.from_confluent(
        settings.kafka_bootstrap_servers,
        group_id=settings.consumer_group_id,
        topics=[settings.input_topic],
    )
    producer = KafkaProducerWrapper.from_confluent(settings.kafka_bootstrap_servers)
    transcriber = Transcriber(settings.model_name)

    LOGGER.info("ASR service started; consuming from %s", settings.input_topic)

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
