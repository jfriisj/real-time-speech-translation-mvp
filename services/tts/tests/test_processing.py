from __future__ import annotations

import pytest

from tts_service.processing import (
    build_audio_payload,
    build_output_event,
    enforce_text_limit,
    extract_translation_request,
    select_audio_transport,
)


class DummyStorage:
    def __init__(self) -> None:
        self.calls = []

    def upload_bytes(self, *, key: str, data: bytes, content_type: str, return_key: bool = False) -> str:
        self.calls.append((key, len(data), content_type, return_key))
        if return_key:
            return f"s3://tts-audio/{key}"
        return "http://minio.local/presigned"


def test_extract_translation_request_requires_correlation_id() -> None:
    with pytest.raises(ValueError):
        extract_translation_request({"payload": {"text": "hello"}})


def test_extract_translation_request_requires_text() -> None:
    with pytest.raises(ValueError):
        extract_translation_request({"correlation_id": "corr-1", "payload": {}})


def test_enforce_text_limit_raises_on_overflow() -> None:
    with pytest.raises(ValueError):
        enforce_text_limit("a" * 501, 500)


def test_select_audio_transport_inline() -> None:
    audio_bytes, audio_uri, mode = select_audio_transport(
        audio_bytes=b"x" * 10,
        inline_limit_bytes=100,
        disable_storage=False,
        storage=None,
        audio_uri_mode="internal",
    )
    assert audio_bytes is not None
    assert audio_uri is None
    assert mode == "inline"


def test_select_audio_transport_requires_storage() -> None:
    with pytest.raises(ValueError):
        select_audio_transport(
            audio_bytes=b"x" * 200,
            inline_limit_bytes=100,
            disable_storage=True,
            storage=None,
            audio_uri_mode="internal",
        )


def test_select_audio_transport_uploads_when_configured() -> None:
    storage = DummyStorage()
    audio_bytes, audio_uri, mode = select_audio_transport(
        audio_bytes=b"x" * 200,
        inline_limit_bytes=100,
        disable_storage=False,
        storage=storage,
        audio_uri_mode="internal",
    )
    assert audio_bytes is None
    assert audio_uri == "s3://tts-audio/" + storage.calls[0][0]
    assert mode == "uri"


def test_build_output_event_includes_speaker_context() -> None:
    payload = build_audio_payload(
        audio_bytes=b"x",
        audio_uri=None,
        duration_ms=100,
        sample_rate_hz=16000,
        model_name="kokoro",
        speaker_reference_bytes=b"\x01\x02",
        speaker_id="speaker-1",
        text_snippet="hello",
    )
    event = build_output_event(correlation_id="corr-1", payload=payload)
    data = event.to_dict()
    assert data["payload"]["speaker_reference_bytes"] == b"\x01\x02"
    assert data["payload"]["speaker_id"] == "speaker-1"
    assert data["payload"]["text_snippet"] == "hello"
