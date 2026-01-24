# ASR Service

Audio-to-text microservice for the speech translation MVP.

## Local development

Install shared contract helpers first, then install the ASR service:

1. `pip install -e ../../shared/speech-lib`
2. `pip install -e .`

## Runtime configuration

- `KAFKA_BOOTSTRAP_SERVERS` (default: `127.0.0.1:29092`)
- `SCHEMA_REGISTRY_URL` (default: `http://127.0.0.1:8081`)
- `MODEL_NAME` (default: `openai/whisper-tiny`)
- `CONSUMER_GROUP_ID` (default: `asr-service`)
- `SCHEMA_DIR` (default: `shared/schemas/avro`)
- `ASR_INPUT_TOPIC` (default: `speech.audio.ingress`)
