# TTS Service

Synthesizes speech from translated text and emits `AudioSynthesisEvent` on `speech.tts.audio`.

## Environment
- `KAFKA_BOOTSTRAP_SERVERS`
- `SCHEMA_REGISTRY_URL`
- `SCHEMA_DIR`
- `CONSUMER_GROUP_ID`
- `TTS_MODEL_NAME`
- `TTS_MODEL_DIR`
- `TTS_MODEL_CACHE_DIR`
- `POLL_TIMEOUT_SECONDS`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET`
- `MINIO_SECURE`
- `MINIO_PUBLIC_ENDPOINT`
- `MINIO_PRESIGNED_EXPIRES_SECONDS`
- `INLINE_PAYLOAD_MAX_BYTES`
- `METRICS_PORT`

## Notes
- Output format is WAV only.
- Speaker context is optional and falls back to the default voice when unsupported.
