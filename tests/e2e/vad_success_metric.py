from __future__ import annotations

import argparse
import audioop
import json
import subprocess
import tempfile
import time
import wave
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from shutil import which
from uuid import uuid4

import numpy as np

from speech_lib import (
    BaseEvent,
    KafkaConsumerWrapper,
    KafkaProducerWrapper,
    SchemaRegistryClient,
    TOPIC_ASR_TEXT,
    TOPIC_AUDIO_INGRESS,
    TOPIC_SPEECH_SEGMENT,
    TOPIC_TRANSLATION_TEXT,
    load_schema,
)


@dataclass(frozen=True)
class RunConfig:
    mode: str
    bootstrap_servers: str
    schema_registry_url: str
    schema_dir: Path
    sample_rate_hz: int
    total_seconds: float
    max_speech_seconds: float
    samples: int
    timeout_seconds: float
    idle_seconds: float
    output_path: Path
    dataset_seed: int
    silence_ratio: float
    espeak_voice: str
    baseline_json: Path | None
    vad_json: Path | None
    wer_guardrail_pp: float


def _parse_args() -> RunConfig:
    parser = argparse.ArgumentParser(description="VAD success-metric validation")
    parser.add_argument("--mode", choices=["baseline", "vad", "compare"], required=True)
    parser.add_argument("--bootstrap", default="127.0.0.1:29092")
    parser.add_argument("--schema-registry", default="http://127.0.0.1:8081")
    parser.add_argument("--schema-dir", default="")
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--total-seconds", type=float, default=30.0)
    parser.add_argument("--max-speech-seconds", type=float, default=2.0)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--idle", type=float, default=6.0)
    parser.add_argument("--output", type=str, default="vad_metric.json")
    parser.add_argument("--dataset-seed", type=int, default=20260119)
    parser.add_argument("--silence-ratio", type=float, default=0.4)
    parser.add_argument("--espeak-voice", type=str, default="en")
    parser.add_argument("--baseline-json", type=str, default="")
    parser.add_argument("--vad-json", type=str, default="")
    parser.add_argument("--wer-guardrail-pp", type=float, default=0.05)
    args = parser.parse_args()

    schema_dir = Path(args.schema_dir) if args.schema_dir else None
    if schema_dir is None:
        schema_dir = Path(__file__).resolve().parents[2] / "shared" / "schemas" / "avro"

    return RunConfig(
        mode=args.mode,
        bootstrap_servers=args.bootstrap,
        schema_registry_url=args.schema_registry,
        schema_dir=schema_dir,
        sample_rate_hz=args.sample_rate,
        total_seconds=args.total_seconds,
        max_speech_seconds=args.max_speech_seconds,
        samples=args.samples,
        timeout_seconds=args.timeout,
        idle_seconds=args.idle,
        output_path=Path(args.output),
        dataset_seed=args.dataset_seed,
        silence_ratio=args.silence_ratio,
        espeak_voice=args.espeak_voice,
        baseline_json=Path(args.baseline_json) if args.baseline_json else None,
        vad_json=Path(args.vad_json) if args.vad_json else None,
        wer_guardrail_pp=args.wer_guardrail_pp,
    )


def _register_schemas(
    config: RunConfig,
) -> tuple[dict[str, dict], dict[str, int], SchemaRegistryClient]:
    input_schema = load_schema("AudioInputEvent.avsc", schema_dir=config.schema_dir)
    segment_schema = load_schema("SpeechSegmentEvent.avsc", schema_dir=config.schema_dir)
    asr_schema = load_schema("TextRecognizedEvent.avsc", schema_dir=config.schema_dir)
    translation_schema = load_schema("TextTranslatedEvent.avsc", schema_dir=config.schema_dir)

    registry = SchemaRegistryClient(config.schema_registry_url)
    schema_ids = {
        "input": registry.register_schema(
            f"{TOPIC_AUDIO_INGRESS}-value", input_schema
        ),
        "segment": registry.register_schema(
            f"{TOPIC_SPEECH_SEGMENT}-value", segment_schema
        ),
        "asr": registry.register_schema(f"{TOPIC_ASR_TEXT}-value", asr_schema),
        "translation": registry.register_schema(
            f"{TOPIC_TRANSLATION_TEXT}-value", translation_schema
        ),
    }

    schemas = {
        "input": input_schema,
        "segment": segment_schema,
        "asr": asr_schema,
        "translation": translation_schema,
    }
    return schemas, schema_ids, registry


def _ensure_espeak() -> None:
    if which("espeak") is None:
        raise SystemExit("espeak not found. Install espeak to synthesize reference audio.")


