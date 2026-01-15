from __future__ import annotations

from typing import Any, Callable, Dict

import numpy as np
from transformers import pipeline


PipelineFactory = Callable[..., Any]


class Transcriber:
    def __init__(self, model_name: str, pipeline_factory: PipelineFactory | None = None) -> None:
        factory = pipeline_factory or pipeline
        self._pipeline = factory("automatic-speech-recognition", model=model_name)

    def transcribe(self, audio: np.ndarray, sample_rate_hz: int) -> Dict[str, Any]:
        result = self._pipeline(
            {"array": audio, "sampling_rate": sample_rate_hz},
            return_timestamps=True,
        )
        if isinstance(result, str):
            return {"text": result}
        return result
