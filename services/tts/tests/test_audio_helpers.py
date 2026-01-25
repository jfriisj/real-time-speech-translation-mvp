from __future__ import annotations

import numpy as np

from tts_service.audio import decode_wav_bytes, encode_wav_bytes


def test_encode_decode_wav_round_trip() -> None:
    audio = np.zeros(1600, dtype=np.float32)
    audio[0:10] = 0.5
    sample_rate = 16000

    encoded = encode_wav_bytes(audio, sample_rate)
    decoded, decoded_rate = decode_wav_bytes(encoded)

    assert decoded_rate == sample_rate
    assert decoded.dtype == np.float32
    assert decoded.shape[0] > 0
