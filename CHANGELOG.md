# Changelog

## 0.4.1 - 2026-01-28
- Added bounded startup readiness gates for Kafka and Schema Registry across services.
- Standardized startup timing configuration via `STARTUP_*` environment variables.
- Added a startup resilience verification script for compose runs.

## 0.5.0 - 2026-01-26
- Added TTS service with Kokoro ONNX backend and pluggable synthesizer factory.
- Enforced input length caps and dual-mode payload delivery for TTS outputs (inline vs URI).
- Added AudioSynthesisEvent speaker context pass-through and text snippet fields.
- Added MinIO lifecycle retention policy for TTS audio URIs (24h).
- Standardized Kafka consumer tuning and validation across VAD/ASR/Translation/TTS.
- Added low-volume Kafka consumer recovery telemetry events for diagnosability.
- Added explicit steady-state vs cold-start modes in the TTS smoke pipeline.

## 0.5.0-rc - 2026-01-25
- Added TTS service with IndexTTS-2 integration and dual-mode audio transport.
- Added MinIO lifecycle policy for `audio_uri` payloads (24h retention).
- Added TTS pipeline end-to-end smoke test.