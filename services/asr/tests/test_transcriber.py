from __future__ import annotations

from typing import Any, Dict

import numpy as np

from asr_service.transcriber import Transcriber


class DummyPipeline:
    def __init__(self, result: Dict[str, Any]) -> None:
        self._result = result

    def __call__(self, payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        assert "array" in payload
        assert "sampling_rate" in payload
        return self._result


def test_transcriber_returns_pipeline_result() -> None:
    dummy = DummyPipeline({"text": "hello", "language": "en", "confidence": 0.9})
    transcriber = Transcriber("dummy", pipeline_factory=lambda *args, **kwargs: dummy)
    audio = np.zeros(16000, dtype=np.float32)
    result = transcriber.transcribe(audio, 16000)
    assert result["text"] == "hello"
