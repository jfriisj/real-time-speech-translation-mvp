from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
import math
from pathlib import Path
import struct
import time
import uuid
import wave

import numpy as np

from speech_lib import (
    BaseEvent,
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    TOPIC_ASR_TEXT,
    TOPIC_AUDIO_INGRESS,
    TOPIC_TRANSLATION_TEXT,
    load_schema,
)


@dataclass
class RunConfig:
    bootstrap_servers: str
    schema_registry_url: str
    schema_dir: Path
    count: int
    warmup_discard: int
    timeout_seconds: float
    output_path: Path
    run_id: str
    sample_rate_hz: int
    duration_seconds: float


def _make_wav_bytes(sample_rate: int, seconds: float) -> bytes:
    n_samples = int(sample_rate * seconds)
    frames = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        value = int(32767 * 0.2 * math.sin(2 * math.pi * 440.0 * t))
        frames += struct.pack("<h", value)

    buffer = BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(frames)

    return buffer.getvalue()


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _to_epoch_ms(value: object) -> int:
    if isinstance(value, datetime):
        return int(value.timestamp() * 1000)
    if isinstance(value, (int, float)):
        return int(value)
    raise TypeError(f"Unsupported timestamp type: {type(value)}")


def _parse_args() -> RunConfig:
    parser = argparse.ArgumentParser(description="Measure end-to-end latency via Kafka events.")
    parser.add_argument("--count", type=int, default=100, help="Number of sequential requests")
    parser.add_argument("--warmup", type=int, default=5, help="Warmup requests to discard")
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout in seconds per request")
    parser.add_argument(
        "--output",
        type=str,
        default="latency_summary.json",
        help="Output JSON summary path",
    )
    parser.add_argument(
        "--bootstrap",
        type=str,
        default="127.0.0.1:29092",
        help="Kafka bootstrap servers",
    )
    parser.add_argument(
        "--schema-registry",
        type=str,
        default="http://127.0.0.1:8081",
        help="Schema Registry URL",
    )
    parser.add_argument(
        "--schema-dir",
        type=str,
        default="",
        help="Optional schema directory override",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Sample rate for generated WAV",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=1.0,
        help="Duration of generated WAV in seconds",
    )

    args = parser.parse_args()
    schema_dir = Path(args.schema_dir) if args.schema_dir else None
    if schema_dir is None:
        schema_dir = Path(__file__).resolve().parents[2] / "shared" / "schemas" / "avro"

    return RunConfig(
        bootstrap_servers=args.bootstrap,
        schema_registry_url=args.schema_registry,
        schema_dir=schema_dir,
        count=args.count,
        warmup_discard=args.warmup,
        timeout_seconds=args.timeout,
        output_path=Path(args.output),
        run_id=str(uuid.uuid4()),
        sample_rate_hz=args.sample_rate,
        duration_seconds=args.duration,
    )


def _register_schemas(
    config: RunConfig,
) -> tuple[dict[str, dict], dict[str, int], SchemaRegistryClient]:
    input_schema = load_schema("AudioInputEvent.avsc", schema_dir=config.schema_dir)
    asr_schema = load_schema("TextRecognizedEvent.avsc", schema_dir=config.schema_dir)
    translation_schema = load_schema("TextTranslatedEvent.avsc", schema_dir=config.schema_dir)

    registry = SchemaRegistryClient(config.schema_registry_url)
    schema_ids = {
        "input": registry.register_schema(
            f"{TOPIC_AUDIO_INGRESS}-value", input_schema
        ),
        "asr": registry.register_schema(f"{TOPIC_ASR_TEXT}-value", asr_schema),
        "translation": registry.register_schema(
            f"{TOPIC_TRANSLATION_TEXT}-value", translation_schema
        ),
    }

    schemas = {
        "input": input_schema,
        "asr": asr_schema,
        "translation": translation_schema,
    }
    return schemas, schema_ids, registry


def _percentiles(values: list[float]) -> dict[str, float]:
    if not values:
        return {"p50": 0.0, "p90": 0.0, "p99": 0.0}
    array = np.array(values, dtype=float)
    return {
        "p50": float(np.percentile(array, 50)),
        "p90": float(np.percentile(array, 90)),
        "p99": float(np.percentile(array, 99)),
    }


