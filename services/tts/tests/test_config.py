from __future__ import annotations

from pathlib import Path

from tts_service.config import Settings


def test_settings_from_env_defaults(monkeypatch) -> None:
    monkeypatch.delenv("KAFKA_BOOTSTRAP_SERVERS", raising=False)
    monkeypatch.delenv("SCHEMA_REGISTRY_URL", raising=False)
    monkeypatch.delenv("DISABLE_STORAGE", raising=False)
    monkeypatch.delenv("TTS_MODEL_REVISION", raising=False)

    settings = Settings.from_env()

    assert settings.kafka_bootstrap_servers == "127.0.0.1:29092"
    assert settings.schema_registry_url == "http://127.0.0.1:8081"
    assert settings.disable_storage is False
    assert settings.schema_dir == Path("shared/schemas/avro")
    assert settings.model_revision == "1939ad2a8e416c0acfeecc08a694d14ef25f2231"


def test_settings_from_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    monkeypatch.setenv("SCHEMA_REGISTRY_URL", "http://schema:8081")
    monkeypatch.setenv("DISABLE_STORAGE", "1")
    monkeypatch.setenv("TTS_SPEED", "1.25")
    monkeypatch.setenv("TTS_SAMPLE_RATE_HZ", "16000")
    monkeypatch.setenv("TTS_MODEL_REVISION", "rev-123")

    settings = Settings.from_env()

    assert settings.kafka_bootstrap_servers == "kafka:9092"
    assert settings.schema_registry_url == "http://schema:8081"
    assert settings.disable_storage is True
    assert settings.tts_speed == 1.25
    assert settings.sample_rate_hz == 16000
    assert settings.model_revision == "rev-123"