from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
import time
from typing import Deque


@dataclass
class BufferAccumulator:
    max_bytes: int
    _buffer: bytearray = field(default_factory=bytearray)

    def add_chunk(self, chunk: bytes) -> None:
        if not chunk:
            return
        if len(self._buffer) + len(chunk) > self.max_bytes:
            raise ValueError("buffer exceeded max_bytes")
        self._buffer.extend(chunk)

    @property
    def size(self) -> int:
        return len(self._buffer)

    def to_bytes(self) -> bytes:
        return bytes(self._buffer)


@dataclass
class RateLimiter:
    max_messages_per_second: int
    window_seconds: float = 1.0
    _events: Deque[float] = field(default_factory=deque)

    def allow(self) -> bool:
        if self.max_messages_per_second <= 0:
            return True
        now = time.monotonic()
        cutoff = now - self.window_seconds
        while self._events and self._events[0] < cutoff:
            self._events.popleft()
        if len(self._events) >= self.max_messages_per_second:
            return False
        self._events.append(now)
        return True


@dataclass
class ConnectionLimiter:
    max_connections: int
    _active: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def acquire(self) -> bool:
        async with self._lock:
            if self.max_connections <= 0:
                return False
            if self._active >= self.max_connections:
                return False
            self._active += 1
            return True

    async def release(self) -> None:
        async with self._lock:
            self._active = max(0, self._active - 1)

    @property
    def active(self) -> int:
        return self._active
