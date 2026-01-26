from __future__ import annotations

import logging
from pathlib import Path
from time import perf_counter
from typing import Any, Dict
from uuid import uuid4

from prometheus_client import Counter, Histogram, start_http_server  # type: ignore[import-not-found]

from speech_lib import (
    AUDIO_PAYLOAD_MAX_BYTES,
    BaseEvent,
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    TOPIC_TRANSLATION_TEXT,
    TOPIC_TTS_OUTPUT,
    load_schema,
)

from .config import Settings
from .storage import ObjectStorage
from .synthesizer_factory import SynthesizerFactory
from .synthesizer_interface import Synthesizer


LOGGER = logging.getLogger(__name__)

TTS_LATENCY_SECONDS = Histogram(
    "tts_latency_seconds",
    "TTS synthesis latency in seconds",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
)
TTS_ERRORS_TOTAL = Counter(
    "tts_errors_total",
    "TTS errors",
    labelnames=("error_type",),
)


def _resolve_schema_dir(schema_dir: Path) -> Path:
    if schema_dir.exists():
        return schema_dir
    candidate = Path(__file__).resolve().parents[4] / "shared" / "schemas" / "avro"
    return candidate


def register_schemas(
    registry: SchemaRegistryClient,
    input_schema: Dict[str, Any],
    output_schema: Dict[str, Any],
) -> None:
    registry.register_schema(f"{TOPIC_TRANSLATION_TEXT}-value", input_schema)
    registry.register_schema(f"{TOPIC_TTS_OUTPUT}-value", output_schema)


def build_output_event(
    *,
    correlation_id: str,
    audio_bytes: bytes | None,
    audio_uri: str | None,
    duration_ms: int,
    sample_rate_hz: int,
    speaker_id: str | None,
    model_name: str | None,
) -> BaseEvent:
    return BaseEvent(
        event_type="AudioSynthesisEvent",
        correlation_id=correlation_id,
        source_service="tts-service",
        payload={
            "audio_bytes": audio_bytes,
            "audio_uri": audio_uri,
            "duration_ms": duration_ms,
            "sample_rate_hz": sample_rate_hz,
            "audio_format": "wav",
            "content_type": "audio/wav",
            "speaker_id": speaker_id,
            "model_name": model_name,
        },
    )


def _extract_request(event: Dict[str, Any]) -> tuple[str, str, bytes | None, str | None]:
    correlation_id = str(event.get("correlation_id", "")).strip()
    if not correlation_id:
        raise ValueError("missing correlation_id")

    payload = event.get("payload") or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        raise ValueError("missing payload.text")

    speaker_reference_bytes = payload.get("speaker_reference_bytes")
    speaker_id = payload.get("speaker_id")

    return (
        correlation_id,
        text,
        speaker_reference_bytes
        if isinstance(speaker_reference_bytes, (bytes, bytearray))
        else None,
        str(speaker_id).strip() if speaker_id else None,
    )


