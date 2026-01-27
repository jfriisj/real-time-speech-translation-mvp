from __future__ import annotations

from tts_service import main as tts_main


class DummyMessage:
    def __init__(self, headers):
        self._headers = headers

    def headers(self):
        return self._headers


def test_extract_traceparent_bytes() -> None:
    message = DummyMessage([("traceparent", b"00-abc"), ("other", b"x")])
    assert tts_main._extract_traceparent(message) == "00-abc"


def test_extract_traceparent_str() -> None:
    message = DummyMessage([("traceparent", "00-xyz")])
    assert tts_main._extract_traceparent(message) == "00-xyz"


def test_extract_traceparent_missing() -> None:
    message = DummyMessage([("other", b"x")])
    assert tts_main._extract_traceparent(message) is None