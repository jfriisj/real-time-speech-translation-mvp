from __future__ import annotations

from io import BytesIO

import numpy as np
import soundfile as sf


def encode_wav(audio: np.ndarray, sample_rate_hz: int) -> bytes:
    buffer = BytesIO()
    sf.write(buffer, audio, sample_rate_hz, format="WAV")
    return buffer.getvalue()


def apply_speed(audio: np.ndarray, speed: float) -> np.ndarray:
    if speed <= 0:
        raise ValueError("TTS_SPEED must be positive")
    if speed == 1.0 or audio.size == 0:
        return audio

    target_length = max(1, int(len(audio) / speed))
    xp = np.arange(len(audio))
    x = np.linspace(0, len(audio) - 1, target_length)
    return np.interp(x, xp, audio).astype(np.float32)
