from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from speech_lib import (
    AUDIO_PAYLOAD_MAX_BYTES,
    BaseEvent,
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    ObjectStorage,
    SchemaRegistryClient,
    TOPIC_AUDIO_INGRESS,
    TOPIC_SPEECH_SEGMENT,
    load_schema,
    select_transport_mode,
)

from .config import Settings
from .processing import (
    build_segments,
    decode_wav,
    resample_audio,
    validate_audio_payload,
)
from speech_lib.startup import wait_for_dependencies
from .vad import VadModel, infer_speech_probabilities, load_onnx_model


LOGGER = logging.getLogger(__name__)


def _resolve_schema_dir(schema_dir: Path) -> Path:
    if schema_dir.exists():
        return schema_dir
    candidate = Path(__file__).resolve().parents[4] / "shared" / "schemas" / "avro"
    return candidate


def register_schemas(
    registry: SchemaRegistryClient,
    input_schema: Dict[str, Any],
    output_schema: Dict[str, Any],
) -> tuple[int, int]:
    input_schema_id = registry.register_schema(
        f"{TOPIC_AUDIO_INGRESS}-value", input_schema
    )
    output_schema_id = registry.register_schema(
        f"{TOPIC_SPEECH_SEGMENT}-value", output_schema
    )
    return input_schema_id, output_schema_id


def _load_vad_model(settings: Settings) -> Optional[VadModel]:
    if not settings.use_onnx:
        LOGGER.info("VAD ONNX disabled; using energy-based segmentation")
        return None

    try:
        model = load_onnx_model(settings.model_repo, settings.model_filename)
    except Exception as exc:
        LOGGER.warning("Unable to load ONNX VAD model: %s", exc)
        return None

    LOGGER.info("Loaded VAD model repo=%s filename=%s", settings.model_repo, settings.model_filename)
    return model


