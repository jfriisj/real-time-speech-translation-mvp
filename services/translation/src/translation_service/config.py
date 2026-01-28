from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap_servers: str
    schema_registry_url: str
    schema_registry_wait_timeout_seconds: float
    consumer_group_id: str
    poll_timeout_seconds: float
    schema_dir: Path
    target_language: str
    model_name: str
    max_new_tokens: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            kafka_bootstrap_servers=os.getenv(
                "KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:29092"
            ),
            schema_registry_url=os.getenv(
                "SCHEMA_REGISTRY_URL", "http://127.0.0.1:8081"
            ),
            schema_registry_wait_timeout_seconds=float(
                os.getenv("SCHEMA_REGISTRY_WAIT_TIMEOUT_SECONDS", "60")
            ),
            consumer_group_id=os.getenv("CONSUMER_GROUP_ID", "translation-service"),
            poll_timeout_seconds=float(os.getenv("POLL_TIMEOUT_SECONDS", "1.0")),
            schema_dir=Path(os.getenv("SCHEMA_DIR", "shared/schemas/avro")),
            target_language=os.getenv("TARGET_LANGUAGE", "es"),
            model_name=os.getenv("TRANSLATION_MODEL_NAME", "Helsinki-NLP/opus-mt-en-es"),
            max_new_tokens=int(os.getenv("MAX_NEW_TOKENS", "256")),
        )
