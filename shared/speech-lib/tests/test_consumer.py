from __future__ import annotations

from typing import Any, List
import sys
import types

from speech_lib.consumer import KafkaConsumerWrapper
from speech_lib.events import BaseEvent
from speech_lib.serialization import load_schema, serialize_event


class _FakeMessage:
    def __init__(self, payload: bytes, error_value: Any = None) -> None:
        self._payload = payload
        self._error = error_value

    def value(self) -> bytes:
        return self._payload

    def error(self) -> Any:
        return self._error


class _FakeConsumer:
    def __init__(self, messages: List[_FakeMessage]) -> None:
        self._messages = list(messages)
        self.commit_args: tuple[Any, bool] | None = None

    def poll(self, timeout: float = 1.0) -> _FakeMessage | None:
        if self._messages:
            return self._messages.pop(0)
        return None

    def commit(self, message: Any = None, asynchronous: bool = False) -> None:
        self.commit_args = (message, asynchronous)


def _build_event_bytes() -> bytes:
    schema = load_schema("TextRecognizedEvent.avsc")
    event = BaseEvent(
        event_type="TextRecognizedEvent",
        correlation_id="corr-123",
        source_service="test",
        payload={
            "text": "hello",
            "language": "en",
            "confidence": 0.9,
        },
    )
    return serialize_event(schema, event.to_dict())


def test_poll_with_message_returns_event_and_message() -> None:
    raw = _build_event_bytes()
    message = _FakeMessage(raw)
    consumer = _FakeConsumer([message])
    wrapper = KafkaConsumerWrapper(consumer=consumer)

    schema = load_schema("TextRecognizedEvent.avsc")
    result = wrapper.poll_with_message(schema, timeout=0.1)

    assert result is not None
    event, returned_message = result
    assert returned_message is message
    assert event["correlation_id"] == "corr-123"
    assert event["payload"]["text"] == "hello"


def test_poll_with_message_returns_none_on_error() -> None:
    raw = _build_event_bytes()
    message = _FakeMessage(raw, error_value="error")
    consumer = _FakeConsumer([message])
    wrapper = KafkaConsumerWrapper(consumer=consumer)

    schema = load_schema("TextRecognizedEvent.avsc")
    assert wrapper.poll_with_message(schema, timeout=0.1) is None


def test_commit_message_commits_sync() -> None:
    consumer = _FakeConsumer([])
    wrapper = KafkaConsumerWrapper(consumer=consumer)

    wrapper.commit_message("msg-1")
    assert consumer.commit_args == ("msg-1", False)


def test_from_confluent_passes_on_assign(monkeypatch: Any) -> None:
    class _StubConsumer:
        def __init__(self, config: dict) -> None:
            self.config = config
            self.subscribed: tuple[list[str], Any] | None = None

        def subscribe(self, topics: list[str], on_assign: Any = None) -> None:
            self.subscribed = (topics, on_assign)

    stub_module = types.SimpleNamespace(Consumer=_StubConsumer)
    monkeypatch.setitem(sys.modules, "confluent_kafka", stub_module)

    def _on_assign(_consumer: Any, _partitions: list[Any]) -> None:
        return None

    wrapper = KafkaConsumerWrapper.from_confluent(
        "localhost:9092",
        "group-1",
        ["topic-1"],
        on_assign=_on_assign,
    )

    assert wrapper.consumer.subscribed == (["topic-1"], _on_assign)