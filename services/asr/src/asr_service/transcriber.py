from __future__ import annotations

from typing import Any, Callable, Dict

import numpy as np


PipelineFactory = Callable[..., Any]


class Transcriber:
    def __init__(self, model_name: str, pipeline_factory: PipelineFactory | None = None) -> None:
        if pipeline_factory is None:
            try:
                from transformers import pipeline  # type: ignore
            except Exception as exc:  # pragma: no cover - optional dependency guard
                raise RuntimeError("transformers is required for ASR inference") from exc
            factory = pipeline
        else:
            factory = pipeline_factory
        self._pipeline = factory("automatic-speech-recognition", model=model_name)

    def transcribe(self, audio: np.ndarray, sample_rate_hz: int) -> Dict[str, Any]:
        payload = {
            "raw": audio,
            "sampling_rate": sample_rate_hz,
            "stride": (0, 0),
        }
        try:
            result = self._pipeline(
                payload,
                return_timestamps=True,
            )
        except KeyError as exc:
            if exc.args and exc.args[0] == "num_frames":
                result = self._pipeline(payload)
            else:
                raise
        if isinstance(result, str):
            return {"text": result}
        return result
