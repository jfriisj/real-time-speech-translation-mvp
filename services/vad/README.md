# VAD Service

Consumes `AudioInputEvent` messages, applies voice activity detection, and emits `SpeechSegmentEvent` messages containing speech-only segments.

## Topics
- Input: `speech.audio.ingress`
- Output: `speech.audio.speech_segment`

## Configuration

| Environment Variable | Default | Description |
| --- | --- | --- |
| `KAFKA_BOOTSTRAP_SERVERS` | `127.0.0.1:29092` | Kafka bootstrap servers. |
| `SCHEMA_REGISTRY_URL` | `http://127.0.0.1:8081` | Schema Registry URL. |
| `SCHEMA_DIR` | `shared/schemas/avro` | Schema directory. |
| `CONSUMER_GROUP_ID` | `vad-service` | Kafka consumer group id. |
| `POLL_TIMEOUT_SECONDS` | `1.0` | Poll timeout seconds. |
| `TARGET_SAMPLE_RATE_HZ` | `16000` | Sample rate used for VAD inference/output. |
| `VAD_WINDOW_MS` | `30` | Window size in milliseconds. |
| `VAD_HOP_MS` | `10` | Hop size in milliseconds. |
| `VAD_SPEECH_THRESHOLD` | `0.5` | Speech probability threshold for ONNX inference. |
| `VAD_ENERGY_THRESHOLD` | `0.01` | RMS energy threshold used when ONNX model is unavailable. |
| `VAD_MIN_SPEECH_MS` | `250` | Minimum speech duration to keep. |
| `VAD_MIN_SILENCE_MS` | `200` | Minimum silence to split segments. |
| `VAD_PADDING_MS` | `100` | Padding added around detected speech. |
| `VAD_USE_ONNX` | `1` | Set `0` to force energy-based detection. |
| `VAD_MODEL_REPO` | `onnx-community/silero-vad` | Hugging Face model repo. |
| `VAD_MODEL_FILENAME` | `silero_vad.onnx` | ONNX model filename. |
