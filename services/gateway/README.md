# gateway-service

WebSocket ingress service for streaming PCM audio into the platform as `AudioInputEvent`.

## Runtime configuration

- `KAFKA_BOOTSTRAP_SERVERS` (default: `127.0.0.1:29092`)
- `SCHEMA_REGISTRY_URL` (default: `http://127.0.0.1:8081`)
- `SCHEMA_DIR` (default: `shared/schemas/avro`)
- `GATEWAY_HOST` (default: `0.0.0.0`)
- `GATEWAY_PORT` (default: `8000`)
- `AUDIO_FORMAT` (default: `wav`)
- `SAMPLE_RATE_HZ` (default: `16000`)
- `MAX_BUFFER_BYTES` (default: `1572864`)
- `MAX_CHUNK_BYTES` (default: `65536`)
- `MAX_CONNECTIONS` (default: `10`)
- `IDLE_TIMEOUT_SECONDS` (default: `10`)
- `MAX_SESSION_SECONDS` (default: `60`)
- `MAX_MESSAGES_PER_SECOND` (default: `200`)
- `ORIGIN_ALLOWLIST` (default: empty)

## WebSocket protocol

1. Connect to `/ws/audio`.
2. Server sends handshake text frame: `{"status":"connected","correlation_id":"..."}`.
3. Client streams binary PCM16 audio frames.
4. Client sends `{"event":"done"}` as a text frame to trigger publish.
5. Server publishes `AudioInputEvent` and closes the connection.

## Local development

1. `pip install -e ../../shared/speech-lib`
2. `pip install -e .`
3. `python -m gateway_service.main`
