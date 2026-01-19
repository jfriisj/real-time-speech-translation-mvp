from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import json
import math
import struct
import time
from typing import List

import websockets


@dataclass
class RunConfig:
    ws_url: str
    clients: int
    sample_rate_hz: int
    duration_seconds: float
    hold_seconds: float
    max_connections: int


def _parse_args() -> RunConfig:
    parser = argparse.ArgumentParser(description="Gateway concurrent connection load test")
    parser.add_argument("--ws-url", default="ws://127.0.0.1:8000/ws/audio")
    parser.add_argument("--clients", type=int, default=12)
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--duration", type=float, default=0.2)
    parser.add_argument("--hold", type=float, default=1.0)
    parser.add_argument("--max-connections", type=int, default=10)
    args = parser.parse_args()
    return RunConfig(
        ws_url=args.ws_url,
        clients=args.clients,
        sample_rate_hz=args.sample_rate,
        duration_seconds=args.duration,
        hold_seconds=args.hold,
        max_connections=args.max_connections,
    )


def _make_pcm_bytes(sample_rate: int, seconds: float) -> bytes:
    n_samples = int(sample_rate * seconds)
    frames = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        value = int(32767 * 0.2 * math.sin(2 * math.pi * 440.0 * t))
        frames += struct.pack("<h", value)
    return bytes(frames)


async def _client_task(config: RunConfig, pcm_bytes: bytes) -> bool:
    try:
        async with websockets.connect(config.ws_url) as websocket:
            handshake = await websocket.recv()
            payload = json.loads(handshake)
            if not payload.get("correlation_id"):
                return False
            await asyncio.sleep(config.hold_seconds)
            midpoint = len(pcm_bytes) // 2
            await websocket.send(pcm_bytes[:midpoint])
            await websocket.send(pcm_bytes[midpoint:])
            await websocket.send('{"event":"done"}')
            await websocket.wait_closed()
            return True
    except Exception:
        return False


async def _run(config: RunConfig) -> List[bool]:
    pcm_bytes = _make_pcm_bytes(config.sample_rate_hz, config.duration_seconds)
    tasks = [_client_task(config, pcm_bytes) for _ in range(config.clients)]
    return await asyncio.gather(*tasks)


def main() -> int:
    config = _parse_args()
    start = time.time()
    results = asyncio.run(_run(config))
    elapsed = time.time() - start
    success_count = sum(1 for value in results if value)
    failure_count = len(results) - success_count
    print(
        "Load test complete: total=%s success=%s failures=%s elapsed=%.2fs"
        % (len(results), success_count, failure_count, elapsed)
    )
    if success_count > config.max_connections:
        raise SystemExit("FAIL: accepted more than max_connections")
    if success_count < min(config.max_connections, config.clients):
        raise SystemExit("FAIL: fewer successful connections than expected")
    print("PASS: concurrency limit respected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
