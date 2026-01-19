from __future__ import annotations

import io
import wave


def pcm_to_wav(pcm_bytes: bytes, sample_rate_hz: int, channels: int = 1) -> bytes:
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")
    if channels <= 0:
        raise ValueError("channels must be positive")

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate_hz)
        wav_file.writeframes(pcm_bytes)
    return buffer.getvalue()
