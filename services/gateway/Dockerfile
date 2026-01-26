# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV SCHEMA_DIR=/app/shared/schemas/avro

WORKDIR /app

COPY shared/schemas /app/shared/schemas
COPY shared/speech-lib /app/shared/speech-lib
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install /app/shared/speech-lib

COPY services/gateway /app/services/gateway
WORKDIR /app/services/gateway

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install .

RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["python", "-m", "gateway_service.main"]
