from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pytest
import numpy as np

from tts_service import main as main_module


class _FakeRegistry:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def register_schema(self, subject: str, schema: dict) -> None:
        self.calls.append((subject, schema))


def test_resolve_schema_dir_existing(tmp_path: Path) -> None:
    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir()
    resolved = main_module._resolve_schema_dir(schema_dir)
    assert resolved == schema_dir


def test_resolve_schema_dir_fallback(tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing"
    resolved = main_module._resolve_schema_dir(missing_dir)
    assert resolved.as_posix().endswith("/shared/schemas/avro")


def test_register_schemas_uses_expected_subjects() -> None:
    registry = _FakeRegistry()
    input_schema = {"type": "record", "name": "Input"}
    output_schema = {"type": "record", "name": "Output"}

    main_module.register_schemas(registry, input_schema, output_schema)

    assert registry.calls == [
        (f"{main_module.TOPIC_TRANSLATION_TEXT}-value", input_schema),
        (f"{main_module.TOPIC_TTS_OUTPUT}-value", output_schema),
    ]


def test_extract_request_raises_on_missing_fields() -> None:
    with pytest.raises(ValueError, match="missing correlation_id"):
        main_module._extract_request({"payload": {"text": "hi"}})

    with pytest.raises(ValueError, match="missing payload.text"):
        main_module._extract_request({"correlation_id": "corr", "payload": {"text": " "}})


def test_extract_request_normalizes_fields() -> None:
    correlation_id, text, speaker_bytes, speaker_id = main_module._extract_request(
        {
            "correlation_id": " corr ",
            "payload": {
                "text": " hello ",
                "speaker_reference_bytes": bytearray(b"\x01\x02"),
                "speaker_id": " speaker ",
            },
        }
    )

    assert correlation_id == "corr"
    assert text == "hello"
    assert speaker_bytes == b"\x01\x02"
    assert speaker_id == "speaker"


@dataclass
class _FakeStorage:
    raised: bool = False
    calls: int = 0

    def upload_bytes(self, *, key: str, _data: bytes, _content_type: str) -> str:
        self.calls += 1
        if self.raised:
            raise RuntimeError("upload failed")
        return f"http://minio/tts-audio/{key}"


class _FakeProducer:
    def __init__(self) -> None:
        self.published: list[tuple[str, object, dict, str | None]] = []

    def publish_event(self, topic: str, event: object, schema: dict, key: str | None = None) -> None:
        self.published.append((topic, event, schema, key))


class _FakeSynthesizer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bytes | None]] = []

    def synthesize(self, text: str, speaker_reference_bytes: bytes | None):
        self.calls.append((text, speaker_reference_bytes))
        audio = np.zeros(1600, dtype=np.float32)
        return audio, 16000


def test_main_exits_on_keyboardinterrupt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    @dataclass(frozen=True)
    class _Settings:
        kafka_bootstrap_servers: str = "kafka"
        schema_registry_url: str = "http://schema-registry"
        consumer_group_id: str = "tts-service"
        poll_timeout_seconds: float = 0.1
        schema_dir: Path = tmp_path
        model_name: str = "IndexTeam/IndexTTS-2"
        inline_payload_max_bytes: int = 1024
        tts_model_dir: str = ""
        tts_model_cache_dir: str = ""
        minio_endpoint: str = "http://minio:9000"
        minio_access_key: str = "minioadmin"
        minio_secret_key: str = "minioadmin"
        minio_bucket: str = "tts-audio"
        minio_secure: bool = False
        minio_public_endpoint: str = ""
        minio_presigned_expires_seconds: int = 86400
        metrics_port: int = 0

    class _FakeRegistryClient:
        def __init__(self, *_args, **_kwargs) -> None:
            self.calls: list[tuple[str, dict]] = []

        def register_schema(self, subject: str, schema: dict) -> None:
            self.calls.append((subject, schema))

    class _FakeConsumer:
        def poll_with_message(self, *_args, **_kwargs):
            raise KeyboardInterrupt

        def commit_message(self, *_args, **_kwargs) -> None:
            return None

    class _FakeProducerFactory:
        @staticmethod
        def from_confluent(*_args, **_kwargs):
            return _FakeProducer()

    class _FakeConsumerFactory:
        @staticmethod
        def from_confluent(*_args, **_kwargs):
            return _FakeConsumer()

    monkeypatch.setattr(main_module.Settings, "from_env", lambda: _Settings())
    monkeypatch.setattr(main_module, "SchemaRegistryClient", _FakeRegistryClient)
    monkeypatch.setattr(main_module, "load_schema", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(main_module, "KafkaProducerWrapper", _FakeProducerFactory)
    monkeypatch.setattr(main_module, "KafkaConsumerWrapper", _FakeConsumerFactory)
    monkeypatch.setattr(main_module, "IndexTTS2Synthesizer", lambda *_args, **_kwargs: _FakeSynthesizer())
    monkeypatch.setattr(main_module, "ObjectStorage", lambda *_args, **_kwargs: _FakeStorage())

    main_module.main()