def _read_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        sample_rate = handle.getframerate()
        frame_count = handle.getnframes()
        frames = handle.readframes(frame_count)

    if sample_width != 2:
        raise ValueError("Expected 16-bit PCM WAV output from espeak")

    audio = np.frombuffer(frames, dtype="<i2")
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1).astype(np.int16)
    return audio, sample_rate


def _resample_int16(audio: np.ndarray, input_rate: int, target_rate: int) -> np.ndarray:
    if input_rate == target_rate:
        return audio
    converted, _ = audioop.ratecv(audio.tobytes(), 2, 1, input_rate, target_rate, None)
    return np.frombuffer(converted, dtype="<i2")


def _synthesize_speech(text: str, voice: str, sample_rate_hz: int) -> np.ndarray:
    _ensure_espeak()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        subprocess.run(
            ["espeak", f"-v{voice}", "-w", str(temp_path), text],
            check=True,
            capture_output=True,
        )
        audio, rate = _read_wav_mono(temp_path)
        if rate != sample_rate_hz:
            audio = _resample_int16(audio, rate, sample_rate_hz)
        return audio.astype(np.float32) / 32768.0
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _build_sparse_audio(
    speech_audio: np.ndarray,
    *,
    sample_rate_hz: int,
    total_seconds: float,
    max_speech_seconds: float,
    silence_ratio: float,
) -> np.ndarray:
    total_samples = int(total_seconds * sample_rate_hz)
    max_speech_samples = int(max_speech_seconds * sample_rate_hz)
    target_speech_samples = int(total_samples * max(0.0, 1.0 - silence_ratio))
    per_segment_samples = max(1, target_speech_samples // 2)
    per_segment_samples = min(per_segment_samples, max_speech_samples, speech_audio.size)
    speech_audio = speech_audio[:per_segment_samples]

    speech_total = min(total_samples, speech_audio.size * 2)
    if speech_total <= 0:
        return np.zeros(total_samples, dtype=np.float32)

    silence_samples = max(0, total_samples - speech_total)
    pre = int(silence_samples * 0.4)
    mid = int(silence_samples * 0.2)
    post = silence_samples - pre - mid

    segments = [
        np.zeros(pre, dtype=np.float32),
        speech_audio,
        np.zeros(mid, dtype=np.float32),
        speech_audio,
        np.zeros(post, dtype=np.float32),
    ]
    combined = np.concatenate(segments)
    return combined[:total_samples]


def _encode_wav(audio: np.ndarray, sample_rate_hz: int) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate_hz)
        int_samples = np.clip(audio, -1.0, 1.0)
        int_samples = (int_samples * 32767).astype(np.int16)
        handle.writeframes(int_samples.tobytes())
    return buffer.getvalue()


def _duration_seconds(audio: np.ndarray, sample_rate_hz: int) -> float:
    if sample_rate_hz <= 0:
        return 0.0
    return float(audio.size / sample_rate_hz)


def _make_dataset(config: RunConfig) -> list[dict[str, object]]:
    samples = []
    for idx in range(config.samples):
        text = f"sample {idx} voice activity detection test"
        speech_audio = _synthesize_speech(text, config.espeak_voice, config.sample_rate_hz)
        combined = _build_sparse_audio(
            speech_audio,
            sample_rate_hz=config.sample_rate_hz,
            total_seconds=config.total_seconds,
            max_speech_seconds=config.max_speech_seconds,
            silence_ratio=config.silence_ratio,
        )
        wav_bytes = _encode_wav(combined, config.sample_rate_hz)
        samples.append(
            {
                "index": idx,
                "reference_text": text,
                "audio_bytes": wav_bytes,
                "duration_seconds": _duration_seconds(combined, config.sample_rate_hz),
            }
        )
    return samples


def _await_asr_text(
    consumer: KafkaConsumerWrapper,
    schema: dict,
    correlation_id: str,
    timeout_seconds: float,
) -> str:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        event = consumer.poll(schema, timeout=0.5)
        if event is None:
            continue
        if event.get("correlation_id") != correlation_id:
            continue
        payload = event.get("payload") or {}
        return str(payload.get("text") or "").strip()
    raise TimeoutError("Timed out waiting for TextRecognizedEvent")


