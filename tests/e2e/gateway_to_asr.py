from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
import json
import math
from pathlib import Path
import struct
import time
from typing import Optional

import websockets

from speech_lib import (
    KafkaConsumerWrapper,
    SchemaRegistryClient,
    TOPIC_ASR_TEXT,
    load_schema,
)


@dataclass
class RunConfig:
    ws_url: str
    bootstrap_servers: str
    schema_registry_url: str
    schema_dir: Path
    timeout_seconds: float
    sample_rate_hz: int
    duration_seconds: float


def _parse_args() -> RunConfig:
    parser = argparse.ArgumentParser(description="Gateway WebSocket → ASR validation")
    parser.add_argument("--ws-url", default="ws://127.0.0.1:8000/ws/audio")
    parser.add_argument("--bootstrap", default="127.0.0.1:29092")
    parser.add_argument("--schema-registry", default="http://127.0.0.1:8081")
    parser.add_argument("--schema-dir", default="")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--duration", type=float, default=0.5)
    args = parser.parse_args()

    schema_dir = Path(args.schema_dir) if args.schema_dir else None
    if schema_dir is None:
        schema_dir = Path(__file__).resolve().parents[2] / "shared" / "schemas" / "avro"

    return RunConfig(
        ws_url=args.ws_url,
        bootstrap_servers=args.bootstrap,
        schema_registry_url=args.schema_registry,
        schema_dir=schema_dir,
        timeout_seconds=args.timeout,
        sample_rate_hz=args.sample_rate,
        duration_seconds=args.duration,
    )


def _make_pcm_bytes(sample_rate: int, seconds: float) -> bytes:
    n_samples = int(sample_rate * seconds)
    frames = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        value = int(32767 * 0.2 * math.sin(2 * math.pi * 440.0 * t))
        frames += struct.pack("<h", value)
    return bytes(frames)


def _register_schema(config: RunConfig) -> tuple[dict, SchemaRegistryClient]:
    schema = load_schema("TextRecognizedEvent.avsc", schema_dir=config.schema_dir)
    registry = SchemaRegistryClient(config.schema_registry_url)
    registry.register_schema(f"{TOPIC_ASR_TEXT}-value", schema)
    return schema, registry


def _parse_correlation_id(handshake: str) -> Optional[str]:
    payload = json.loads(handshake)
    return payload.get("correlation_id")


async def _send_stream(config: RunConfig) -> str:
    pcm_bytes = _make_pcm_bytes(config.sample_rate_hz, config.duration_seconds)
    async with websockets.connect(config.ws_url) as websocket:
        handshake = await websocket.recv()
        correlation_id = _parse_correlation_id(handshake)
        if not correlation_id:
            raise AssertionError("Handshake missing correlation_id")
        midpoint = len(pcm_bytes) // 2
        await websocket.send(pcm_bytes[:midpoint])
        await websocket.send(pcm_bytes[midpoint:])
        await websocket.send('{"event":"done"}')
        await websocket.wait_closed()
        return correlation_id


def _await_asr_event(
    consumer: KafkaConsumerWrapper,
    schema: dict,
    correlation_id: str,
    timeout_seconds: float,
) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        event = consumer.poll(schema, timeout=0.5)
        if event is None:
            continue
        if event.get("correlation_id") != correlation_id:
            continue
        payload = event.get("payload") or {}
        text = str(payload.get("text", ""))
        if not text:
            raise AssertionError("ASR produced empty text")
        return
    raise TimeoutError("Timed out waiting for TextRecognizedEvent")


def main() -> int:
    config = _parse_args()
    schema, registry = _register_schema(config)
    consumer = KafkaConsumerWrapper.from_confluent(
        config.bootstrap_servers,
        group_id=f"gateway-asr-qa-{int(time.time())}",
        topics=[TOPIC_ASR_TEXT],
        config={"enable.auto.commit": False},
        schema_registry=registry,
    )
    consumer.poll(schema, timeout=0.1)
    correlation_id = asyncio.run(_send_stream(config))
    _await_asr_event(consumer, schema, correlation_id, config.timeout_seconds)
    print("PASS: WebSocket ingress produced TextRecognizedEvent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
