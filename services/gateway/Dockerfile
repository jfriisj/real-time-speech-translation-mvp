FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV SCHEMA_DIR=/app/shared/schemas/avro

WORKDIR /app

COPY shared/schemas /app/shared/schemas
COPY shared/speech-lib /app/shared/speech-lib
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /app/shared/speech-lib

COPY services/gateway /app/services/gateway
WORKDIR /app/services/gateway

RUN pip install --no-cache-dir .

RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["python", "-m", "gateway_service.main"]
