# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV SCHEMA_DIR=/app/shared/schemas/avro

WORKDIR /app

COPY shared/schemas /app/shared/schemas
COPY shared/speech-lib /app/shared/speech-lib
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install /app/shared/speech-lib \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch==2.6.0+cpu \
    && pip install "numpy<2" \
    && pip install confluent-kafka transformers sentencepiece

COPY services/translation /app/services/translation
WORKDIR /app/services/translation

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install . --no-deps

# Optional: set HF_HOME at runtime to control model cache location.

ENTRYPOINT ["python", "-m", "translation_service.main"]
