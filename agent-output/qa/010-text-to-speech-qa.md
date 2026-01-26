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
| 2026-01-26 | Implementer | Verify coverage and execute tests | Re-ran analyzer gate + coverage tests; unit tests failed after Kokoro ONNX pivot; coverage dropped to 38.46%; Ruff/Vulture findings in `synthesizer_kokoro.py`. |
| 2026-01-26 | Implementer | Fix tests and rerun QA | Updated tests for Kokoro pivot; unit tests pass; coverage now 77.59%; Ruff/Vulture clean. |
| 2026-01-26 | QA | Verify coverage and execute tests | Re-ran Ruff + Vulture gates and TTS unit tests with coverage; 11/11 tests pass; coverage remains 77.59%; integration tests still not executed. |

## Timeline
- **Test Strategy Started**: 2026-01-25
- **Test Strategy Completed**: 2026-01-25
- **Implementation Received**: 2026-01-25
- **Testing Started**: 2026-01-26
- **Testing Completed**: 2026-01-26
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
- Kokoro ONNX synthesizer scaffold added with pluggable factory selection.
- `AudioSynthesisEvent` schema updated with optional `model_name`.
- TTS service updated to emit `model_name` and use factory-based synthesizer.

## Test Coverage Analysis
### New/Modified Code
| File | Function/Class | Test File | Test Case | Coverage Status |
|------|---------------|-----------|-----------|-----------------|
| services/tts/src/tts_service/main.py | `build_output_event()` | services/tts/tests/test_tts_processing.py | `test_build_output_event_sets_payload` | COVERED |
| services/tts/src/tts_service/main.py | `process_event()` | services/tts/tests/test_tts_processing.py | `test_process_event_emits_inline_audio`, `test_process_event_emits_uri_when_too_large` | COVERED |
| services/tts/src/tts_service/main.py | `main()` | services/tts/tests/test_main.py | `test_main_exits_on_keyboardinterrupt` | COVERED |
| services/tts/src/tts_service/synthesizer_kokoro.py | `KokoroSynthesizer` | services/tts/tests/test_synthesizer.py | `test_kokoro_synthesizer_downloads_assets` | COVERED |

### Coverage Gaps
- Integration tests validating MinIO lifecycle, URI retrieval, and downstream failure handling remain unexecuted.
- Real Kokoro inference (phoneme/token mapping + voices.bin parsing) remains mocked; audio quality acceptance criteria are not validated by unit tests.

## Test Execution Results
### Unit Tests (Coverage Mode)
- **Command**: runTests (coverage mode) for `services/tts/tests` with coverage file `services/tts/src/tts_service/main.py`
- **Status**: PASS
- **Output**: 11 passed, 0 failed

### Coverage
- **Command**: runTests (coverage mode) with coverage file `services/tts/src/tts_service/main.py`
- **Status**: PASS
- **Output**: main.py coverage 77.59% (79/100 statements; branches 11/16).

### Integration Tests
- **Status**: NOT RUN
- **Reason**: Docker-based Kafka/Schema Registry/MinIO bring-up not executed in this session.

## Code Quality Gate
- **Ruff**: PASS (no issues in `services/tts/src/tts_service/main.py`, `synthesizer_kokoro.py`, `synthesizer_factory.py`)
- **Dead-code scan**: PASS (no high-confidence unused code reported)

## QA Decision
**QA Failed** due to:
1. Integration testing for Kafka + MinIO + TTS flow not executed.
2. Real Kokoro inference path remains mocked; audio quality acceptance criteria not validated.

## Recommended Next Steps
- Run integration tests with Docker Compose and verify MinIO lifecycle + URI retrieval paths.
- Add integration validation for URI retrieval failure behavior (404/timeout) and confirm log/skip semantics.

## Handoff
Testing incomplete. QA not ready for UAT.
