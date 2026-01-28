from speech_lib.constants import AUDIO_PAYLOAD_MAX_BYTES
from speech_lib.correlation import correlation_context, get_correlation_id
from speech_lib.events import (
    AudioInputPayload,
    AudioSynthesisPayload,
    BaseEvent,
    SpeechSegmentPayload,
)


def test_audio_payload_size_limit():
    payload = AudioInputPayload(
        audio_bytes=b"a" * (AUDIO_PAYLOAD_MAX_BYTES + 1),
        audio_uri=None,
        audio_format="wav",
        sample_rate_hz=16000,
    )

    try:
        payload.validate()
    except ValueError as exc:
        assert "exceeds" in str(exc)
    else:  # pragma: no cover
        assert False, "Expected ValueError for oversized audio payload"


def test_base_event_requires_fields():
    event = BaseEvent(
        event_type="TextRecognizedEvent",
        correlation_id="corr-123",
        source_service="asr",
        payload={"text": "hello"},
    )

    event_dict = event.to_dict()
    assert event_dict["event_type"] == "TextRecognizedEvent"
    assert event_dict["correlation_id"] == "corr-123"
    assert event_dict["source_service"] == "asr"
    assert "event_id" in event_dict
    assert "timestamp" in event_dict


def test_speech_segment_payload_validation() -> None:
    payload = SpeechSegmentPayload(
        segment_id="segment-1",
        segment_index=0,
        start_ms=0,
        end_ms=1000,
        audio_bytes=b"\x00\x01",
        segment_uri=None,
        sample_rate_hz=16000,
        audio_format="wav",
    )

    payload.validate()

    invalid_payload = SpeechSegmentPayload(
        segment_id="",
        segment_index=-1,
        start_ms=10,
        end_ms=5,
        audio_bytes=None,
        segment_uri=None,
        sample_rate_hz=0,
        audio_format="mp3",
    )

    try:
        invalid_payload.validate()
    except ValueError:
        assert True
    else:  # pragma: no cover
        assert False, "Expected ValueError for invalid segment payload"


def test_correlation_context_sets_and_resets():
    assert get_correlation_id() is None

    with correlation_context("corr-xyz"):
        assert get_correlation_id() == "corr-xyz"

    assert get_correlation_id() is None


def test_audio_synthesis_payload_requires_exactly_one_source() -> None:
    payload = AudioSynthesisPayload(
        audio_bytes=b"\x00\x01",
        audio_uri=None,
        duration_ms=1000,
        sample_rate_hz=16000,
    )
    payload.validate()

    invalid_payload = AudioSynthesisPayload(
        audio_bytes=b"\x00",
        audio_uri="s3://bucket/key",
        duration_ms=1000,
        sample_rate_hz=16000,
    )

    try:
        invalid_payload.validate()
    except ValueError:
        assert True
    else:  # pragma: no cover
        assert False, "Expected ValueError when both audio_bytes and audio_uri are set"
