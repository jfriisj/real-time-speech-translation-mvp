from gateway_service.protocol import build_handshake_message, parse_sentinel_message


def test_build_handshake_message_contains_correlation_id() -> None:
    message = build_handshake_message("abc-123")
    assert "abc-123" in message


def test_parse_sentinel_message_accepts_done_event() -> None:
    assert parse_sentinel_message('{"event": "done"}') is True


def test_parse_sentinel_message_rejects_other_events() -> None:
    assert parse_sentinel_message('{"event": "ping"}') is False


def test_parse_sentinel_message_rejects_invalid_json() -> None:
    assert parse_sentinel_message("not-json") is False
