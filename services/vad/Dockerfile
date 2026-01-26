# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ARG VAD_MODEL_REPO=onnx-community/silero-vad
ARG VAD_MODEL_FILENAME=silero_vad.onnx

ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/.cache/huggingface
ENV SCHEMA_DIR=/app/shared/schemas/avro
ENV VAD_MODEL_REPO=${VAD_MODEL_REPO}
ENV VAD_MODEL_FILENAME=${VAD_MODEL_FILENAME}

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY shared/schemas /app/shared/schemas
COPY shared/speech-lib /app/shared/speech-lib
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install /app/shared/speech-lib

COPY services/vad /app/services/vad
WORKDIR /app/services/vad

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install .

RUN --mount=type=cache,target=/app/.cache/huggingface \
    python - <<'PY'
import os
from huggingface_hub import hf_hub_download

repo_id = os.getenv("VAD_MODEL_REPO", "onnx-community/silero-vad")
filename = os.getenv("VAD_MODEL_FILENAME", "silero_vad.onnx")
try:
    hf_hub_download(repo_id=repo_id, filename=filename)
    print(f"Downloaded VAD model {repo_id}:{filename}")
except Exception as exc:
    print(f"Skipping VAD model prefetch: {exc}")
PY

ENTRYPOINT ["python", "-m", "vad_service.main"]
