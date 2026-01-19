FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV SCHEMA_DIR=/app/shared/schemas/avro

WORKDIR /app

COPY shared/schemas /app/shared/schemas
COPY shared/speech-lib /app/shared/speech-lib
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /app/shared/speech-lib \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.6.0+cpu \
    && pip install --no-cache-dir "numpy<2" \
    && pip install --no-cache-dir confluent-kafka transformers sentencepiece

COPY services/translation /app/services/translation
WORKDIR /app/services/translation

RUN pip install --no-cache-dir . --no-deps

# Optional: set HF_HOME at runtime to control model cache location.

ENTRYPOINT ["python", "-m", "translation_service.main"]
