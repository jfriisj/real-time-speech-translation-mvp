# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ARG TTS_MODEL_REPO=onnx-community/Kokoro-82M-v1.0-ONNX
ARG TTS_MODEL_FILENAME=model.onnx

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/.cache/huggingface
ENV SCHEMA_DIR=/app/shared/schemas/avro
ENV TTS_MODEL_REPO=${TTS_MODEL_REPO}
ENV TTS_MODEL_FILENAME=${TTS_MODEL_FILENAME}

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libsndfile1 espeak-ng \
    && rm -rf /var/lib/apt/lists/*

COPY shared/schemas /app/shared/schemas
COPY shared/speech-lib /app/shared/speech-lib
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install /app/shared/speech-lib

COPY services/tts /app/services/tts
WORKDIR /app/services/tts

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install .

RUN --mount=type=cache,target=/app/.cache/huggingface \
    python - <<'PY'
import os
from huggingface_hub import hf_hub_download

repo_id = os.getenv("TTS_MODEL_REPO", "onnx-community/Kokoro-82M-v1.0-ONNX")
filename = os.getenv("TTS_MODEL_FILENAME", "model.onnx")
try:
    hf_hub_download(repo_id=repo_id, filename=filename)
    hf_hub_download(repo_id=repo_id, filename="tokenizer.json")
    print(f"Downloaded TTS model {repo_id}:{filename}")
except Exception as exc:
    print(f"Skipping TTS model prefetch: {exc}")
PY

ENTRYPOINT ["python", "-m", "tts_service.main"]
