# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ARG MODEL_NAME=openai/whisper-tiny
ENV MODEL_NAME=${MODEL_NAME}
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/.cache/huggingface
ENV SCHEMA_DIR=/app/shared/schemas/avro

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY shared/schemas /app/shared/schemas
COPY shared/speech-lib /app/shared/speech-lib
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install /app/shared/speech-lib

COPY services/asr /app/services/asr
WORKDIR /app/services/asr

ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install .

RUN --mount=type=cache,target=/app/.cache/huggingface \
    python - <<'PY'
import os
from transformers import pipeline

model_name = os.getenv("MODEL_NAME", "openai/whisper-tiny")
pipeline("automatic-speech-recognition", model=model_name)
PY

ENTRYPOINT ["python", "-m", "asr_service.main"]
