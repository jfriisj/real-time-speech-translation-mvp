import pytest

from speech_lib.claim_check import select_transport_mode


def test_select_transport_mode_inline() -> None:
    decision = select_transport_mode(payload_size_bytes=10, threshold_bytes=100)
    assert decision.mode == "inline"


def test_select_transport_mode_uri_when_over_threshold() -> None:
    decision = select_transport_mode(payload_size_bytes=200, threshold_bytes=100)
    assert decision.mode == "uri"


def test_select_transport_mode_force_uri() -> None:
    decision = select_transport_mode(payload_size_bytes=10, threshold_bytes=100, force_uri=True)
    assert decision.mode == "uri"


def test_select_transport_mode_rejects_invalid_threshold() -> None:
    with pytest.raises(ValueError):
        select_transport_mode(payload_size_bytes=10, threshold_bytes=0)
