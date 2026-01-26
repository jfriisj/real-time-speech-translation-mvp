from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from tts_service import synthesizer_kokoro
from tts_service.synthesizer_factory import SynthesizerFactory


def test_kokoro_synthesizer_downloads_assets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    model_path = tmp_path / "kokoro.onnx"
    voices_path = tmp_path / "af_bella.bin"
    tokenizer_path = tmp_path / "tokenizer.json"
    model_path.write_bytes(b"fake-onnx")
    voice_vectors = np.arange(512, dtype=np.float32).reshape(2, 256)
    voice_vectors.tofile(voices_path)
    tokenizer_path.write_text('{"model": {"vocab": {"a": 1, "$": 0}}}')
    monkeypatch.setenv("TTS_MODEL_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("TTS_SPEED", "1.25")

    class _FakeSession:
        def __init__(self, *_args, **_kwargs) -> None:
            self.last_input = None

        def run(self, _output_names, input_feed):
            self.last_input = input_feed
            return [np.zeros((1, 24000), dtype=np.float32)]

    def _fake_download(*_args, **_kwargs):
        filename = _kwargs.get("filename")
        if filename == synthesizer_kokoro.MODEL_FILENAME:
            return str(model_path)
        if filename == synthesizer_kokoro.TOKENIZER_FILENAME:
            return str(tokenizer_path)
        return str(voices_path)

    monkeypatch.setattr(synthesizer_kokoro, "hf_hub_download", _fake_download)
    monkeypatch.setattr(synthesizer_kokoro.ort, "InferenceSession", _FakeSession)
    monkeypatch.setattr(
        synthesizer_kokoro.KokoroSynthesizer,
        "_init_g2p",
        lambda _self: (lambda _text: "a"),
    )

    synthesizer = synthesizer_kokoro.KokoroSynthesizer()
    audio_bytes, sample_rate, duration_ms = synthesizer.synthesize("hello", None, "af_bella-1")

    assert isinstance(audio_bytes, (bytes, bytearray))
    assert sample_rate == 24000
    assert duration_ms > 0
    assert synthesizer.session.last_input is not None
    assert synthesizer.session.last_input["speed"].item() == pytest.approx(1.25)
    assert np.array_equal(synthesizer.session.last_input["style"], voice_vectors[1:2])


def test_factory_selects_kokoro(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeSynthesizer:
        pass

    monkeypatch.setenv("TTS_MODEL_NAME", "kokoro")
    monkeypatch.setattr(synthesizer_kokoro, "KokoroSynthesizer", lambda: _FakeSynthesizer())

    synthesizer = SynthesizerFactory.create()
    assert isinstance(synthesizer, _FakeSynthesizer)
