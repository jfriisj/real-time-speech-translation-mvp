from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tts_service import kokoro


class DummyInput:
    def __init__(self, name: str) -> None:
        self.name = name


class DummySession:
    def __init__(self, output: np.ndarray) -> None:
        self._output = output

    def get_inputs(self) -> list[DummyInput]:
        return [DummyInput("input_ids"), DummyInput("style")]

    def run(self, _output_names, _inputs):
        return [self._output]


def _write_tokenizer(path: Path) -> None:
    data = {
        "model": {
            "vocab": {
                "<unk>": 0,
                "<bos>": 1,
                "<eos>": 2,
                "AH": 3,
                "B": 4,
            }
        }
    }
    path.write_text(json.dumps(data))


def test_kokoro_tokenizer_ids_include_special_tokens(tmp_path, monkeypatch) -> None:
    tokenizer_path = tmp_path / "tokenizer.json"
    _write_tokenizer(tokenizer_path)

    tokenizer = kokoro.KokoroTokenizer.from_json(tokenizer_path)
    monkeypatch.setattr(kokoro, "_phonemize", lambda _text: "AH B")

    tokens = tokenizer.tokenize("hello")
    assert tokens == ["AH", "B"]

    token_ids = tokenizer.tokens_to_ids(tokens)
    assert token_ids == [1, 3, 4, 2]


def test_kokoro_synthesize_uses_onnx_and_speed(tmp_path, monkeypatch) -> None:
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"onnx")
    tokenizer_path = tmp_path / "tokenizer.json"
    _write_tokenizer(tokenizer_path)

    monkeypatch.setattr(
        kokoro,
        "hf_hub_download",
        lambda repo_id, filename, cache_dir=None, revision=None: str(
            tokenizer_path if filename == "tokenizer.json" else model_path
        ),
    )
    monkeypatch.setattr(kokoro, "_phonemize", lambda _text: "AH B")

    output = np.ones((1, 24000), dtype=np.float32)
    monkeypatch.setattr(kokoro, "_load_onnx_session", lambda _path: DummySession(output))

    synth = kokoro.KokoroSynthesizer(
        model_repo="dummy",
        model_revision="rev",
        model_filename="model.onnx",
        cache_dir=tmp_path,
        sample_rate_hz=24000,
        model_name="kokoro",
    )

    result = synth.synthesize("hello", speaker_id=None, speed=2.0)
    assert result.model_name == "kokoro"
    assert result.sample_rate_hz == 24000
    assert result.audio_bytes
    assert 400 <= result.duration_ms <= 600