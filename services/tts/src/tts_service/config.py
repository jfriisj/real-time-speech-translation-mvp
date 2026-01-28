from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from speech_lib import AUDIO_PAYLOAD_MAX_BYTES


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap_servers: str
    schema_registry_url: str
    startup_max_wait_seconds: float
    startup_initial_backoff_seconds: float
    startup_max_backoff_seconds: float
    startup_attempt_timeout_seconds: float
    consumer_group_id: str
    poll_timeout_seconds: float
    consumer_session_timeout_ms: int
    consumer_heartbeat_interval_ms: int
    consumer_max_poll_interval_ms: int
    consumer_partition_assignment_strategy: str | None
    consumer_enable_static_membership: bool
    consumer_group_instance_id: str | None
    schema_dir: Path
    model_engine: str
    model_repo: str
    model_revision: str
    model_filename: str
    model_cache_dir: Path
    model_name: str
    sample_rate_hz: int
    tts_speed: float
    max_text_length: int
    inline_payload_max_bytes: int
    disable_storage: bool
    audio_uri_mode: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool
    minio_public_endpoint: str | None
    minio_presign_expiry_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:29092"),
            schema_registry_url=os.getenv("SCHEMA_REGISTRY_URL", "http://127.0.0.1:8081"),
            startup_max_wait_seconds=float(
                os.getenv("STARTUP_MAX_WAIT_SECONDS", "60")
            ),
            startup_initial_backoff_seconds=float(
                os.getenv("STARTUP_INITIAL_BACKOFF_SECONDS", "1")
            ),
            startup_max_backoff_seconds=float(
                os.getenv("STARTUP_MAX_BACKOFF_SECONDS", "5")
            ),
            startup_attempt_timeout_seconds=float(
                os.getenv("STARTUP_ATTEMPT_TIMEOUT_SECONDS", "2")
            ),
            consumer_group_id=os.getenv("CONSUMER_GROUP_ID", "tts-service"),
            poll_timeout_seconds=float(os.getenv("POLL_TIMEOUT_SECONDS", "1.0")),
            consumer_session_timeout_ms=int(
                os.getenv("KAFKA_CONSUMER_SESSION_TIMEOUT_MS", "15000")
            ),
            consumer_heartbeat_interval_ms=int(
                os.getenv("KAFKA_CONSUMER_HEARTBEAT_INTERVAL_MS", "5000")
            ),
            consumer_max_poll_interval_ms=int(
                os.getenv("KAFKA_CONSUMER_MAX_POLL_INTERVAL_MS", "300000")
            ),
            consumer_partition_assignment_strategy=(
                os.getenv("KAFKA_CONSUMER_PARTITION_ASSIGNMENT_STRATEGY") or None
            ),
            consumer_enable_static_membership=(
                os.getenv("KAFKA_CONSUMER_ENABLE_STATIC_MEMBERSHIP", "0") == "1"
            ),
            consumer_group_instance_id=(
                os.getenv("KAFKA_CONSUMER_GROUP_INSTANCE_ID") or None
            ),
            schema_dir=Path(os.getenv("SCHEMA_DIR", "shared/schemas/avro")),
            model_engine=os.getenv("TTS_MODEL_ENGINE", "kokoro_onnx"),
            model_repo=os.getenv("TTS_MODEL_REPO", "onnx-community/Kokoro-82M-v1.0-ONNX"),
            model_revision=os.getenv(
                "TTS_MODEL_REVISION", "1939ad2a8e416c0acfeecc08a694d14ef25f2231"
            ),
            model_filename=os.getenv("TTS_MODEL_FILENAME", "onnx/model.onnx"),
            model_cache_dir=Path(os.getenv("TTS_MODEL_CACHE_DIR", "model_cache")),
            model_name=os.getenv("TTS_MODEL_NAME", "kokoro-82m-onnx"),
            sample_rate_hz=int(os.getenv("TTS_SAMPLE_RATE_HZ", "24000")),
            tts_speed=float(os.getenv("TTS_SPEED", "1.0")),
            max_text_length=int(os.getenv("MAX_TEXT_LENGTH", "500")),
            inline_payload_max_bytes=int(
                os.getenv("INLINE_PAYLOAD_MAX_BYTES", str(AUDIO_PAYLOAD_MAX_BYTES))
            ),
            disable_storage=os.getenv("DISABLE_STORAGE", "0") == "1",
            audio_uri_mode=os.getenv("TTS_AUDIO_URI_MODE", "internal"),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000"),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            minio_bucket=os.getenv("MINIO_BUCKET", "tts-audio"),
            minio_secure=os.getenv("MINIO_SECURE", "0") == "1",
            minio_public_endpoint=os.getenv("MINIO_PUBLIC_ENDPOINT") or None,
            minio_presign_expiry_seconds=int(
                os.getenv("MINIO_PRESIGN_EXPIRY_SECONDS", str(60 * 60 * 24))
            ),
        )
