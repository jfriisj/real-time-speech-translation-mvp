from __future__ import annotations

from pathlib import Path

import pytest

from tts_service import synthesizer_kokoro
from tts_service.synthesizer_factory import SynthesizerFactory


def test_kokoro_synthesizer_downloads_assets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    model_path = tmp_path / "kokoro.onnx"
    voices_path = tmp_path / "af_bella.bin"
    model_path.write_bytes(b"fake-onnx")
    voices_path.write_bytes(b"fake-voices")

    def _fake_download(*_args, **_kwargs):
        filename = _kwargs.get("filename")
        if filename == synthesizer_kokoro.MODEL_FILENAME:
            return str(model_path)
        return str(voices_path)

    monkeypatch.setattr(synthesizer_kokoro, "hf_hub_download", _fake_download)

    synthesizer = synthesizer_kokoro.KokoroSynthesizer()
    audio_bytes, sample_rate, duration_ms = synthesizer.synthesize("hello", None, "af_bella")

    assert isinstance(audio_bytes, (bytes, bytearray))
    assert sample_rate == 24000
    assert duration_ms > 0


def test_factory_selects_kokoro(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeSynthesizer:
        pass

    monkeypatch.setenv("TTS_MODEL_NAME", "kokoro")
    monkeypatch.setattr(synthesizer_kokoro, "KokoroSynthesizer", lambda: _FakeSynthesizer())

    synthesizer = SynthesizerFactory.create()
    assert isinstance(synthesizer, _FakeSynthesizer)
