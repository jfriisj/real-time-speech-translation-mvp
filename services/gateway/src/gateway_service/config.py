from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import FrozenSet

from speech_lib import AUDIO_PAYLOAD_MAX_BYTES


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap_servers: str
    schema_registry_url: str
    startup_max_wait_seconds: float
    startup_initial_backoff_seconds: float
    startup_max_backoff_seconds: float
    startup_attempt_timeout_seconds: float
    schema_dir: Path
    host: str
    port: int
    audio_format: str
    sample_rate_hz: int
    max_buffer_bytes: int
    max_chunk_bytes: int
    max_connections: int
    idle_timeout_seconds: float
    max_session_seconds: float
    max_messages_per_second: int
    origin_allowlist: FrozenSet[str]
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
            schema_dir=Path(os.getenv("SCHEMA_DIR", "shared/schemas/avro")),
            host=os.getenv("GATEWAY_HOST", "0.0.0.0"),
            port=int(os.getenv("GATEWAY_PORT", "8000")),
            audio_format=os.getenv("AUDIO_FORMAT", "wav"),
            sample_rate_hz=int(os.getenv("SAMPLE_RATE_HZ", "16000")),
            max_buffer_bytes=int(
                os.getenv("MAX_BUFFER_BYTES", str(AUDIO_PAYLOAD_MAX_BYTES * 4))
            ),
            max_chunk_bytes=int(os.getenv("MAX_CHUNK_BYTES", "65536")),
            max_connections=int(os.getenv("MAX_CONNECTIONS", "10")),
            idle_timeout_seconds=float(os.getenv("IDLE_TIMEOUT_SECONDS", "10")),
            max_session_seconds=float(os.getenv("MAX_SESSION_SECONDS", "60")),
            max_messages_per_second=int(os.getenv("MAX_MESSAGES_PER_SECOND", "200")),
            origin_allowlist=_parse_allowlist(os.getenv("ORIGIN_ALLOWLIST", "")),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000"),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            minio_bucket=os.getenv("MINIO_BUCKET", "audio-ingress"),
            minio_secure=os.getenv("MINIO_SECURE", "0") == "1",
            disable_storage=os.getenv("GATEWAY_DISABLE_STORAGE", "0") == "1",
        )


def _parse_allowlist(raw: str) -> FrozenSet[str]:
    entries = [item.strip() for item in raw.split(",") if item.strip()]
    return frozenset(entries)
