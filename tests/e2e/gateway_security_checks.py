from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import json
from typing import Optional

import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatus


@dataclass
class RunConfig:
    ws_url: str
    allowed_origin: str
    disallowed_origin: str
    idle_timeout_seconds: float
    max_chunk_bytes: int


def _parse_args() -> RunConfig:
    parser = argparse.ArgumentParser(description="Gateway security control checks")
    parser.add_argument("--ws-url", default="ws://127.0.0.1:8000/ws/audio")
    parser.add_argument("--allowed-origin", default="http://allowed")
    parser.add_argument("--disallowed-origin", default="http://blocked")
    parser.add_argument("--idle-timeout", type=float, default=2.0)
    parser.add_argument("--max-chunk", type=int, default=1024)
    args = parser.parse_args()
    return RunConfig(
        ws_url=args.ws_url,
        allowed_origin=args.allowed_origin,
        disallowed_origin=args.disallowed_origin,
        idle_timeout_seconds=args.idle_timeout,
        max_chunk_bytes=args.max_chunk,
    )


def _parse_correlation_id(message: str) -> Optional[str]:
    payload = json.loads(message)
    return payload.get("correlation_id")


async def _expect_origin_block(config: RunConfig) -> None:
    try:
        async with websockets.connect(
            config.ws_url,
            additional_headers={"Origin": config.disallowed_origin},
        ):
            raise AssertionError("Expected origin to be blocked")
    except (ConnectionClosed, InvalidStatus):
        return


async def _expect_oversized_chunk_rejected(config: RunConfig) -> None:
    oversize = b"0" * (config.max_chunk_bytes + 1)
    async with websockets.connect(
        config.ws_url,
        additional_headers={"Origin": config.allowed_origin},
    ) as websocket:
        handshake = await websocket.recv()
        if not _parse_correlation_id(handshake):
            raise AssertionError("Handshake missing correlation_id")
        await websocket.send(oversize)
        try:
            await websocket.recv()
        except ConnectionClosed:
            return
        raise AssertionError("Expected connection to close after oversized chunk")


async def _expect_idle_timeout(config: RunConfig) -> None:
    async with websockets.connect(
        config.ws_url,
        additional_headers={"Origin": config.allowed_origin},
    ) as websocket:
        handshake = await websocket.recv()
        if not _parse_correlation_id(handshake):
            raise AssertionError("Handshake missing correlation_id")
        await asyncio.sleep(config.idle_timeout_seconds + 1.0)
        try:
            await websocket.recv()
        except ConnectionClosed:
            return
        raise AssertionError("Expected idle timeout to close the connection")


async def _run(config: RunConfig) -> None:
    await _expect_origin_block(config)
    await _expect_oversized_chunk_rejected(config)
    await _expect_idle_timeout(config)


def main() -> int:
    config = _parse_args()
    asyncio.run(_run(config))
    print("PASS: origin allowlist, chunk size, and idle timeout enforced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
