from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from io import BytesIO
import json
import math
from pathlib import Path
import struct
import time
import wave

import websockets

from speech_lib import (
    KafkaConsumerWrapper,
    SchemaRegistryClient,
    TOPIC_AUDIO_INGRESS,
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
    parser = argparse.ArgumentParser(description="Gateway WebSocket → Kafka validation")
    parser.add_argument("--ws-url", default="ws://127.0.0.1:8000/ws/audio")
    parser.add_argument("--bootstrap", default="127.0.0.1:29092")
    parser.add_argument("--schema-registry", default="http://127.0.0.1:8081")
    parser.add_argument("--schema-dir", default="")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--duration", type=float, default=0.2)
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


def _validate_wav_bytes(wav_bytes: bytes, sample_rate_hz: int) -> None:
    with wave.open(BytesIO(wav_bytes), "rb") as handle:
        if handle.getframerate() != sample_rate_hz:
            raise AssertionError("Unexpected sample rate")
        if handle.getnchannels() != 1:
            raise AssertionError("Expected mono audio")
        if handle.getsampwidth() != 2:
            raise AssertionError("Expected 16-bit audio")


def _register_schema(config: RunConfig) -> dict:
    schema = load_schema("AudioInputEvent.avsc", schema_dir=config.schema_dir)
    registry = SchemaRegistryClient(config.schema_registry_url)
    registry.register_schema(f"{TOPIC_AUDIO_INGRESS}-value", schema)
    return schema


async def _send_stream(config: RunConfig) -> str:
    pcm_bytes = _make_pcm_bytes(config.sample_rate_hz, config.duration_seconds)
    async with websockets.connect(config.ws_url) as websocket:
        handshake = await websocket.recv()
        payload = json.loads(handshake)
        correlation_id = payload.get("correlation_id")
        if not correlation_id:
            raise AssertionError("Handshake missing correlation_id")
        midpoint = len(pcm_bytes) // 2
        await websocket.send(pcm_bytes[:midpoint])
        await websocket.send(pcm_bytes[midpoint:])
        await websocket.send('{"event":"done"}')
        await websocket.wait_closed()
        return correlation_id


def _await_kafka_event(
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
        audio_bytes = payload.get("audio_bytes")
        audio_format = payload.get("audio_format")
        sample_rate_hz = payload.get("sample_rate_hz")
        if audio_format != "wav":
            raise AssertionError("audio_format must be wav")
        if not isinstance(audio_bytes, (bytes, bytearray)) or not audio_bytes:
            raise AssertionError("audio_bytes missing")
        _validate_wav_bytes(bytes(audio_bytes), int(sample_rate_hz))
        return
    raise TimeoutError("Timed out waiting for AudioInputEvent")


def main() -> int:
    config = _parse_args()
    schema = _register_schema(config)
    consumer = KafkaConsumerWrapper.from_confluent(
        config.bootstrap_servers,
        group_id=f"gateway-qa-{int(time.time())}",
        topics=[TOPIC_AUDIO_INGRESS],
        config={"enable.auto.commit": False},
    )
    consumer.poll(schema, timeout=0.1)
    correlation_id = asyncio.run(_send_stream(config))
    _await_kafka_event(consumer, schema, correlation_id, config.timeout_seconds)
    print("PASS: WebSocket ingress produced AudioInputEvent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
