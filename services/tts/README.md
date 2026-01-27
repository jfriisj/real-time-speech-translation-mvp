# TTS Service

Text-to-speech microservice for the speech translation MVP.

Consumes `TextTranslatedEvent` from `speech.translation.text` and produces `AudioSynthesisEvent` to `speech.tts.audio`.

## Local development

Install shared contract helpers first, then install the TTS service:

1. `pip install -e ../../shared/speech-lib`
2. `pip install -e .`

## Runtime configuration

- `KAFKA_BOOTSTRAP_SERVERS` (default: `127.0.0.1:29092`)
- `SCHEMA_REGISTRY_URL` (default: `http://127.0.0.1:8081`)
- `CONSUMER_GROUP_ID` (default: `tts-service`)
- `POLL_TIMEOUT_SECONDS` (default: `1.0`)
- `SCHEMA_DIR` (default: `shared/schemas/avro`)
- `TTS_MODEL_ENGINE` (default: `kokoro_onnx`)
- `TTS_MODEL_REPO` (default: `onnx-community/Kokoro-82M-v1.0-ONNX`)
- `TTS_MODEL_FILENAME` (default: `model.onnx`)
- `TTS_MODEL_CACHE_DIR` (default: `model_cache`)
- `TTS_MODEL_NAME` (default: `kokoro-82m-onnx`)
- `TTS_SAMPLE_RATE_HZ` (default: `24000`)
- `TTS_SPEED` (default: `1.0`)
- `MAX_TEXT_LENGTH` (default: `500`)
- `INLINE_PAYLOAD_MAX_BYTES` (default: `1310720`)
- `DISABLE_STORAGE` (default: `0`)
- `TTS_AUDIO_URI_MODE` (default: `internal`, options: `internal`, `presigned`)

### Object storage (optional)

- `MINIO_ENDPOINT` (default: `http://127.0.0.1:9000`)
- `MINIO_ACCESS_KEY` (default: `minioadmin`)
- `MINIO_SECRET_KEY` (default: `minioadmin`)
- `MINIO_BUCKET` (default: `tts-audio`)
- `MINIO_SECURE` (default: `0`)
- `MINIO_PUBLIC_ENDPOINT` (default: empty)
- `MINIO_PRESIGN_EXPIRY_SECONDS` (default: `86400`)

Note: In local Docker compose the service is configured with `TTS_AUDIO_URI_MODE=presigned` to keep the smoke test compatible. In production the preferred mode is `internal` so the Gateway can presign at read-time.
