from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from tts_service import synthesizer as synth_module
from tts_service.synthesizer import INDEX_TTS_MODEL_ID, IndexTTS2Synthesizer


class _FakeIndexTTS2:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def infer(self, *, spk_audio_prompt: str, text: str, output_path: str, verbose: bool = False):  # noqa: ANN001
        _ = verbose
        self.calls.append((spk_audio_prompt, text, output_path))
        sf.write(output_path, np.zeros(1600, dtype=np.float32), 16000)
        return output_path


def test_synthesizer_uses_index_tts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_tts = _FakeIndexTTS2()

    monkeypatch.setattr(synth_module, "_download_model_dir", lambda *_args, **_kwargs: tmp_path)
    monkeypatch.setattr(synth_module, "_load_indextts", lambda *_args, **_kwargs: fake_tts)
    monkeypatch.setattr(
        synth_module,
        "decode_wav_bytes",
        lambda _data: (np.zeros(1600, dtype=np.float32), 16000),
    )

    synthesizer = IndexTTS2Synthesizer(model_name=INDEX_TTS_MODEL_ID)
    audio, rate = synthesizer.synthesize("hello", b"\x00\x01")

    assert audio.shape[0] == 1600
    assert rate == 16000
    assert fake_tts.calls


def test_synthesizer_falls_back_when_speaker_invalid(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_tts = _FakeIndexTTS2()

    monkeypatch.setattr(synth_module, "_download_model_dir", lambda *_args, **_kwargs: tmp_path)
    monkeypatch.setattr(synth_module, "_load_indextts", lambda *_args, **_kwargs: fake_tts)

    def _raise_decode(_data: bytes):
        raise ValueError("invalid wav")

    monkeypatch.setattr(synth_module, "decode_wav_bytes", _raise_decode)

    synthesizer = IndexTTS2Synthesizer(model_name=INDEX_TTS_MODEL_ID)
    audio, rate = synthesizer.synthesize("hello", b"bad")

    assert audio.shape[0] == 1600
    assert rate == 16000
    assert fake_tts.calls


def test_synthesizer_raises_on_empty_text() -> None:
    synthesizer = IndexTTS2Synthesizer(model_name=INDEX_TTS_MODEL_ID)
    with pytest.raises(ValueError, match="text is empty"):
        synthesizer.synthesize(" ", None)
