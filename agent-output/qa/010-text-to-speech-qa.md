# QA Report: Text-to-Speech (TTS) Service

**Plan Reference**: agent-output/planning/010-text-to-speech-plan.md
**QA Status**: QA Failed
**QA Specialist**: qa

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-25 | Implementer | Verify coverage and execute tests | Executed unit tests, ran Ruff gate, captured TTS coverage (72%), integration gaps remain. |
| 2026-01-25 | QA | Re-verify coverage and tests | Re-ran TTS unit tests with coverage; Ruff + Vulture clean; integration tests still pending. |
| 2026-01-25 | QA | Address coverage gaps | Added unit tests for `tts_service.main` helpers and `main()` control flow; coverage now >70% for main.py. |

## Timeline
- **Test Strategy Started**: 2026-01-25
- **Test Strategy Completed**: 2026-01-25
- **Implementation Received**: 2026-01-25
- **Testing Started**: 2026-01-25
- **Testing Completed**: 2026-01-25
- **Final Status**: QA Failed

## Test Strategy (Pre-Implementation)
### Critical User Workflows
- End-to-end speech-to-speech flow: `TextTranslatedEvent` -> `AudioSynthesisEvent` with correlation preserved.
- Voice cloning context propagation (speaker reference bytes + speaker ID pass-through).
- Large output audio switches to `audio_uri` and is retrievable.

### Key Failure Modes
- Oversized audio payload emits inline bytes exceeding cap.
- Object store upload failure causes crash-loop or silent drop without logging.
- Missing/invalid speaker reference breaks synthesis rather than falling back.
- Schema compatibility drift across services (optional fields not handled).

### Test Types
- **Unit**: Event payload validation, speaker context pass-through, dual-mode payload selection.
- **Integration**: Kafka + Schema Registry + MinIO bring-up with TTS consuming and emitting events.
- **E2E**: Full pipeline speech -> translation -> TTS output and playback validation.

### ⚠️ Testing Infrastructure Needed
- Docker Compose for Kafka + Schema Registry + MinIO + TTS service.
- Pytest (already used in repo).
- Local MinIO bucket lifecycle rule application (24h) for retention validation.

### Acceptance Criteria
- TTS service runs and emits `AudioSynthesisEvent` keyed by `correlation_id`.
- Inline vs URI switch at payload cap is enforced.
- Speaker context is propagated from ingress to TTS.
- MinIO retention lifecycle applied (24h).

## Implementation Review (Post-Implementation)
### Code Changes Summary
- Added TTS service, MinIO integration, and `AudioSynthesisEvent` schema.
- Updated ASR/Translation/VAD to pass through speaker context fields.
- Added dataset for TTS metrics in tests data.

## Test Coverage Analysis
### New/Modified Code
| File | Function/Class | Test File | Test Case | Coverage Status |
|------|---------------|-----------|-----------|-----------------|
| services/tts/src/tts_service/main.py | `process_event()` | services/tts/tests/test_tts_processing.py | `test_process_event_emits_inline_audio`, `test_process_event_emits_uri_when_too_large` | COVERED |
| services/tts/src/tts_service/synthesizer.py | `HuggingFaceSynthesizer` | services/tts/tests/test_synthesizer.py | `test_synthesizer_*` | COVERED |
| services/tts/src/tts_service/storage.py | `ObjectStorage.upload_bytes()` | services/tts/tests/test_storage.py | `test_upload_bytes_returns_public_uri` | COVERED |
| services/tts/src/tts_service/audio.py | `encode_wav_bytes()` | services/tts/tests/test_audio_helpers.py | `test_encode_decode_wav_round_trip` | COVERED |
| services/translation/src/translation_service/main.py | `extract_translation_request()` | services/translation/tests/test_translation_processing.py | `test_extract_translation_request_defaults_missing_source_language` | COVERED |
| services/asr/src/asr_service/main.py | `build_output_event()` | services/asr/tests/test_processing.py | `test_build_output_event_includes_speaker_context` | COVERED |
| services/vad/src/vad_service/main.py | `process_event()` | services/vad/tests/test_processing.py | `test_process_event_passes_speaker_context` | COVERED |
| shared/speech-lib/src/speech_lib/events.py | `AudioSynthesisPayload.validate()` | shared/speech-lib/tests/test_events.py | `test_audio_synthesis_payload_requires_exactly_one_source` | COVERED |

### Coverage Gaps
- TTS service `main.py` remains partially uncovered (end-to-end run loop, unexpected exception branch).
- No integration tests validate MinIO lifecycle or URI retrieval behavior.

## Test Execution Results
### Unit Tests
- **Command**: runTests (services/tts/tests)
- **Status**: PASS
- **Output**: 14 passed, 0 failed

### Unit Tests (TTS)
- **Command**: `python -m pytest services/tts/tests`
- **Status**: PASS
- **Output**: 8 passed, 0 failed

### Coverage
- **Command**: runTests (coverage mode) with coverage file `services/tts/src/tts_service/main.py`
- **Status**: PASS
- **Output**: main.py coverage 81.31% (77/93 statements; branches 10/14).

### Integration Tests
- **Status**: NOT RUN
- **Reason**: Docker-based Kafka/Schema Registry/MinIO bring-up not executed in this session.

## Code Quality Gate
- **Ruff**: PASS (no issues on TTS source + tests)
- **Dead-code scan**: PASS (no high-confidence unused code in TTS source)

## QA Decision
**QA Failed** due to:
1. Integration testing for Kafka + MinIO + TTS flow not executed.

## Recommended Next Steps
- Run integration tests with Docker Compose and verify MinIO lifecycle + URI retrieval paths.
- Add integration validation for URI retrieval failure behavior (404/timeout) and confirm log/skip semantics.

## Handoff
Testing incomplete. QA not ready for UAT.
