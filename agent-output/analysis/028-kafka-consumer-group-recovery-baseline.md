---
ID: 028
Origin: 028
UUID: 4f6b2c1d
Status: Active
---

# Baseline Evidence: Kafka Consumer Group Recovery (Plan 028)

## Status
Pending measurement. This file is a placeholder to capture the baseline evidence required by Plan 028.

## Environment Summary
- Date/time: 2026-01-28 (UTC)
- Host: cachyos-x8664
- Compose profile: default (docker-compose.yml)
- Services measured: tts-service, vad-service

## Baseline Consumer Tuning Snapshot (Allowlisted)

### tts-service
- service_name: tts-service
- consumer_group_id: tts-service
- session_timeout_ms: 15000
- heartbeat_interval_ms: 5000
- max_poll_interval_ms: 300000
- partition_assignment_strategy: None
- static_membership_enabled: False

### vad-service
- service_name: vad-service
- consumer_group_id: vad-service
- session_timeout_ms: 15000
- heartbeat_interval_ms: 5000
- max_poll_interval_ms: 300000
- partition_assignment_strategy: None
- static_membership_enabled: False

## Restart Condition Description
- Restart action: `docker compose up -d --build` (full rebuild/recreate) followed by `docker compose restart tts-service` and `docker compose restart vad-service`.
- Publish timing relative to restart:
	- TTS: smoke publish immediately after restart via `tests/e2e/tts_pipeline_smoke.py` in `cold-start` mode.
	- VAD: smoke publish immediately after restart via `tests/e2e/vad_pipeline_smoke.py`.

## Timing Evidence

### tts-service (cold-start smoke)
- restart_timestamp: 2026-01-28T21:10:35Z (restart command issued)
- assignment_acquired_timestamp: 2026-01-28T21:11:03.684Z
- first_input_received_timestamp: 2026-01-28T21:11:07.752Z
- first_output_published_timestamp: 2026-01-28T21:11:10.487Z (AudioSynthesisEvent published)

### vad-service (pipeline smoke)
- restart_timestamp: 2026-01-28T21:11:31Z (restart command issued)
- assignment_acquired_timestamp: 2026-01-28T21:12:12.199Z
- first_input_received_timestamp: 2026-01-28T21:12:12.308Z
- first_output_published_timestamp: 2026-01-28T21:12:12.412Z (SpeechSegmentEvent published)

## Notes
- Image/workspace parity: Compose stack rebuilt and containers recreated via `docker compose up -d --build` immediately before measurements.
- TTS smoke: `TTS_SMOKE_MODE=cold-start` succeeded with `PASS: TTS pipeline produced AudioSynthesisEvent`.
- VAD smoke: `tests/e2e/vad_pipeline_smoke.py` timed out waiting for `TextRecognizedEvent` (ASR); VAD consumed input and published `SpeechSegmentEvent` as shown in telemetry logs.
- VAD logs reported a 404 when attempting to load the ONNX VAD model from Hugging Face prior to consuming input.
- ASR logs show a processing error on the same correlation_id (`KeyError: 'num_frames'` in transformers pipeline), which likely caused the missing `TextRecognizedEvent`.
- Follow-up: Updated ASR transcriber input handling resolved the `num_frames` error; VAD pipeline smoke now passes (see implementation report).