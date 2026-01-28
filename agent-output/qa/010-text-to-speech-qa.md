# QA Report: Plan 010 Text-to-Speech (TTS) Service

**Plan Reference**: [agent-output/planning/010-text-to-speech-plan.md](agent-output/planning/010-text-to-speech-plan.md)
**QA Status**: QA Failed
**QA Specialist**: qa

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | User → QA | Implementation complete; verify coverage and run tests | Executed Ruff checks, created QA venv, ran unit tests with coverage, identified integration/e2e gaps. |
| 2026-01-27 | User → QA | Implementation complete; verify coverage and run tests | Added Kokoro/config/main tests, ran Ruff checks, attempted pytest run but pytest missing in local env. |
| 2026-01-27 | User → QA | Implementation complete; verify coverage and run tests | Re-ran unit tests and coverage in .venv; Ruff clean; integration/e2e still pending. |
| 2026-01-27 | User → QA | Run integration/e2e smoke for TTS | Rebuilt TTS service and ran TTS pipeline smoke test (inline payload) successfully. |
| 2026-01-27 | User → QA | Run URI/MinIO smoke for TTS | Forced URI storage and validated MinIO path via TTS pipeline smoke test (URI payload) successfully. |
| 2026-01-28 | User → QA | Implementation complete; verify coverage and run tests | Re-ran Ruff checks, unit tests, and coverage; e2e inline/URI smoke tests timed out waiting for `AudioSynthesisEvent`. |

## Timeline
- **Test Strategy Started**: 2026-01-27
- **Test Strategy Completed**: 2026-01-27
- **Implementation Received**: 2026-01-27
- **Testing Started**: 2026-01-27
- **Testing Completed**: 2026-01-28
- **Final Status**: QA Failed

## Test Strategy (Pre-Implementation)

### Critical User Workflows
- TTS consumes `TextTranslatedEvent` and emits `AudioSynthesisEvent` with valid WAV output.
- Payload transport switches between inline bytes and URI based on size limits.
- Input contract enforcement: >500 characters rejected without crashing the service.
- Speaker context is preserved end-to-end (pass-through metadata).
- Trace propagation persists across service boundaries.

### Key Failure Modes
- Missing `correlation_id` or `payload.text` results in dropped events without logs.
- Payload size exceeds limit and storage is disabled (should warn + drop).
- URI mode emits invalid keys or presigned URL data is logged.
- Tokenization or ONNX runtime failures cause repeated crash loop.

### Test Types
- **Unit**: Payload handling, input validation, speaker context propagation.
- **Integration**: Kafka consume/produce, schema registration, MinIO uploads, URI mode behavior.
- **E2E**: TTS service produces audible audio in pipeline run, latency logging, and RTF evidence.

### Testing Infrastructure Requirements
**Test Frameworks Needed**:
- pytest
- pytest-cov

**Testing Libraries Needed**:
- onnxruntime (runtime inference)
- phonemizer + espeak backend
- soundfile, numpy
- confluent-kafka

**Configuration Files Needed**:
- [services/tts/pyproject.toml](services/tts/pyproject.toml) (pytest markers, package config)

**Build Tooling Changes Needed**:
- Provide a dedicated QA virtual environment (used `.venv-qa`) with pytest tooling.

**Dependencies to Install**:
```bash
python -m venv /home/jonfriis/github/real-time-speech-translation-mvp/.venv-qa
/home/jonfriis/github/real-time-speech-translation-mvp/.venv-qa/bin/pip install -e /home/jonfriis/github/real-time-speech-translation-mvp/shared/speech-lib -e /home/jonfriis/github/real-time-speech-translation-mvp/services/tts pytest pytest-cov
```

### Required Unit Tests
- Validate extraction of translation request and error handling for missing fields.
- Validate inline vs URI selection and storage-disabled behavior.
- Validate speaker context pass-through in output event.

### Required Integration Tests
- Kafka consume/produce with schema registry for `TextTranslatedEvent` → `AudioSynthesisEvent`.
- MinIO upload path emits internal key or presigned URL and avoids logging presigned URL.

### Acceptance Criteria
- Unit tests cover payload building and contract validation.
- Integration tests validate schema registration and storage behavior.
- Coverage threshold ≥90% for payload/processing logic.

## Implementation Review (Post-Implementation)

