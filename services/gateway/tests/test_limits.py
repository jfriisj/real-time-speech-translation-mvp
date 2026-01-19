import asyncio

import pytest

from gateway_service.limits import BufferAccumulator, ConnectionLimiter, RateLimiter


def test_buffer_accumulator_enforces_max_bytes() -> None:
    buffer = BufferAccumulator(max_bytes=4)
    buffer.add_chunk(b"ab")
    buffer.add_chunk(b"cd")
    assert buffer.size == 4
    with pytest.raises(ValueError):
        buffer.add_chunk(b"e")


def test_rate_limiter_allows_within_limit() -> None:
    limiter = RateLimiter(max_messages_per_second=2, window_seconds=10.0)
    assert limiter.allow() is True
    assert limiter.allow() is True
    assert limiter.allow() is False


def test_connection_limiter_enforces_max() -> None:
    async def _exercise() -> None:
        limiter = ConnectionLimiter(max_connections=1)
        assert await limiter.acquire() is True
        assert await limiter.acquire() is False
        await limiter.release()
        assert await limiter.acquire() is True

    asyncio.run(_exercise())
