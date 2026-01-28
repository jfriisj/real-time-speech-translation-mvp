from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap_servers: str
    schema_registry_url: str
    startup_max_wait_seconds: float
    startup_initial_backoff_seconds: float
    startup_max_backoff_seconds: float
    startup_attempt_timeout_seconds: float
    model_name: str
    consumer_group_id: str
    poll_timeout_seconds: float
    consumer_session_timeout_ms: int
    consumer_heartbeat_interval_ms: int
    consumer_max_poll_interval_ms: int
    consumer_partition_assignment_strategy: str | None
    consumer_enable_static_membership: bool
    consumer_group_instance_id: str | None
    schema_dir: Path
    input_topic: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool
    disable_storage: bool

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
            model_name=os.getenv("MODEL_NAME", "openai/whisper-tiny"),
            consumer_group_id=os.getenv("CONSUMER_GROUP_ID", "asr-service"),
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
            input_topic=os.getenv("ASR_INPUT_TOPIC", "speech.audio.ingress"),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000"),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            minio_bucket=os.getenv("MINIO_BUCKET", "audio-ingress"),
            minio_secure=os.getenv("MINIO_SECURE", "0") == "1",
            disable_storage=os.getenv("ASR_DISABLE_STORAGE", "0") == "1",
        )