def process_event(
    *,
    event: Dict[str, Any],
    producer: KafkaProducerWrapper,
    output_schema: Dict[str, Any],
    output_schema_id: int,
    settings: Settings,
    vad_model: Optional[VadModel],
    storage: ObjectStorage | None,
    traceparent: str | None = None,
) -> None:
    correlation_id = str(event.get("correlation_id", "")).strip()
    if not correlation_id:
        raise ValueError("missing correlation_id")

    payload = event.get("payload") or {}
    audio_bytes, sample_rate_hz, audio_format = validate_audio_payload(payload, storage)
    speaker_reference_bytes = payload.get("speaker_reference_bytes")
    speaker_id = payload.get("speaker_id")
    audio, actual_rate = decode_wav(audio_bytes, sample_rate_hz)
    audio, effective_rate = resample_audio(audio, actual_rate, settings.target_sample_rate_hz)

    speech_probabilities = None
    if vad_model is not None:
        frame_length = max(1, int(effective_rate * settings.window_ms / 1000))
        hop_length = max(1, int(effective_rate * settings.hop_ms / 1000))
        probabilities = infer_speech_probabilities(
            model=vad_model,
            audio=audio,
            sample_rate_hz=effective_rate,
            frame_length=frame_length,
            hop_length=hop_length,
        )
        if probabilities.size > 0:
            speech_probabilities = probabilities

    segments = build_segments(
        audio=audio,
        sample_rate_hz=effective_rate,
        window_ms=settings.window_ms,
        hop_ms=settings.hop_ms,
        speech_threshold=settings.speech_threshold,
        energy_threshold=settings.energy_threshold,
        min_speech_ms=settings.min_speech_ms,
        min_silence_ms=settings.min_silence_ms,
        padding_ms=settings.padding_ms,
        speech_probabilities=speech_probabilities,
    )

    if not segments:
        LOGGER.info("No speech segments detected correlation_id=%s", correlation_id)
        return

    for index, segment in enumerate(segments):
        decision = select_transport_mode(
            payload_size_bytes=len(segment.audio_bytes),
            threshold_bytes=AUDIO_PAYLOAD_MAX_BYTES,
        )
        audio_bytes_out: bytes | None = segment.audio_bytes
        segment_uri: str | None = None
        bucket: str | None = None
        key: str | None = None
        if decision.mode == "uri":
            if settings.disable_storage or storage is None:
                LOGGER.error(
                    "event_name=claim_check_drop correlation_id=%s reason=storage_unavailable payload_size_bytes=%s threshold_bytes=%s",
                    correlation_id,
                    len(segment.audio_bytes),
                    AUDIO_PAYLOAD_MAX_BYTES,
                )
                continue
            key = f"{correlation_id}/{index}.wav"
            try:
                segment_uri = storage.upload_bytes(
                    key=key,
                    data=segment.audio_bytes,
                    content_type="audio/wav",
                    return_key=True,
                )
                bucket, key = ObjectStorage.parse_s3_uri(segment_uri)
                audio_bytes_out = None
            except Exception:  # pragma: no cover - storage failure guard
                LOGGER.error(
                    "event_name=claim_check_drop correlation_id=%s reason=storage_error payload_size_bytes=%s threshold_bytes=%s",
                    correlation_id,
                    len(segment.audio_bytes),
                    AUDIO_PAYLOAD_MAX_BYTES,
                )
                continue

        output_event = BaseEvent(
            event_type="SpeechSegmentEvent",
            correlation_id=correlation_id,
            source_service="vad-service",
            payload={
                "segment_id": str(uuid4()),
                "segment_index": index,
                "start_ms": int(segment.start_ms),
                "end_ms": int(segment.end_ms),
                "audio_bytes": audio_bytes_out,
                "segment_uri": segment_uri,
                "sample_rate_hz": effective_rate,
                "audio_format": audio_format,
                "speaker_reference_bytes": speaker_reference_bytes
                if isinstance(speaker_reference_bytes, (bytes, bytearray))
                else None,
                "speaker_id": str(speaker_id).strip() if speaker_id else None,
            },
        )

        if traceparent:
            producer.publish_event(
                TOPIC_SPEECH_SEGMENT,
                output_event,
                output_schema,
                key=correlation_id,
                headers={"traceparent": traceparent},
                schema_id=output_schema_id,
            )
        else:
            producer.publish_event(
                TOPIC_SPEECH_SEGMENT,
                output_event,
                output_schema,
                key=correlation_id,
                schema_id=output_schema_id,
            )
        LOGGER.info(
            "Published SpeechSegmentEvent correlation_id=%s segment_index=%s",
            correlation_id,
            index,
        )
        LOGGER.info(
            "event_name=%s correlation_id=%s transport_mode=%s payload_size_bytes=%s threshold_bytes=%s bucket=%s key=%s",
            "claim_check_offload" if decision.mode == "uri" else "claim_check_inline",
            correlation_id,
            decision.mode,
            decision.payload_size_bytes,
            decision.threshold_bytes,
            bucket,
            key,
        )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    settings = Settings.from_env()
    schema_dir = _resolve_schema_dir(settings.schema_dir)

    wait_for_dependencies(settings)

    input_schema = load_schema("AudioInputEvent.avsc", schema_dir=schema_dir)
    output_schema = load_schema("SpeechSegmentEvent.avsc", schema_dir=schema_dir)

    registry = SchemaRegistryClient(settings.schema_registry_url)
    _input_schema_id, output_schema_id = register_schemas(
        registry, input_schema, output_schema
    )

    consumer = KafkaConsumerWrapper.from_confluent(
        settings.kafka_bootstrap_servers,
        group_id=settings.consumer_group_id,
        topics=[TOPIC_AUDIO_INGRESS],
        schema_registry=registry,
    )
    producer = KafkaProducerWrapper.from_confluent(settings.kafka_bootstrap_servers)
    vad_model = _load_vad_model(settings)
    storage = None
    if not settings.disable_storage:
        storage = ObjectStorage(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket,
            secure=settings.minio_secure,
        )

    LOGGER.info("VAD service started; consuming from %s", TOPIC_AUDIO_INGRESS)

    try:
        while True:
            polled = consumer.poll_with_message(
                input_schema, timeout=settings.poll_timeout_seconds
            )
            if polled is None:
                continue
            event, message = polled
            try:
                traceparent = None
                headers = message.headers() if hasattr(message, "headers") else None
                if headers:
                    for key, value in headers:
                        if key == "traceparent":
                            traceparent = (
                                value.decode("utf-8", errors="ignore")
                                if isinstance(value, bytes)
                                else value
                            )
                            break
                process_event(
                    event=event,
                    producer=producer,
                    output_schema=output_schema,
                    output_schema_id=output_schema_id,
                    settings=settings,
                    vad_model=vad_model,
                    storage=storage,
                    traceparent=traceparent,
                )
            except ValueError as exc:
                LOGGER.warning("Dropping event: %s", exc)
            except Exception:  # pragma: no cover - safety net for runtime errors
                LOGGER.exception("Unexpected error while processing event")
    except KeyboardInterrupt:
        LOGGER.info("VAD service shutting down")


if __name__ == "__main__":
    main()
