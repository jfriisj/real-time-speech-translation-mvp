from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

import numpy as np

from huggingface_hub import hf_hub_download

from .audio import apply_speed, encode_wav
from .synthesizer import SynthesizedAudio


@dataclass(frozen=True)
class KokoroTokenizer:
    vocab: dict[str, int]
    unk_token_id: int | None
    bos_token_id: int | None
    eos_token_id: int | None

    @classmethod
    def from_json(cls, tokenizer_path: Path) -> "KokoroTokenizer":
        data = json.loads(tokenizer_path.read_text())
        vocab = (
            data.get("model", {}).get("vocab")
            or data.get("vocab")
            or data.get("tokenizer", {}).get("vocab")
            or {}
        )
        unk_token_id = _find_token_id(vocab, ["<unk>", "[UNK]", "<UNK>"])
        bos_token_id = _find_token_id(vocab, ["<bos>", "[BOS]"])
        eos_token_id = _find_token_id(vocab, ["<eos>", "[EOS]"])
        return cls(vocab=vocab, unk_token_id=unk_token_id, bos_token_id=bos_token_id, eos_token_id=eos_token_id)

    def tokenize(self, text: str) -> list[str]:
        phonemes = _phonemize(text)
        tokens = [token for token in phonemes.split() if token]
        if not tokens:
            tokens = list(text)
        return tokens

    def tokens_to_ids(self, tokens: Iterable[str]) -> list[int]:
        ids: list[int] = []
        if self.bos_token_id is not None:
            ids.append(self.bos_token_id)
        for token in tokens:
            token_id = self.vocab.get(token)
            if token_id is None:
                if self.unk_token_id is None:
                    continue
                token_id = self.unk_token_id
            ids.append(int(token_id))
        if self.eos_token_id is not None:
            ids.append(self.eos_token_id)
        if not ids:
            for char in "".join(tokens):
                token_id = self.vocab.get(char)
                if token_id is not None:
                    ids.append(int(token_id))
            if not ids:
                space_id = self.vocab.get(" ")
                if space_id is not None:
                    ids.append(int(space_id))
        return ids


class KokoroSynthesizer:
    def __init__(
        self,
        *,
        model_repo: str,
        model_revision: str,
        model_filename: str,
        cache_dir: Path,
        sample_rate_hz: int,
        model_name: str,
    ) -> None:
        self.sample_rate_hz = sample_rate_hz
        self.model_name = model_name
        self.model_path = Path(
            hf_hub_download(
                repo_id=model_repo,
                filename=model_filename,
                cache_dir=str(cache_dir),
                revision=model_revision,
            )
        )
        self.tokenizer_path = Path(
            hf_hub_download(
                repo_id=model_repo,
                filename="tokenizer.json",
                cache_dir=str(cache_dir),
                revision=model_revision,
            )
        )
        self.tokenizer = KokoroTokenizer.from_json(self.tokenizer_path)
        self.session = _load_onnx_session(self.model_path)
        self.input_names = [inp.name for inp in self.session.get_inputs()]

    def synthesize(self, text: str, *, speaker_id: str | None, speed: float) -> SynthesizedAudio:
        tokens = self.tokenizer.tokenize(text)
        input_ids = np.asarray([self.tokenizer.tokens_to_ids(tokens)], dtype=np.int64)
        inputs = _build_inputs(self.input_names, input_ids)
        outputs = self.session.run(None, inputs)
        if not outputs:
            raise RuntimeError("Kokoro ONNX returned no outputs")
        audio = np.asarray(outputs[0]).squeeze()
        if audio.ndim != 1:
            audio = audio.reshape(-1)
        audio = audio.astype(np.float32)
        audio = apply_speed(audio, speed)
        audio_bytes = encode_wav(audio, self.sample_rate_hz)
        duration_ms = int(len(audio) / self.sample_rate_hz * 1000)
        return SynthesizedAudio(
            audio_bytes=audio_bytes,
            sample_rate_hz=self.sample_rate_hz,
            duration_ms=duration_ms,
            model_name=self.model_name,
        )


def _find_token_id(vocab: dict[str, int], candidates: Iterable[str]) -> int | None:
    for token in candidates:
        token_id = vocab.get(token)
        if token_id is not None:
            return int(token_id)
    return None


def _phonemize(text: str) -> str:
    try:
        from phonemizer import phonemize  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency guard
        raise RuntimeError("phonemizer is required for Kokoro tokenization") from exc

    return phonemize(
        text,
        language="en-us",
        backend="espeak",
        strip=True,
        preserve_punctuation=True,
        with_stress=True,
    )


def _load_onnx_session(model_path: Path):
    try:
        import onnxruntime as ort  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency guard
        raise RuntimeError("onnxruntime is required for Kokoro ONNX inference") from exc

    return ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])


def _build_inputs(input_names: list[str], input_ids: np.ndarray) -> dict[str, np.ndarray]:
    inputs: dict[str, np.ndarray] = {}
    for name in input_names:
        lowered = name.lower()
        if "input" in lowered or "token" in lowered:
            inputs[name] = input_ids
        elif "style" in lowered:
            inputs[name] = np.zeros((1, 256), dtype=np.float32)
        elif "speed" in lowered:
            inputs[name] = np.asarray([1.0], dtype=np.float32)
    if not inputs:
        raise RuntimeError("Unable to map Kokoro ONNX inputs")
    return inputs
