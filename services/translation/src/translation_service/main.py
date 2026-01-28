from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict

import requests

from speech_lib import (
    BaseEvent,
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    TOPIC_ASR_TEXT,
    TOPIC_TRANSLATION_TEXT,
    load_schema,
)

from .config import Settings
from .translator import HuggingFaceTranslator, Translator


LOGGER = logging.getLogger(__name__)


def wait_for_schema_registry(
    registry_url: str,
    timeout_seconds: float,
    *,
    initial_backoff_seconds: float = 1.0,
    max_backoff_seconds: float = 8.0,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    attempt = 0
    while True:
        attempt += 1
        try:
            response = requests.get(
                f"{registry_url.rstrip('/')}/subjects",
                timeout=5,
            )
            response.raise_for_status()
            LOGGER.info("Schema Registry ready at %s", registry_url)
            return
        except Exception as exc:
            if time.monotonic() >= deadline:
                LOGGER.error(
                    "Schema Registry not ready after %.0fs at %s",
                    timeout_seconds,
                    registry_url,
                )
                raise SystemExit(1) from exc
            sleep_seconds = min(
                initial_backoff_seconds * (2 ** (attempt - 1)),
                max_backoff_seconds,
            )
            LOGGER.info(
                "Waiting for Schema Registry at %s (retry in %.1fs)",
                registry_url,
                sleep_seconds,
            )
            time.sleep(sleep_seconds)


def extract_translation_request(
    *,
    event: Dict[str, Any],
    target_language: str,
) -> tuple[str, str, str, str, bytes | None, str | None]:
    correlation_id = str(event.get("correlation_id", "")).strip()
    if not correlation_id:
        raise ValueError("missing correlation_id")

    payload = event.get("payload") or {}
    input_text = str(payload.get("text", "")).strip()
    if not input_text:
        raise ValueError("missing payload.text")

    source_language = str(payload.get("language") or "").strip() or "en"
    effective_target = target_language.strip() or "es"
    speaker_reference_bytes = payload.get("speaker_reference_bytes")
    speaker_id = payload.get("speaker_id")
    return (
        correlation_id,
        input_text,
        source_language,
        effective_target,
        speaker_reference_bytes if isinstance(speaker_reference_bytes, (bytes, bytearray)) else None,
        str(speaker_id).strip() if speaker_id else None,
    )


def register_schemas(
    registry: SchemaRegistryClient,
    input_schema: Dict[str, Any],
    output_schema: Dict[str, Any],
) -> tuple[int, int]:
    input_schema_id = registry.register_schema(
        f"{TOPIC_ASR_TEXT}-value", input_schema
    )
    output_schema_id = registry.register_schema(
        f"{TOPIC_TRANSLATION_TEXT}-value", output_schema
    )
    return input_schema_id, output_schema_id


def build_output_event(
    *,
    correlation_id: str,
    translated_text: str,
    source_language: str,
    target_language: str,
    speaker_reference_bytes: bytes | None,
    speaker_id: str | None,
) -> BaseEvent:
    return BaseEvent(
        event_type="TextTranslatedEvent",
        correlation_id=correlation_id,
        source_service="translation-service",
        payload={
            "text": translated_text,
            "source_language": source_language,
            "target_language": target_language,
            "quality_score": None,
            "speaker_reference_bytes": speaker_reference_bytes,
            "speaker_id": speaker_id,
        },
    )


def process_event(
    *,
    event: Dict[str, Any],
    translator: Translator,
    producer: KafkaProducerWrapper,
    output_schema: Dict[str, Any],
    output_schema_id: int,
    target_language: str,
) -> None:
    (
        correlation_id,
        input_text,
        source_language,
        effective_target,
        speaker_reference_bytes,
        speaker_id,
    ) = extract_translation_request(
        event=event,
        target_language=target_language,
    )
    translated_text = translator.translate(input_text, source_language, effective_target)
    if not translated_text:
        raise ValueError("translation result is empty")

    output_event = build_output_event(
        correlation_id=correlation_id,
        translated_text=translated_text,
        source_language=source_language,
        target_language=effective_target,
        speaker_reference_bytes=speaker_reference_bytes,
        speaker_id=speaker_id,
    )

    producer.publish_event(
        TOPIC_TRANSLATION_TEXT,
        output_event,
        output_schema,
        schema_id=output_schema_id,
    )
    LOGGER.info("Published TextTranslatedEvent correlation_id=%s", correlation_id)


def _resolve_schema_dir(schema_dir: Path) -> Path:
    if schema_dir.exists():
        return schema_dir
    # Useful when running inside service folder locally
    candidate = Path(__file__).resolve().parents[4] / "shared" / "schemas" / "avro"
    return candidate


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = Settings.from_env()
    schema_dir = _resolve_schema_dir(settings.schema_dir)

    wait_for_schema_registry(
        settings.schema_registry_url,
        settings.schema_registry_wait_timeout_seconds,
    )

    input_schema = load_schema("TextRecognizedEvent.avsc", schema_dir=schema_dir)
    output_schema = load_schema("TextTranslatedEvent.avsc", schema_dir=schema_dir)

    registry = SchemaRegistryClient(settings.schema_registry_url)
    _input_schema_id, output_schema_id = register_schemas(
        registry, input_schema, output_schema
    )

    consumer = KafkaConsumerWrapper.from_confluent(
        settings.kafka_bootstrap_servers,
        group_id=settings.consumer_group_id,
        topics=[TOPIC_ASR_TEXT],
        config={"enable.auto.commit": False},
        schema_registry=registry,
    )
    producer = KafkaProducerWrapper.from_confluent(settings.kafka_bootstrap_servers)

    translator: Translator = HuggingFaceTranslator(
        model_name=settings.model_name,
        max_new_tokens=settings.max_new_tokens,
    )

    LOGGER.info(
        "Translation service started; consuming from %s target_language=%s model=%s",
        TOPIC_ASR_TEXT,
        settings.target_language,
        settings.model_name,
    )

    try:
        while True:
            polled = consumer.poll_with_message(
                input_schema, timeout=settings.poll_timeout_seconds
            )
            if polled is None:
                continue

            event, message = polled
            try:
                process_event(
                    event=event,
                    translator=translator,
                    producer=producer,
                    output_schema=output_schema,
                    output_schema_id=output_schema_id,
                    target_language=settings.target_language,
                )
            except ValueError as exc:
                LOGGER.warning("Dropping event: %s", exc)
            except Exception:  # pragma: no cover - safety net for runtime errors
                LOGGER.exception("Unexpected error while processing event")
            finally:
                consumer.commit_message(message)
    except KeyboardInterrupt:
        LOGGER.info("Translation service shutting down")


if __name__ == "__main__":
    main()