### Code Changes Summary
- TTS service implementation and Kokoro ONNX integration added under [services/tts/src/tts_service](services/tts/src/tts_service).
- Event payload and storage handling updated in shared libraries and schemas.
- Unit tests added in [services/tts/tests/test_processing.py](services/tts/tests/test_processing.py), [services/tts/tests/test_kokoro.py](services/tts/tests/test_kokoro.py), [services/tts/tests/test_config.py](services/tts/tests/test_config.py), and [services/tts/tests/test_main.py](services/tts/tests/test_main.py).

## Test Coverage Analysis

### New/Modified Code
| File | Function/Class | Test File | Test Case | Coverage Status |
|------|---------------|-----------|-----------|-----------------|
| [services/tts/src/tts_service/processing.py](services/tts/src/tts_service/processing.py) | `extract_translation_request` / payload helpers | [services/tts/tests/test_processing.py](services/tts/tests/test_processing.py) | `test_*` cases | COVERED (96% for module) |
| [services/tts/src/tts_service/main.py](services/tts/src/tts_service/main.py) | `_extract_traceparent` | [services/tts/tests/test_main.py](services/tts/tests/test_main.py) | `test_extract_traceparent_*` | PARTIAL (main loop untested) |
| [services/tts/src/tts_service/kokoro.py](services/tts/src/tts_service/kokoro.py) | `KokoroSynthesizer` | [services/tts/tests/test_kokoro.py](services/tts/tests/test_kokoro.py) | `test_kokoro_*` | COVERED (unit tests executed) |
| [services/tts/src/tts_service/config.py](services/tts/src/tts_service/config.py) | `Settings.from_env()` | [services/tts/tests/test_config.py](services/tts/tests/test_config.py) | `test_settings_*` | COVERED (unit tests executed) |

### Coverage Gaps
- No tests for `main()` event loop, Kafka publish/consume loop, or MinIO integration pathways.
- `select_audio_transport` internal key branch missing lines 81-83 in `tts_service.processing` (coverage 96%).

### Comparison to Test Plan
- **Tests Planned**: 6 (3 unit, 2 integration, 1 e2e)
- **Tests Implemented**: 6 unit (including Kokoro/config/main)
- **Tests Missing**: Service-level latency/RTF evidence
- **Tests Added Beyond Plan**: None

## Analyzer Verification Gate
- Ruff lint: PASS on TTS service sources/tests and shared events model (0 issues).
- Dead-code scan: Not executed (not required for this pass).

## Test Execution Results

### Unit Tests
- **Command**: `/home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python -m pytest services/tts/tests/test_processing.py services/tts/tests/test_main.py services/tts/tests/test_kokoro.py services/tts/tests/test_config.py`
- **Status**: PASS (17 tests)
- **Output**: All tests passed (17/17).
- **Coverage Percentage**: Not measured for full suite.

### Unit Test Coverage
- **Command**: `/home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python -m pytest services/tts/tests/test_processing.py --cov=tts_service.processing --cov-report=term-missing`
- **Status**: PASS (10 tests)
- **Coverage Percentage**: 96% for `tts_service.processing` (missing lines 83-85)

### Integration Tests
- **Command**: Not executed (requires Kafka/Schema Registry/MinIO).
- **Status**: NOT RUN
- **Output**: N/A

### E2E Tests
- **Command**: `TTS_SMOKE_PHRASE_SET=curated TTS_SMOKE_PHRASE_LIMIT=5 /home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python tests/e2e/tts_pipeline_smoke.py`
- **Status**: FAIL
- **Output**: Timed out waiting for `AudioSynthesisEvent`.

### E2E Tests (URI/MinIO)
- **Command**: `EXPECT_PAYLOAD_MODE=URI TTS_SMOKE_PHRASE_SET=curated TTS_SMOKE_PHRASE_LIMIT=3 /home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python tests/e2e/tts_pipeline_smoke.py`
- **Status**: FAIL
- **Output**: Timed out waiting for `AudioSynthesisEvent`.

## QA Assessment
- Unit tests executed successfully; processing coverage is 96% and meets the 90% threshold.
- E2E pipeline smoke tests failed (inline and URI) due to timeouts waiting for `AudioSynthesisEvent` while the Docker stack was running. Translation service logs show Schema Registry connection errors, which likely blocked downstream processing.
- Service-level latency/RTF evidence remains a follow-up for UAT readiness.

## QA Status
**QA Failed** — e2e smoke tests timed out; infrastructure readiness needs remediation before UAT handoff.