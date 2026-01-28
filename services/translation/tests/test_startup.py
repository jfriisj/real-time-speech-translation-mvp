import pytest

from translation_service import startup


def test_parse_kafka_bootstrap_plain() -> None:
    host, port = startup._parse_kafka_bootstrap("kafka:9092")
    assert host == "kafka"
    assert port == 9092


def test_parse_kafka_bootstrap_with_scheme() -> None:
    host, port = startup._parse_kafka_bootstrap("PLAINTEXT://kafka:19092")
    assert host == "kafka"
    assert port == 19092


def test_sanitize_url_strips_credentials() -> None:
    safe = startup._sanitize_url("http://user:pass@schema-registry:8081")
    assert safe == "schema-registry:8081"


def test_wait_for_kafka_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("no broker")

    monkeypatch.setattr(startup.socket, "create_connection", lambda *_a, **_k: fail())
    with pytest.raises(SystemExit):
        startup.wait_for_kafka(
            host="localhost",
            port=9092,
            max_wait_seconds=0,
            initial_backoff_seconds=0,
            max_backoff_seconds=0,
            attempt_timeout_seconds=0.01,
        )


def test_wait_for_schema_registry_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise startup.URLError("no registry")

    monkeypatch.setattr(startup, "urlopen", fail)
    with pytest.raises(SystemExit):
        startup.wait_for_schema_registry(
            registry_url="http://user:pass@localhost:8081",
            max_wait_seconds=0,
            initial_backoff_seconds=0,
            max_backoff_seconds=0,
            attempt_timeout_seconds=0.01,
        )
