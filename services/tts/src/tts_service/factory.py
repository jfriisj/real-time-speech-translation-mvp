from __future__ import annotations

from .config import Settings
from .kokoro import KokoroSynthesizer
from .synthesizer import MockSynthesizer, Synthesizer


class SynthesizerFactory:
    @staticmethod
    def create(settings: Settings) -> Synthesizer:
        engine = settings.model_engine.lower()
        if engine == "kokoro_onnx":
            return KokoroSynthesizer(
                model_repo=settings.model_repo,
                model_filename=settings.model_filename,
                cache_dir=settings.model_cache_dir,
                sample_rate_hz=settings.sample_rate_hz,
                model_name=settings.model_name,
            )
        if engine == "mock":
            return MockSynthesizer(
                sample_rate_hz=settings.sample_rate_hz,
                model_name="mock",
            )
        raise ValueError(f"Unsupported TTS_MODEL_ENGINE: {settings.model_engine}")
