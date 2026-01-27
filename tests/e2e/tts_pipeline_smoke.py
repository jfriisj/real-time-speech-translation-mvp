from __future__ import annotations

import json
import math
import os
import struct
import time
import wave
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse
from urllib.request import urlopen
from uuid import uuid4

from speech_lib import (
    BaseEvent,
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    TOPIC_TRANSLATION_TEXT,
    TOPIC_TTS_OUTPUT,
    load_schema,
    ObjectStorage,
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


def _load_phrase_set() -> list[dict]:
    phrase_file = os.getenv("TTS_SMOKE_PHRASE_FILE")
    if phrase_file:
        data = json.loads(Path(phrase_file).read_text())
        return data if isinstance(data, list) else []
    if os.getenv("TTS_SMOKE_PHRASE_SET", "").lower() == "curated":
        curated = Path(__file__).resolve().parents[2] / "tests" / "data" / "metrics" / "tts_phrases.json"
        data = json.loads(curated.read_text())
        return data if isinstance(data, list) else []
    return []


def _register_schemas(
    registry: SchemaRegistryClient, schema_dir: Path
) -> tuple[dict[str, dict], dict[str, int]]:
    schemas = {
        "translation": load_schema("TextTranslatedEvent.avsc", schema_dir=schema_dir),
        "tts": load_schema("AudioSynthesisEvent.avsc", schema_dir=schema_dir),
    }
    ids = {
        "translation": registry.register_schema(
            f"{TOPIC_TRANSLATION_TEXT}-value", schemas["translation"]
        ),
        "tts": registry.register_schema(f"{TOPIC_TTS_OUTPUT}-value", schemas["tts"]),
    }
    return schemas, ids


def _await_event(
    consumer: KafkaConsumerWrapper,
    schema: dict,
    correlation_id: str,
    timeout_seconds: float,
) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        event = consumer.poll(schema, timeout=0.5)
        if event is None:
            continue
        if event.get("correlation_id") != correlation_id:
            continue
        return event
    raise TimeoutError("Timed out waiting for AudioSynthesisEvent")


def _rewrite_minio_uri(audio_uri: str, public_endpoint: str) -> str:
    parsed = urlparse(audio_uri)
    if parsed.hostname and parsed.hostname != "minio":
        return audio_uri
    public_parsed = urlparse(public_endpoint)
    rewritten = parsed._replace(
        scheme=public_parsed.scheme or parsed.scheme,
        netloc=public_parsed.netloc or parsed.netloc,
    )
    return urlunparse(rewritten)


def _prime_consumer(consumer: KafkaConsumerWrapper, schema: dict) -> None:
    deadline = time.time() + 5
    while time.time() < deadline:
        consumer.consumer.poll(0.2)
        if consumer.consumer.assignment():
            return
        time.sleep(0.1)


def _fetch_audio(
    audio_uri: str,
    public_endpoint: str,
    timeout_seconds: float,
) -> bytes:
    if audio_uri.startswith("s3://"):
        bucket, key = audio_uri.replace("s3://", "", 1).split("/", 1)
        storage = ObjectStorage(
            endpoint=os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            bucket=bucket,
            secure=os.getenv("MINIO_SECURE", "0") == "1",
            public_endpoint=os.getenv("MINIO_PUBLIC_ENDPOINT") or None,
        )
        audio_uri = storage.presign_get(key=key)
    elif "://" not in audio_uri:
        bucket = os.getenv("MINIO_BUCKET", "tts-audio")
        storage = ObjectStorage(
            endpoint=os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            bucket=bucket,
            secure=os.getenv("MINIO_SECURE", "0") == "1",
            public_endpoint=os.getenv("MINIO_PUBLIC_ENDPOINT") or None,
        )
        audio_uri = storage.presign_get(key=audio_uri)
    resolved_uri = _rewrite_minio_uri(audio_uri, public_endpoint)
    with urlopen(resolved_uri, timeout=timeout_seconds) as response:
        return response.read()


def _validate_payload(payload: dict, expected_mode: Optional[str], public_endpoint: str) -> None:
    audio_bytes = payload.get("audio_bytes")
    audio_uri = payload.get("audio_uri")

    has_bytes = isinstance(audio_bytes, (bytes, bytearray)) and bool(audio_bytes)
    has_uri = isinstance(audio_uri, str) and bool(audio_uri.strip())
    if has_bytes == has_uri:
        raise ValueError("Expected exactly one of audio_bytes or audio_uri")

    payload_mode = "URI" if has_uri else "INLINE"
    if expected_mode and payload_mode != expected_mode:
        raise AssertionError(
            f"Expected payload_mode={expected_mode} but got {payload_mode}"
        )

    if has_uri:
        data = _fetch_audio(audio_uri, public_endpoint, timeout_seconds=10.0)
        if not data:
            raise ValueError("Fetched audio_uri returned empty payload")
    else:
        if not audio_bytes:
            raise ValueError("Inline audio_bytes payload is empty")


def main() -> int:
    kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:29092")
    schema_registry_url = os.getenv("SCHEMA_REGISTRY_URL", "http://127.0.0.1:8081")
    public_endpoint = os.getenv("MINIO_PUBLIC_ENDPOINT", "http://127.0.0.1:9000")
    expected_mode = os.getenv("EXPECT_PAYLOAD_MODE", "").upper() or None
    timeout_seconds = float(os.getenv("TTS_SMOKE_TIMEOUT", "240"))
    input_text = os.getenv(
        "TTS_SMOKE_TEXT",
        "Hello from the TTS smoke test. This checks inline or URI payload delivery.",
    )
    phrase_limit = int(os.getenv("TTS_SMOKE_PHRASE_LIMIT", "5"))
    phrases = _load_phrase_set()

    schema_dir = _resolve_schema_dir()
    registry = SchemaRegistryClient(schema_registry_url)
    schemas, schema_ids = _register_schemas(registry, schema_dir)

    producer = KafkaProducerWrapper.from_confluent(kafka_bootstrap)
    consumer = KafkaConsumerWrapper.from_confluent(
        kafka_bootstrap,
        group_id=f"tts-smoke-{int(time.time())}",
        topics=[TOPIC_TTS_OUTPUT],
        config={
            "enable.auto.commit": False,
            "auto.offset.reset": "latest",
        },
        schema_registry=registry,
    )

    _prime_consumer(consumer, schemas["tts"])

    speaker_reference = _make_wav_bytes()
    if phrases:
        phrases = phrases[:phrase_limit]
        for phrase in phrases:
            correlation_id = f"tts-smoke-{uuid4()}"
            event = BaseEvent(
                event_type="TextTranslatedEvent",
                correlation_id=correlation_id,
                source_service="tts-smoke-test",
                payload={
                    "text": phrase.get("text", ""),
                    "source_language": phrase.get("language", "en"),
                    "target_language": "es",
                    "quality_score": None,
                    "speaker_reference_bytes": speaker_reference,
                    "speaker_id": "smoke-speaker",
                },
            )

            producer.publish_event(
                TOPIC_TRANSLATION_TEXT,
                event,
                schemas["translation"],
                schema_id=schema_ids["translation"],
            )
            output_event = _await_event(consumer, schemas["tts"], correlation_id, timeout_seconds)
            payload = output_event.get("payload") or {}
            _validate_payload(payload, expected_mode, public_endpoint)
            print(f"PASS: {phrase.get('id', correlation_id)}")
    else:
        correlation_id = f"tts-smoke-{uuid4()}"
        event = BaseEvent(
            event_type="TextTranslatedEvent",
            correlation_id=correlation_id,
            source_service="tts-smoke-test",
            payload={
                "text": input_text,
                "source_language": "en",
                "target_language": "es",
                "quality_score": None,
                "speaker_reference_bytes": speaker_reference,
                "speaker_id": "smoke-speaker",
            },
        )

        producer.publish_event(
            TOPIC_TRANSLATION_TEXT,
            event,
            schemas["translation"],
            schema_id=schema_ids["translation"],
        )
        output_event = _await_event(consumer, schemas["tts"], correlation_id, timeout_seconds)
        payload = output_event.get("payload") or {}
        _validate_payload(payload, expected_mode, public_endpoint)
        print("PASS: TTS pipeline produced AudioSynthesisEvent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())