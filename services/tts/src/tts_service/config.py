from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap_servers: str
    schema_registry_url: str
    consumer_group_id: str
    poll_timeout_seconds: float
    schema_dir: Path
    model_name: str
    inline_payload_max_bytes: int
    tts_model_dir: str
    tts_model_cache_dir: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool
    minio_public_endpoint: str
    minio_presigned_expires_seconds: int
    metrics_port: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:29092"),
            schema_registry_url=os.getenv("SCHEMA_REGISTRY_URL", "http://127.0.0.1:8081"),
            consumer_group_id=os.getenv("CONSUMER_GROUP_ID", "tts-service"),
            poll_timeout_seconds=float(os.getenv("POLL_TIMEOUT_SECONDS", "1.0")),
            schema_dir=Path(os.getenv("SCHEMA_DIR", "shared/schemas/avro")),
            model_name=os.getenv("TTS_MODEL_NAME", "kokoro-82m-onnx"),
            inline_payload_max_bytes=int(
                os.getenv("INLINE_PAYLOAD_MAX_BYTES", str(int(1.5 * 1024 * 1024)))
            ),
            tts_model_dir=os.getenv("TTS_MODEL_DIR", ""),
            tts_model_cache_dir=os.getenv("TTS_MODEL_CACHE_DIR", ""),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            minio_bucket=os.getenv("MINIO_BUCKET", "tts-audio"),
            minio_secure=os.getenv("MINIO_SECURE", "0") == "1",
            minio_public_endpoint=os.getenv("MINIO_PUBLIC_ENDPOINT", ""),
            minio_presigned_expires_seconds=int(
                os.getenv("MINIO_PRESIGNED_EXPIRES_SECONDS", "86400")
            ),
            metrics_port=int(os.getenv("METRICS_PORT", "0")),
        )