def main() -> int:
    config = _parse_args()
    schemas, schema_ids, registry = _register_schemas(config)

    producer = KafkaProducerWrapper.from_confluent(config.bootstrap_servers)
    asr_consumer = KafkaConsumerWrapper.from_confluent(
        config.bootstrap_servers,
        group_id=f"traceability-probe-{config.run_id}",
        topics=[TOPIC_ASR_TEXT],
        config={"auto.offset.reset": "latest", "enable.auto.commit": False},
        schema_registry=registry,
    )
    translation_consumer = KafkaConsumerWrapper.from_confluent(
        config.bootstrap_servers,
        group_id=f"traceability-probe-{config.run_id}",
        topics=[TOPIC_TRANSLATION_TEXT],
        config={"auto.offset.reset": "latest", "enable.auto.commit": False},
        schema_registry=registry,
    )

    wav_bytes = _make_wav_bytes(config.sample_rate_hz, config.duration_seconds)

    successes: list[float] = []
    failures = {"timeout": 0, "broken_chain": 0}
    warmup_failures = {"timeout": 0, "broken_chain": 0}

    def run_request(correlation_id: str, track_failures: dict[str, int]) -> float | None:
        payload = {
            "audio_bytes": wav_bytes,
            "audio_format": "wav",
            "sample_rate_hz": config.sample_rate_hz,
            "language_hint": None,
        }
        event = BaseEvent(
            event_type="AudioInputEvent",
            correlation_id=correlation_id,
            source_service="traceability-probe",
            payload=payload,
        )

        producer.publish_event(
            TOPIC_AUDIO_INGRESS,
            event,
            schemas["input"],
            schema_id=schema_ids["input"],
        )
        t0 = _to_epoch_ms(event.timestamp)
        t1 = None
        t2 = None
        deadline = time.time() + config.timeout_seconds

        while time.time() < deadline and t2 is None:
            asr_event = asr_consumer.poll(schemas["asr"], timeout=0.5)
            if asr_event and asr_event.get("correlation_id") == correlation_id:
                t1 = _to_epoch_ms(asr_event.get("timestamp"))

            translation_event = translation_consumer.poll(
                schemas["translation"], timeout=0.5
            )
            if (
                translation_event
                and translation_event.get("correlation_id") == correlation_id
            ):
                t2 = _to_epoch_ms(translation_event.get("timestamp"))

        if t2 is None:
            if t1 is None:
                track_failures["timeout"] += 1
            else:
                track_failures["broken_chain"] += 1
            return None

        return float(t2 - t0)

    for index in range(config.warmup_discard):
        correlation_id = f"traceability-{config.run_id}-warmup-{index:04d}"
        latency = run_request(correlation_id, warmup_failures)
        if latency is None:
            print(
                f"[warmup {index + 1}/{config.warmup_discard}] Timeout/broken chain"
            )
        else:
            print(
                f"[warmup {index + 1}/{config.warmup_discard}] latency_total_ms={latency:.2f}"
            )

    for index in range(config.count):
        correlation_id = f"traceability-{config.run_id}-{index:04d}"
        latency_total = run_request(correlation_id, failures)
        if latency_total is None:
            print(f"[{index + 1}/{config.count}] Timeout waiting for ASR/Translation")
            continue

        successes.append(latency_total)
        print(
            f"[{index + 1}/{config.count}] latency_total_ms={latency_total:.2f}"
        )

    percentiles = _percentiles(successes)

    summary = {
        "meta": {
            "timestamp": _utc_timestamp(),
            "run_id": config.run_id,
            "warmup_discarded": config.warmup_discard,
        },
        "counts": {
            "total": config.count,
            "success": len(successes),
            "failure": failures["timeout"] + failures["broken_chain"],
        },
        "latencies_ms": percentiles,
        "failures": failures,
    }

    config.output_path.write_text(
        __import__("json").dumps(summary, indent=2), encoding="utf-8"
    )

    print("\nSummary:")
    print(f"  Success: {summary['counts']['success']} / {summary['counts']['total']}")
    if config.warmup_discard:
        print(
            "  Warmup failures: "
            f"{warmup_failures['timeout']} timeout, "
            f"{warmup_failures['broken_chain']} broken chain"
        )
    print(
        "  P50/P90/P99 (ms): "
        f"{summary['latencies_ms']['p50']:.2f} / "
        f"{summary['latencies_ms']['p90']:.2f} / "
        f"{summary['latencies_ms']['p99']:.2f}"
    )
    print(f"  Output: {config.output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
