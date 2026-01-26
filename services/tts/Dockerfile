# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV SCHEMA_DIR=/app/shared/schemas/avro

WORKDIR /app

COPY shared/schemas /app/shared/schemas
COPY shared/speech-lib /app/shared/speech-lib

# System dependencies for soundfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends libsndfile1 git \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install /app/shared/speech-lib

COPY services/tts /app/services/tts
WORKDIR /app/services/tts

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install .

# Ensure model cache directory exists
RUN mkdir -p /app/model_cache && chmod 777 /app/model_cache

ENTRYPOINT ["python", "-m", "tts_service.main"]
