FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV SCHEMA_DIR=/app/shared/schemas/avro

WORKDIR /app

COPY shared/schemas /app/shared/schemas
COPY shared/speech-lib /app/shared/speech-lib
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /app/shared/speech-lib \
    && pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.6.0+cpu torchaudio==2.6.0+cpu \
    && pip install --no-cache-dir "numpy<2" \
    && pip install --no-cache-dir boto3 confluent-kafka prometheus-client soundfile huggingface-hub omegaconf librosa safetensors sentencepiece textstat \
    && pip install --no-cache-dir --no-deps git+https://github.com/index-tts/index-tts.git

COPY services/tts /app/services/tts
WORKDIR /app/services/tts

RUN pip install --no-cache-dir . --no-deps

ENTRYPOINT ["python", "-m", "tts_service.main"]