def process_event(
    *,
    event: Dict[str, Any],
    synthesizer: Synthesizer,
    storage: ObjectStorage,
    producer: KafkaProducerWrapper,
    output_schema: Dict[str, Any],
    inline_max_bytes: int,
    model_name: str | None,
) -> None:
    correlation_id, text, speaker_reference_bytes, speaker_id = _extract_request(event)

    start_time = perf_counter()
    # Updated signature: synthesize(text, ref_bytes, speaker_id) -> (bytes, sample_rate, duration)
    wav_bytes, sample_rate_hz, duration_ms = synthesizer.synthesize(text, speaker_reference_bytes, speaker_id)
    synthesis_seconds = perf_counter() - start_time
    TTS_LATENCY_SECONDS.observe(synthesis_seconds)

    payload_mode = "INLINE"
    audio_bytes: bytes | None = None
    audio_uri: str | None = None
    payload_size_bytes = len(wav_bytes)

    if payload_size_bytes <= min(inline_max_bytes, AUDIO_PAYLOAD_MAX_BYTES):
        audio_bytes = wav_bytes
    else:
        payload_mode = "URI"
        key = f"{correlation_id}/{uuid4()}.wav"
        try:
            audio_uri = storage.upload_bytes(
                key=key,
                data=wav_bytes,
                content_type="audio/wav",
            )
        except Exception as exc:
            TTS_ERRORS_TOTAL.labels("object_store_upload").inc()
            LOGGER.error(
                "Object store upload failed correlation_id=%s error=%s",
                correlation_id,
                exc,
            )
            return

    output_event = build_output_event(
        correlation_id=correlation_id,
        audio_bytes=audio_bytes,
        audio_uri=audio_uri,
        duration_ms=duration_ms,
        sample_rate_hz=sample_rate_hz,
        speaker_id=speaker_id,
        model_name=model_name,
    )

    producer.publish_event(
        TOPIC_TTS_OUTPUT,
        output_event,
        output_schema,
        key=correlation_id,
    )

    LOGGER.info(
        "Published AudioSynthesisEvent correlation_id=%s input_char_count=%s "
        "synthesis_latency_ms=%s payload_mode=%s payload_size_bytes=%s",
        correlation_id,
        len(text),
        int(synthesis_seconds * 1000),
        payload_mode,
        payload_size_bytes,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = Settings.from_env()
    schema_dir = _resolve_schema_dir(settings.schema_dir)

    input_schema = load_schema("TextTranslatedEvent.avsc", schema_dir=schema_dir)
    output_schema = load_schema("AudioSynthesisEvent.avsc", schema_dir=schema_dir)

    registry = SchemaRegistryClient(settings.schema_registry_url)
    register_schemas(registry, input_schema, output_schema)

    if settings.metrics_port > 0:
        start_http_server(settings.metrics_port)
        LOGGER.info("Metrics server started port=%s", settings.metrics_port)

    consumer = KafkaConsumerWrapper.from_confluent(
        settings.kafka_bootstrap_servers,
        group_id=settings.consumer_group_id,
        topics=[TOPIC_TRANSLATION_TEXT],
        config={"enable.auto.commit": False},
    )
    producer = KafkaProducerWrapper.from_confluent(settings.kafka_bootstrap_servers)

    synthesizer: Synthesizer = SynthesizerFactory.create()
    
    # Optional warmup if supported
    if hasattr(synthesizer, "warmup") and callable(synthesizer.warmup):
        LOGGER.info("Warming up TTS model")
        synthesizer.warmup()
        LOGGER.info("TTS model warmup complete")

    storage = ObjectStorage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket,
        secure=settings.minio_secure,
        public_endpoint=settings.minio_public_endpoint or None,
        presign_expiry_seconds=settings.minio_presigned_expires_seconds,
    )

    LOGGER.info(
        "TTS service started; consuming from %s model=%s",
        TOPIC_TRANSLATION_TEXT,
        settings.model_name,
    )

    try:
        while True:
            try:
                polled = consumer.poll_with_message(
                    input_schema, timeout=settings.poll_timeout_seconds
                )
            except Exception as exc:
                TTS_ERRORS_TOTAL.labels("deserialize").inc()
                LOGGER.warning("Failed to decode event: %s", exc)
                continue
            if polled is None:
                continue
            event, message = polled
            try:
                process_event(
                    event=event,
                    synthesizer=synthesizer,
                    storage=storage,
                    producer=producer,
                    output_schema=output_schema,
                    inline_max_bytes=settings.inline_payload_max_bytes,
                    model_name=settings.model_name,
                )
            except ValueError as exc:
                TTS_ERRORS_TOTAL.labels("validation").inc()
                LOGGER.warning("Dropping event correlation_id=%s reason=%s", event.get("correlation_id"), exc)
            except Exception:  # pragma: no cover - safety net for runtime errors
                TTS_ERRORS_TOTAL.labels("unexpected").inc()
                LOGGER.exception("Unexpected error while processing event")
            finally:
                consumer.commit_message(message)
    except KeyboardInterrupt:
        LOGGER.info("TTS service shutting down")


if __name__ == "__main__":
    main()
