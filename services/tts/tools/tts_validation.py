from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Iterable
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = REPO_ROOT / "services" / "tts" / "src"
SPEECH_LIB_PATH = REPO_ROOT / "shared" / "speech-lib" / "src"
for path in (SRC_PATH, SPEECH_LIB_PATH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from tts_service.synthesizer_factory import SynthesizerFactory  # noqa: E402
from tts_service import main as tts_main  # noqa: E402
DEFAULT_PHRASES_PATH = REPO_ROOT / "tests" / "data" / "metrics" / "tts_phrases.json"
DEFAULT_VALIDATION_DIR = REPO_ROOT / "agent-output" / "validation"


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return values_sorted[f]
    d0 = values_sorted[f] * (c - k)
    d1 = values_sorted[c] * (k - f)
    return d0 + d1


def _load_phrases(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("phrases JSON must be a list")
    return data


def _write_samples(phrases: Iterable[dict[str, str]], output_dir: Path, sample_count: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    synthesizer = SynthesizerFactory.create()
    os.environ.setdefault("TTS_SPEED", "1.0")

    for phrase in list(phrases)[:sample_count]:
        phrase_id = phrase.get("id", "sample")
        text = phrase.get("text", "")
        if not text:
            continue
        audio_bytes, _, _ = synthesizer.synthesize(text, None, None)
        sample_path = output_dir / f"{phrase_id}.wav"
        sample_path.write_bytes(audio_bytes)


def _measure_performance(
    phrases: Iterable[dict[str, str]],
    iterations: int,
) -> tuple[list[float], list[float]]:
    os.environ.setdefault("TTS_SPEED", "1.0")
    synthesizer = SynthesizerFactory.create()
    latency_ms: list[float] = []
    rtf: list[float] = []

    for _ in range(iterations):
        for phrase in phrases:
            text = phrase.get("text", "")
            if not text:
                continue
            start = perf_counter()
            _audio_bytes, _sample_rate, duration_ms = synthesizer.synthesize(text, None, None)
            elapsed_ms = (perf_counter() - start) * 1000
            latency_ms.append(elapsed_ms)
            if duration_ms > 0:
                rtf.append(elapsed_ms / duration_ms)

    return latency_ms, rtf


class _NullProducer:
    def publish_event(self, *_args, **_kwargs) -> None:
        return None


class _NullStorage:
    def upload_bytes(self, *, key: str, data: bytes, content_type: str) -> str:
        _ = key, data, content_type
        return "http://example.invalid/tts-audio/placeholder.wav"


def _measure_service_latency(
    phrases: Iterable[dict[str, str]],
    iterations: int,
    inline_max_bytes: int,
    model_name: str,
) -> list[float]:
    os.environ.setdefault("TTS_SPEED", "1.0")
    synthesizer = SynthesizerFactory.create()
    storage = _NullStorage()
    producer = _NullProducer()
    service_latency_ms: list[float] = []

    for _ in range(iterations):
        for phrase in phrases:
            text = phrase.get("text", "")
            if not text:
                continue
            event = {
                "correlation_id": f"tts-validation-{uuid4()}",
                "payload": {"text": text},
            }
            start = perf_counter()
            tts_main.process_event(
                event=event,
                synthesizer=synthesizer,
                storage=storage,
                producer=producer,
                output_schema={},
                inline_max_bytes=inline_max_bytes,
                model_name=model_name,
            )
            service_latency_ms.append((perf_counter() - start) * 1000)

    return service_latency_ms


def _measure_speed_shift(phrase: dict[str, str], speed_a: float, speed_b: float) -> dict[str, float]:
    synthesizer = SynthesizerFactory.create()
    text = phrase.get("text", "")
    if not text:
        raise ValueError("phrase text missing for speed check")

    def _duration_at(speed: float) -> int:
        os.environ["TTS_SPEED"] = str(speed)
        _audio_bytes, _sample_rate, duration_ms = synthesizer.synthesize(text, None, None)
        return duration_ms

    duration_a = _duration_at(speed_a)
    duration_b = _duration_at(speed_b)
    delta = ((duration_b - duration_a) / duration_a) if duration_a else 0.0
    return {
        "duration_a_ms": float(duration_a),
        "duration_b_ms": float(duration_b),
        "delta": delta,
    }


def _write_report(
    *,
    output_path: Path,
    phrases_path: Path,
    latency_ms: list[float],
    service_latency_ms: list[float],
    rtf: list[float],
    speed_results: dict[str, float],
    iterations: int,
    speed_a: float,
    speed_b: float,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = [
        "# TTS Validation Performance Report",
        "",
        f"Phrases source: {phrases_path}",
        f"Iterations per phrase: {iterations}",
        "",
        "## Latency (Synthesis Only)",
        f"- P50: {median(latency_ms):.2f} ms",
        f"- P95: {_percentile(latency_ms, 95):.2f} ms",
        "",
        "## Latency (Service, process_event inline)",
        f"- P50: {median(service_latency_ms):.2f} ms",
        f"- P95: {_percentile(service_latency_ms, 95):.2f} ms",
        "",
        "## Real-Time Factor (RTF)",
        f"- Mean RTF: {sum(rtf) / len(rtf):.3f}" if rtf else "- Mean RTF: n/a",
        f"- P50 RTF: {median(rtf):.3f}" if rtf else "- P50 RTF: n/a",
        "",
        "## Speed Control",
        f"- Speed A: {speed_a}",
        f"- Speed B: {speed_b}",
        f"- Duration A: {speed_results['duration_a_ms']:.2f} ms",
        f"- Duration B: {speed_results['duration_b_ms']:.2f} ms",
        f"- Delta: {speed_results['delta'] * 100:.2f}%",
        "",
        "## Notes",
        "- Synthesis latency reflects local inference time only.",
        "- Service latency uses process_event with an in-process producer and inline payloads (no Kafka/MinIO).",
    ]
    output_path.write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TTS validation samples and metrics.")
    parser.add_argument("--phrases", type=Path, default=DEFAULT_PHRASES_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_VALIDATION_DIR)
    parser.add_argument("--sample-count", type=int, default=5)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--speed-a", type=float, default=1.0)
    parser.add_argument("--speed-b", type=float, default=1.2)
    args = parser.parse_args()

    phrases = _load_phrases(args.phrases)
    _write_samples(phrases, args.out_dir / "samples", args.sample_count)

    latency_ms, rtf = _measure_performance(phrases, args.iterations)

    service_latency_ms = _measure_service_latency(
        phrases,
        args.iterations,
        inline_max_bytes=int(os.getenv("INLINE_PAYLOAD_MAX_BYTES", str(int(1.5 * 1024 * 1024)))),
        model_name=os.getenv("TTS_MODEL_NAME", "kokoro-82m-onnx"),
    )

    speed_results = _measure_speed_shift(phrases[0], args.speed_a, args.speed_b)
    _write_report(
        output_path=args.out_dir / "performance_report.md",
        phrases_path=args.phrases,
        latency_ms=latency_ms,
        service_latency_ms=service_latency_ms,
        rtf=rtf,
        speed_results=speed_results,
        iterations=args.iterations,
        speed_a=args.speed_a,
        speed_b=args.speed_b,
    )


if __name__ == "__main__":
    main()
