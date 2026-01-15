from __future__ import annotations

from io import BytesIO
import math
import os
import struct
import time
import wave

import numpy as np

from asr_service.transcriber import Transcriber
from asr_service.processing import decode_wav


def _generate_wav_bytes(sample_rate: int, seconds: float) -> bytes:
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


def main() -> None:
    seconds = float(os.getenv("BENCH_SECONDS", "45"))
    model_name = os.getenv("MODEL_NAME", "openai/whisper-tiny")
    sample_rate = int(os.getenv("SAMPLE_RATE_HZ", "16000"))

    audio_bytes = _generate_wav_bytes(sample_rate, seconds)
    audio, effective_rate = decode_wav(audio_bytes, sample_rate)

    transcriber = Transcriber(model_name)
    start = time.perf_counter()
    result = transcriber.transcribe(np.asarray(audio), effective_rate)
    duration = time.perf_counter() - start

    text = str(result.get("text", "")).strip()
    print(f"model={model_name}")
    print(f"duration_seconds={seconds}")
    print(f"inference_seconds={duration:.2f}")
    print(f"text_preview={text[:80]}")


if __name__ == "__main__":
    main()
