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
    consumer_group_id: str
    poll_timeout_seconds: float
    schema_dir: Path
    target_language: str
    model_name: str
    max_new_tokens: int

    @classmethod
    def from_env(cls) -> "Settings":
        max_wait_seconds = os.getenv("STARTUP_MAX_WAIT_SECONDS")
        if max_wait_seconds is None:
            max_wait_seconds = os.getenv("SCHEMA_REGISTRY_WAIT_TIMEOUT_SECONDS", "60")
        return cls(
            kafka_bootstrap_servers=os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:29092"
            ),
            schema_registry_url=os.getenv(
                "SCHEMA_REGISTRY_URL", "http://127.0.0.1:8081"
            ),
            startup_max_wait_seconds=float(max_wait_seconds),
            startup_initial_backoff_seconds=float(
                os.getenv("STARTUP_INITIAL_BACKOFF_SECONDS", "1")
            ),
            startup_max_backoff_seconds=float(
                os.getenv("STARTUP_MAX_BACKOFF_SECONDS", "5")
            ),
            startup_attempt_timeout_seconds=float(
                os.getenv("STARTUP_ATTEMPT_TIMEOUT_SECONDS", "2")
            ),
            consumer_group_id=os.getenv("CONSUMER_GROUP_ID", "translation-service"),
            poll_timeout_seconds=float(os.getenv("POLL_TIMEOUT_SECONDS", "1.0")),
            schema_dir=Path(os.getenv("SCHEMA_DIR", "shared/schemas/avro")),
            target_language=os.getenv("TARGET_LANGUAGE", "es"),
            model_name=os.getenv("TRANSLATION_MODEL_NAME", "Helsinki-NLP/opus-mt-en-es"),
            max_new_tokens=int(os.getenv("MAX_NEW_TOKENS", "256")),
        )
