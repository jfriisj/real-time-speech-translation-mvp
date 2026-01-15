from speech_lib.events import BaseEvent
from speech_lib.serialization import deserialize_event, load_schema, serialize_event


def test_round_trip_serialization():
    schema = load_schema("TextTranslatedEvent.avsc")
    event = BaseEvent(
        event_type="TextTranslatedEvent",
        correlation_id="corr-456",
        source_service="translation",
        payload={
            "text": "hola",
            "source_language": "en",
            "target_language": "es",
            "quality_score": 0.95,
        },
    )

    raw = serialize_event(schema, event.to_dict())
    decoded = deserialize_event(schema, raw)
    assert decoded["payload"]["text"] == "hola"
    assert decoded["payload"]["target_language"] == "es"
