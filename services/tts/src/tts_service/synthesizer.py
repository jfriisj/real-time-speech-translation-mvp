from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
import tempfile
from pathlib import Path
from typing import Any, Tuple

import numpy as np
import soundfile as sf

from .audio import decode_wav_bytes


LOGGER = logging.getLogger(__name__)


INDEX_TTS_MODEL_ID = "IndexTeam/IndexTTS-2"


class Synthesizer:
    def synthesize(self, text: str, speaker_reference_bytes: bytes | None) -> Tuple[np.ndarray, int]:
        raise NotImplementedError

    def warmup(self) -> None:
        return None


@lru_cache(maxsize=2)
def _download_model_dir(model_name: str, cache_dir: str | None) -> Path:
    from huggingface_hub import snapshot_download

    local_dir = snapshot_download(
        repo_id=model_name,
        cache_dir=cache_dir,
        local_dir=None,
        local_dir_use_symlinks=False,
    )
    return Path(local_dir)


@lru_cache(maxsize=1)
def _load_indextts(model_dir: str) -> Any:
    from indextts.infer_v2 import IndexTTS2

    cfg_path = Path(model_dir) / "config.yaml"
    return IndexTTS2(
        cfg_path=str(cfg_path),
        model_dir=str(model_dir),
        use_fp16=False,
        use_cuda_kernel=False,
        use_deepspeed=False,
    )


def _default_prompt_audio(sample_rate: int = 16000, duration_seconds: float = 0.8) -> np.ndarray:
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds), endpoint=False)
    return (0.1 * np.sin(2 * np.pi * 220.0 * t)).astype(np.float32)


@dataclass(frozen=True)
class IndexTTS2Synthesizer(Synthesizer):
    model_name: str
    model_dir: str | None = None
    cache_dir: str | None = None

    def warmup(self) -> None:
        resolved_dir = self.model_dir or _download_model_dir(self.model_name, self.cache_dir)
        _load_indextts(str(resolved_dir))

    def synthesize(self, text: str, speaker_reference_bytes: bytes | None) -> Tuple[np.ndarray, int]:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("text is empty")
        if self.model_name != INDEX_TTS_MODEL_ID:
            raise ValueError(f"Unsupported TTS model: {self.model_name}")

        resolved_dir = self.model_dir or _download_model_dir(self.model_name, self.cache_dir)
        tts = _load_indextts(str(resolved_dir))

        with tempfile.TemporaryDirectory() as tmp_dir:
            prompt_path = Path(tmp_dir) / "prompt.wav"
            output_path = Path(tmp_dir) / "output.wav"

            if speaker_reference_bytes:
                try:
                    speaker_audio, speaker_rate = decode_wav_bytes(speaker_reference_bytes)
                    sf.write(prompt_path, speaker_audio, speaker_rate)
                    LOGGER.info("Speaker reference enabled for IndexTTS-2")
                except Exception as exc:
                    LOGGER.info("Invalid speaker reference audio; falling back to default voice: %s", exc)
                    speaker_audio = _default_prompt_audio()
                    sf.write(prompt_path, speaker_audio, 16000)
            else:
                speaker_audio = _default_prompt_audio()
                sf.write(prompt_path, speaker_audio, 16000)

            tts.infer(
                spk_audio_prompt=str(prompt_path),
                text=cleaned,
                output_path=str(output_path),
                verbose=False,
            )

            audio, sample_rate = sf.read(output_path, dtype="float32")
            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)
            return audio, int(sample_rate)
