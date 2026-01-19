# translation-service

Consumes `TextRecognizedEvent` from `speech.asr.text` and produces `TextTranslatedEvent` to `speech.translation.text`.

## Configuration

- `KAFKA_BOOTSTRAP_SERVERS` (default: `127.0.0.1:29092`)
- `SCHEMA_REGISTRY_URL` (default: `http://127.0.0.1:8081`)
- `SCHEMA_DIR` (default: `shared/schemas/avro`)
- `CONSUMER_GROUP_ID` (default: `translation-service`)
- `POLL_TIMEOUT_SECONDS` (default: `1.0`)
- `TARGET_LANGUAGE` (default: `es`)
- `TRANSLATION_MODEL_NAME` (default: `Helsinki-NLP/opus-mt-en-es`)
- `MAX_NEW_TOKENS` (default: `256`)

## Docker Notes
- The Docker image installs a CPU-only PyTorch wheel to avoid pulling CUDA dependencies.
