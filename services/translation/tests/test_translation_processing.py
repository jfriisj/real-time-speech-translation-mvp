from __future__ import annotations

import pytest

from speech_lib import TOPIC_TRANSLATION_TEXT
from translation_service.main import (
    build_output_event,
    extract_translation_request,
    process_event,
)


class _RecordingProducer:
    def __init__(self) -> None:
        self.published: list[tuple[str, object, dict]] = []

    def publish_event(self, topic: str, event: object, schema: dict) -> None:
        self.published.append((topic, event, schema))


class _Translator:
    def __init__(self, output: str) -> None:
        self._output = output

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        return self._output


def test_build_output_event_has_required_fields() -> None:
    event = build_output_event(
        correlation_id="corr-1",
        translated_text="[ES] hello",
        source_language="en",
        target_language="es",
    )
    data = event.to_dict()
    assert data["event_type"] == "TextTranslatedEvent"
    assert data["correlation_id"] == "corr-1"
    assert data["payload"]["text"] == "[ES] hello"
    assert data["payload"]["source_language"] == "en"
    assert data["payload"]["target_language"] == "es"


def test_extract_translation_request_defaults_missing_source_language() -> None:
    correlation_id, text, source_language, target_language = extract_translation_request(
        event={
            "correlation_id": "corr-2",
            "payload": {"text": "hello", "language": ""},
        },
        target_language="es",
    )

    assert correlation_id == "corr-2"
    assert text == "hello"
    assert source_language == "en"
    assert target_language == "es"


def test_process_event_requires_correlation_id() -> None:
    with pytest.raises(ValueError, match="correlation_id"):
        extract_translation_request(
            event={"payload": {"text": "hello", "language": "en"}},
            target_language="es",
        )


def test_process_event_requires_text() -> None:
    with pytest.raises(ValueError, match="payload.text"):
        extract_translation_request(
            event={"correlation_id": "corr-3", "payload": {"text": "", "language": "en"}},
            target_language="es",
        )


def test_process_event_publishes_translated_event() -> None:
    translator = _Translator("hola")
    producer = _RecordingProducer()

    process_event(
        event={
            "correlation_id": "corr-4",
            "payload": {"text": "hello", "language": "en"},
        },
        translator=translator,
        producer=producer,
        output_schema={},
        target_language="es",
    )

    assert producer.published
    topic, event, _schema = producer.published[0]
    assert topic == TOPIC_TRANSLATION_TEXT
    payload = event.to_dict()["payload"]
    assert payload["text"] == "hola"
    assert payload["source_language"] == "en"
    assert payload["target_language"] == "es"


def test_process_event_raises_on_empty_translation() -> None:
    translator = _Translator("")
    producer = _RecordingProducer()

    with pytest.raises(ValueError, match="translation result is empty"):
        process_event(
            event={
                "correlation_id": "corr-5",
                "payload": {"text": "hello", "language": "en"},
            },
            translator=translator,
            producer=producer,
            output_schema={},
            target_language="es",
        )
