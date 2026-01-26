# Changelog

## 0.5.0 - 2026-01-26
- Finalized Kokoro ONNX inference pipeline with real phoneme tokenization.
- Enforced input length caps and dual-mode payload delivery for TTS outputs.
- Verified MinIO lifecycle retention policy for TTS audio URIs (24h).

## 0.5.0-rc - 2026-01-25
- Added TTS service with IndexTTS-2 integration and dual-mode audio transport.
- Added MinIO lifecycle policy for `audio_uri` payloads (24h retention).
- Added TTS pipeline end-to-end smoke test.