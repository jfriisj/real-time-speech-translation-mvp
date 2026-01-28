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
    target_sample_rate_hz: int
    window_ms: int
    hop_ms: int
    speech_threshold: float
    energy_threshold: float
    min_speech_ms: int
    min_silence_ms: int
    padding_ms: int
    use_onnx: bool
    model_repo: str
    model_filename: str
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
            consumer_group_id=os.getenv("CONSUMER_GROUP_ID", "vad-service"),
            poll_timeout_seconds=float(os.getenv("POLL_TIMEOUT_SECONDS", "1.0")),
            schema_dir=Path(os.getenv("SCHEMA_DIR", "shared/schemas/avro")),
            target_sample_rate_hz=int(os.getenv("TARGET_SAMPLE_RATE_HZ", "16000")),
            window_ms=int(os.getenv("VAD_WINDOW_MS", "30")),
            hop_ms=int(os.getenv("VAD_HOP_MS", "10")),
            speech_threshold=float(os.getenv("VAD_SPEECH_THRESHOLD", "0.5")),
            energy_threshold=float(os.getenv("VAD_ENERGY_THRESHOLD", "0.01")),
            min_speech_ms=int(os.getenv("VAD_MIN_SPEECH_MS", "250")),
            min_silence_ms=int(os.getenv("VAD_MIN_SILENCE_MS", "200")),
            padding_ms=int(os.getenv("VAD_PADDING_MS", "100")),
            use_onnx=os.getenv("VAD_USE_ONNX", "1") != "0",
            model_repo=os.getenv("VAD_MODEL_REPO", "onnx-community/silero-vad"),
            model_filename=os.getenv("VAD_MODEL_FILENAME", "silero_vad.onnx"),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000"),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            minio_bucket=os.getenv("MINIO_BUCKET", "vad-segments"),
            minio_secure=os.getenv("MINIO_SECURE", "0") == "1",
            disable_storage=os.getenv("VAD_DISABLE_STORAGE", "0") == "1",
        )