def _await_translation(
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
        return
    raise TimeoutError("Timed out waiting for TextTranslatedEvent")


def _collect_vad_results(
    segment_consumer: KafkaConsumerWrapper,
    asr_consumer: KafkaConsumerWrapper,
    segment_schema: dict,
    asr_schema: dict,
    correlation_id: str,
    timeout_seconds: float,
    idle_seconds: float,
) -> tuple[float, str]:
    deadline = time.time() + timeout_seconds
    last_event_time = time.time()
    segments: dict[int, tuple[int, int]] = {}
    texts: list[str] = []

    while time.time() < deadline:
        now = time.time()
        segment_event = segment_consumer.poll(segment_schema, timeout=0.2)
        if segment_event and segment_event.get("correlation_id") == correlation_id:
            payload = segment_event.get("payload") or {}
            try:
                index = int(payload.get("segment_index"))
                start_ms = int(payload.get("start_ms"))
                end_ms = int(payload.get("end_ms"))
                segments[index] = (start_ms, end_ms)
            except (TypeError, ValueError):
                pass
            last_event_time = now

        asr_event = asr_consumer.poll(asr_schema, timeout=0.2)
        if asr_event and asr_event.get("correlation_id") == correlation_id:
            payload = asr_event.get("payload") or {}
            text = str(payload.get("text") or "").strip()
            if text:
                texts.append(text)
            last_event_time = now

        if segments and (now - last_event_time) >= idle_seconds:
            break

    total_segment_ms = sum(end - start for start, end in segments.values())
    transcript = " ".join(texts).strip()
    return float(total_segment_ms) / 1000.0, transcript


def _word_error_rate(reference: str, hypothesis: str) -> float:
    ref_words = [w for w in reference.strip().split() if w]
    hyp_words = [w for w in hypothesis.strip().split() if w]
    if not ref_words:
        return 0.0

    dp = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
    for i in range(len(ref_words) + 1):
        dp[i][0] = i
    for j in range(len(hyp_words) + 1):
        dp[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    return float(dp[-1][-1]) / float(len(ref_words))


def _run_baseline(config: RunConfig) -> dict[str, object]:
    schemas, schema_ids, registry = _register_schemas(config)
    producer = KafkaProducerWrapper.from_confluent(config.bootstrap_servers)
    asr_consumer = KafkaConsumerWrapper.from_confluent(
        config.bootstrap_servers,
        group_id=f"vad-baseline-{int(time.time())}",
        topics=[TOPIC_ASR_TEXT],
        config={"enable.auto.commit": False},
        schema_registry=registry,
    )
    translation_consumer = KafkaConsumerWrapper.from_confluent(
        config.bootstrap_servers,
        group_id=f"vad-baseline-translation-{int(time.time())}",
        topics=[TOPIC_TRANSLATION_TEXT],
        config={"enable.auto.commit": False},
        schema_registry=registry,
    )
    dataset = _make_dataset(config)

    results = []
    for sample in dataset:
        correlation_id = f"baseline-{config.dataset_seed}-{sample['index']}-{uuid4().hex}"
        event = BaseEvent(
            event_type="AudioInputEvent",
            correlation_id=correlation_id,
            source_service="vad-metric-baseline",
            payload={
                "audio_bytes": sample["audio_bytes"],
                "audio_format": "wav",
                "sample_rate_hz": config.sample_rate_hz,
                "language_hint": "en",
            },
        )
        producer.publish_event(
            TOPIC_AUDIO_INGRESS,
            event,
            schemas["input"],
            schema_id=schema_ids["input"],
        )
        text = _await_asr_text(asr_consumer, schemas["asr"], correlation_id, config.timeout_seconds)
        _await_translation(
            translation_consumer,
            schemas["translation"],
            correlation_id,
            config.timeout_seconds,
        )
        results.append(
            {
                "index": sample["index"],
                "reference_text": sample["reference_text"],
                "duration_seconds": sample["duration_seconds"],
                "transcript": text,
            }
        )

    return {
        "mode": "baseline",
        "meta": {
            "dataset_seed": config.dataset_seed,
            "samples": config.samples,
            "total_seconds": config.total_seconds,
            "sample_rate_hz": config.sample_rate_hz,
            "silence_ratio": config.silence_ratio,
        },
        "samples": results,
    }


def _run_vad(config: RunConfig) -> dict[str, object]:
    schemas, schema_ids, registry = _register_schemas(config)
    producer = KafkaProducerWrapper.from_confluent(config.bootstrap_servers)
    segment_consumer = KafkaConsumerWrapper.from_confluent(
        config.bootstrap_servers,
        group_id=f"vad-segment-metric-{int(time.time())}",
        topics=[TOPIC_SPEECH_SEGMENT],
        config={"enable.auto.commit": False},
        schema_registry=registry,
    )
    asr_consumer = KafkaConsumerWrapper.from_confluent(
        config.bootstrap_servers,
        group_id=f"vad-asr-metric-{int(time.time())}",
        topics=[TOPIC_ASR_TEXT],
        config={"enable.auto.commit": False},
        schema_registry=registry,
    )

    dataset = _make_dataset(config)
    results = []
    for sample in dataset:
        correlation_id = f"vad-{config.dataset_seed}-{sample['index']}-{uuid4().hex}"
        event = BaseEvent(
            event_type="AudioInputEvent",
            correlation_id=correlation_id,
            source_service="vad-metric",
            payload={
                "audio_bytes": sample["audio_bytes"],
                "audio_format": "wav",
                "sample_rate_hz": config.sample_rate_hz,
                "language_hint": "en",
            },
        )
        producer.publish_event(
            TOPIC_AUDIO_INGRESS,
            event,
            schemas["input"],
            schema_id=schema_ids["input"],
        )
        segment_seconds, transcript = _collect_vad_results(
            segment_consumer,
            asr_consumer,
            schemas["segment"],
            schemas["asr"],
            correlation_id,
            config.timeout_seconds,
            config.idle_seconds,
        )
        results.append(
            {
                "index": sample["index"],
                "reference_text": sample["reference_text"],
                "duration_seconds": sample["duration_seconds"],
                "segment_seconds": segment_seconds,
                "transcript": transcript,
            }
        )

    return {
        "mode": "vad",
        "meta": {
            "dataset_seed": config.dataset_seed,
            "samples": config.samples,
            "total_seconds": config.total_seconds,
            "sample_rate_hz": config.sample_rate_hz,
            "silence_ratio": config.silence_ratio,
        },
        "samples": results,
    }


def _compare(baseline_path: Path, vad_path: Path) -> dict[str, object]:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    vad = json.loads(vad_path.read_text(encoding="utf-8"))

    baseline_samples = {s["index"]: s for s in baseline.get("samples", [])}
    vad_samples = {s["index"]: s for s in vad.get("samples", [])}

    reductions = []
    baseline_wers = []
    vad_wers = []
    wer_deltas = []
    skipped_wer = 0

    for index, base in baseline_samples.items():
        vad_sample = vad_samples.get(index)
        if not vad_sample:
            continue

        original = float(base.get("duration_seconds", 0.0))
        segment = float(vad_sample.get("segment_seconds", 0.0))
        if original > 0:
            reductions.append(1.0 - (segment / original))

        ref_text = str(base.get("reference_text") or vad_sample.get("reference_text") or "").strip()
        if not ref_text:
            skipped_wer += 1
            continue

        base_text = str(base.get("transcript") or "").strip()
        vad_text = str(vad_sample.get("transcript") or "").strip()
        base_wer = _word_error_rate(ref_text, base_text)
        vad_wer = _word_error_rate(ref_text, vad_text)
        baseline_wers.append(base_wer)
        vad_wers.append(vad_wer)
        wer_deltas.append(vad_wer - base_wer)

    avg_reduction = float(sum(reductions) / len(reductions)) if reductions else 0.0
    avg_baseline_wer = float(sum(baseline_wers) / len(baseline_wers)) if baseline_wers else 0.0
    avg_vad_wer = float(sum(vad_wers) / len(vad_wers)) if vad_wers else 0.0
    avg_wer_delta = float(sum(wer_deltas) / len(wer_deltas)) if wer_deltas else 0.0

    return {
        "reduction_avg": avg_reduction,
        "reduction_min": float(min(reductions)) if reductions else 0.0,
        "reduction_max": float(max(reductions)) if reductions else 0.0,
        "wer_baseline_avg": avg_baseline_wer,
        "wer_vad_avg": avg_vad_wer,
        "wer_delta_avg": avg_wer_delta,
        "wer_samples": len(wer_deltas),
        "wer_skipped": skipped_wer,
    }


def main() -> int:
    config = _parse_args()

    if config.mode == "baseline":
        result = _run_baseline(config)
        config.output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote baseline metrics to {config.output_path}")
        return 0

    if config.mode == "vad":
        result = _run_vad(config)
        config.output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote VAD metrics to {config.output_path}")
        return 0

    if not config.baseline_json or not config.vad_json:
        raise SystemExit("Provide --baseline-json and --vad-json for compare mode")

    summary = _compare(config.baseline_json, config.vad_json)
    summary_path = config.output_path
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"Wrote summary to {summary_path}")

    if summary["reduction_avg"] < 0.30:
        raise SystemExit("FAIL: reduction below 30% target")

    if summary["wer_delta_avg"] > config.wer_guardrail_pp:
        raise SystemExit(
            "FAIL: WER guardrail exceeded (avg delta {:.3f} > {:.3f})".format(
                summary["wer_delta_avg"],
                config.wer_guardrail_pp,
            )
        )

    print("PASS: success metric + WER guardrail")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
