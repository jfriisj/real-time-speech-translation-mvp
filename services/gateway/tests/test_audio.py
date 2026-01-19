import io
import wave

from gateway_service.audio import pcm_to_wav


def test_pcm_to_wav_produces_valid_header() -> None:
    pcm = b"\x00\x00" * 100
    wav_bytes = pcm_to_wav(pcm, sample_rate_hz=16000)
    assert wav_bytes[:4] == b"RIFF"

    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getframerate() == 16000
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
