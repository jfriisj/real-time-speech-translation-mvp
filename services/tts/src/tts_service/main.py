from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path
from typing import Any

from speech_lib import (
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    TOPIC_TRANSLATION_TEXT,
    TOPIC_TTS_OUTPUT,
    load_schema,
)
from speech_lib.storage import ObjectStorage

from .config import Settings
from .factory import SynthesizerFactory
from .processing import (
    build_audio_payload,
    build_output_event,
    compute_rtf,
    enforce_text_limit,
    extract_translation_request,
    select_audio_transport,
)
from speech_lib.startup import wait_for_dependencies


LOGGER = logging.getLogger(__name__)


def _resolve_schema_dir(schema_dir: Path) -> Path:
    if schema_dir.exists():
        return schema_dir
    candidate = Path(__file__).resolve().parents[4] / "shared" / "schemas" / "avro"
    return candidate


def _build_storage(settings: Settings) -> ObjectStorage | None:
    if settings.disable_storage:
        return None
    return ObjectStorage(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket,
        secure=settings.minio_secure,
        public_endpoint=settings.minio_public_endpoint,
        presign_expiry_seconds=settings.minio_presign_expiry_seconds,
    )


def _extract_traceparent(message: Any) -> str | None:
    if message is None:
        return None
    headers = message.headers() if hasattr(message, "headers") else None
    if not headers:
        return None
    for key, value in headers:
        if key == "traceparent":
            if isinstance(value, bytes):
                return value.decode("utf-8", errors="ignore")
            if isinstance(value, str):
                return value
    return None


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    settings = Settings.from_env()
    schema_dir = _resolve_schema_dir(settings.schema_dir)

    wait_for_dependencies(settings)

    input_schema = load_schema("TextTranslatedEvent.avsc", schema_dir=schema_dir)
    output_schema = load_schema("AudioSynthesisEvent.avsc", schema_dir=schema_dir)

    registry = SchemaRegistryClient(settings.schema_registry_url)
    _input_schema_id = registry.register_schema(
        f"{TOPIC_TRANSLATION_TEXT}-value", input_schema
    )
    output_schema_id = registry.register_schema(
        f"{TOPIC_TTS_OUTPUT}-value", output_schema
    )

    consumer = KafkaConsumerWrapper.from_confluent(
        settings.kafka_bootstrap_servers,
        group_id=settings.consumer_group_id,
        topics=[TOPIC_TRANSLATION_TEXT],
        config={"enable.auto.commit": False},
        schema_registry=registry,
    )
    producer = KafkaProducerWrapper.from_confluent(settings.kafka_bootstrap_servers)
    synthesizer = SynthesizerFactory.create(settings)
    storage = _build_storage(settings)

    LOGGER.info(
        "TTS service started; consuming from %s engine=%s",
        TOPIC_TRANSLATION_TEXT,
        settings.model_engine,
    )

    try:
        while True:
            polled = consumer.poll_with_message(input_schema, timeout=settings.poll_timeout_seconds)
            if polled is None:
                continue

            event, message = polled
            traceparent = _extract_traceparent(message)
            correlation_id = str(event.get("correlation_id", "")).strip() or "unknown"
            try:
                request = extract_translation_request(event)
                enforce_text_limit(request.text, settings.max_text_length)

                synthesis_start = time.perf_counter()
                synthesized = synthesizer.synthesize(
                    request.text,
                    speaker_id=request.speaker_id,
                    speed=settings.tts_speed,
                )
                synthesis_latency_ms = (time.perf_counter() - synthesis_start) * 1000
                rtf = compute_rtf(synthesized.duration_ms, synthesis_latency_ms)

                audio_bytes = synthesized.audio_bytes
                audio_size_bytes = len(audio_bytes)
                audio_sha256 = hashlib.sha256(audio_bytes).hexdigest()
                audio_bytes_out, audio_uri, mode = select_audio_transport(
                    audio_bytes=audio_bytes,
                    inline_limit_bytes=settings.inline_payload_max_bytes,
                    disable_storage=settings.disable_storage,
                    storage=storage,
                    audio_uri_mode=settings.audio_uri_mode,
                    correlation_id=request.correlation_id,
                )

                payload = build_audio_payload(
                    audio_bytes=audio_bytes_out,
                    audio_uri=audio_uri,
                    duration_ms=synthesized.duration_ms,
                    sample_rate_hz=synthesized.sample_rate_hz,
                    model_name=synthesized.model_name,
                    speaker_reference_bytes=request.speaker_reference_bytes,
                    speaker_id=request.speaker_id,
                    text_snippet=request.text[:120],
                    audio_sha256=audio_sha256,
                    audio_size_bytes=audio_size_bytes,
                )

                output_event = build_output_event(
                    correlation_id=request.correlation_id,
                    payload=payload,
                )

                headers = {"traceparent": traceparent} if traceparent else None
                producer.publish_event(
                    TOPIC_TTS_OUTPUT,
                    output_event,
                    output_schema,
                    key=request.correlation_id,
                    headers=headers,
                    schema_id=output_schema_id,
                )

                bucket = None
                key = None
                if audio_uri and audio_uri.startswith("s3://"):
                    try:
                        bucket, key = ObjectStorage.parse_s3_uri(audio_uri)
                    except ValueError:
                        bucket = None
                        key = None

                LOGGER.info(
                    "Published AudioSynthesisEvent correlation_id=%s audio_size_bytes=%s transport_mode=%s synthesis_latency_ms=%.2f rtf=%s",
                    request.correlation_id,
                    audio_size_bytes,
                    mode,
                    synthesis_latency_ms,
                    f"{rtf:.3f}" if rtf is not None else "n/a",
                )
                LOGGER.info(
                    "event_name=%s correlation_id=%s transport_mode=%s payload_size_bytes=%s threshold_bytes=%s bucket=%s key=%s",
                    "claim_check_offload" if mode == "uri" else "claim_check_inline",
                    request.correlation_id,
                    mode,
                    audio_size_bytes,
                    settings.inline_payload_max_bytes,
                    bucket,
                    key,
                )
            except ValueError as exc:
                if "Payload too large" in str(exc):
                    LOGGER.error(
                        "event_name=claim_check_drop correlation_id=%s reason=storage_unavailable payload_size_bytes=%s threshold_bytes=%s",
                        correlation_id,
                        "unknown",
                        settings.inline_payload_max_bytes,
                    )
                LOGGER.warning("Dropping event correlation_id=%s: %s", correlation_id, exc)
            except Exception:  # pragma: no cover - safety net
                LOGGER.exception(
                    "Unexpected error while processing event correlation_id=%s",
                    correlation_id,
                )
            finally:
                consumer.commit_message(message)
    except KeyboardInterrupt:
        LOGGER.info("TTS service shutting down")


if __name__ == "__main__":
    main()
