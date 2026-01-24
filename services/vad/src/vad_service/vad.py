from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
from huggingface_hub import hf_hub_download


LOGGER = logging.getLogger(__name__)


@dataclass
class VadModel:
    session: Any
    input_name: str
    sample_rate_name: Optional[str]


def _resolve_onnx_path(model_repo: str, model_filename: str) -> Path:
    path = hf_hub_download(repo_id=model_repo, filename=model_filename)
    return Path(path)


def load_onnx_model(model_repo: str, model_filename: str) -> VadModel:
    try:
        import onnxruntime as ort  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("onnxruntime is required for ONNX inference") from exc

    model_path = _resolve_onnx_path(model_repo, model_filename)
    session = ort.InferenceSession(
        str(model_path),
        providers=["CPUExecutionProvider"],
    )

    inputs = session.get_inputs()
    if not inputs:
        raise RuntimeError("ONNX model has no inputs")

    input_name = inputs[0].name
    sample_rate_name = None
    if len(inputs) > 1:
        sample_rate_name = inputs[1].name

    return VadModel(session=session, input_name=input_name, sample_rate_name=sample_rate_name)


def infer_speech_probabilities(
    *,
    model: VadModel,
    audio: np.ndarray,
    sample_rate_hz: int,
    frame_length: int,
    hop_length: int,
) -> np.ndarray:
    probabilities = []
    for start in range(0, len(audio), hop_length):
        frame = audio[start : start + frame_length]
        if len(frame) < frame_length:
            frame = np.pad(frame, (0, frame_length - len(frame)))

        inputs = {model.input_name: frame.astype(np.float32)[None, :]}
        if model.sample_rate_name:
            inputs[model.sample_rate_name] = np.array([sample_rate_hz], dtype=np.int64)

        outputs = model.session.run(None, inputs)
        if not outputs:
            continue

        output = np.asarray(outputs[0]).reshape(-1)
        if output.size == 0:
            continue
        probabilities.append(float(output[0]))

    if not probabilities:
        LOGGER.warning("ONNX VAD returned no probabilities; falling back to energy detection")
        return np.array([], dtype=np.float32)

    return np.asarray(probabilities, dtype=np.float32)
