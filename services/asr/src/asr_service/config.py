from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap_servers: str
    schema_registry_url: str
    model_name: str
    consumer_group_id: str
    poll_timeout_seconds: float
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
            model_name=os.getenv("MODEL_NAME", "openai/whisper-tiny"),
            consumer_group_id=os.getenv("CONSUMER_GROUP_ID", "asr-service"),
            poll_timeout_seconds=float(os.getenv("POLL_TIMEOUT_SECONDS", "1.0")),
            schema_dir=Path(os.getenv("SCHEMA_DIR", "shared/schemas/avro")),
            input_topic=os.getenv("ASR_INPUT_TOPIC", "speech.audio.ingress"),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000"),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            minio_bucket=os.getenv("MINIO_BUCKET", "audio-ingress"),
            minio_secure=os.getenv("MINIO_SECURE", "0") == "1",
            disable_storage=os.getenv("ASR_DISABLE_STORAGE", "0") == "1",
        )
