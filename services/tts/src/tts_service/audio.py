from __future__ import annotations

from io import BytesIO
from typing import Tuple

import numpy as np
import soundfile as sf


def decode_wav_bytes(audio_bytes: bytes) -> Tuple[np.ndarray, int]:
    data, sample_rate = sf.read(BytesIO(audio_bytes), dtype="float32")
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    return data, sample_rate


def encode_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    buffer = BytesIO()
    sf.write(buffer, audio, sample_rate, format="WAV")
    return buffer.getvalue()
