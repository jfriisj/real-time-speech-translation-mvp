# QA Report: Plan 009 Voice Activity Detection (VAD) Service

**Plan Reference**: agent-output/planning/009-voice-activity-detection-plan.md
**QA Status**: QA Failed
**QA Specialist**: qa

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-19 | Planner | Test strategy for Plan 009 VAD | Authored QA strategy aligned to VAD acceptance criteria and architecture constraints. |
| 2026-01-19 | Implementer | Implementation complete, ready for testing | Executed unit tests + Ruff gate; ran VAD → ASR → Translation smoke test; legacy pipeline regression still pending. |
| 2026-01-19 | QA | Retest after plan revision sync | Re-ran Ruff gate, unit tests, and VAD pipeline smoke test; legacy Pipeline A regression + success-metric validation still pending. |

## Timeline
- **Test Strategy Started**: 2026-01-19
- **Test Strategy Completed**: 2026-01-19
- **Implementation Received**: 2026-01-19
- **Testing Started**: 2026-01-19
- **Testing Completed**: 2026-01-19
- **Final Status**: QA Failed

## Test Strategy (Pre-Implementation)
Focus on end-to-end segmentation correctness, schema compliance, and ASR dual-mode consumption while preserving ordering guarantees via `correlation_id`.

### Testing Infrastructure Requirements
**Test Frameworks Needed**:
- pytest (workspace default)

**Testing Libraries Needed**:
- confluent-kafka, numpy, librosa, soundfile, onnxruntime, huggingface-hub

**Configuration Files Needed**:
- docker-compose.yml (Kafka + Schema Registry + services)

**Build Tooling Changes Needed**:
- None (existing Python + Docker tooling)

**Dependencies to Install**:
```bash
pip install -r tests/requirements.txt
pip install -e shared/speech-lib
pip install -e services/vad
```

### Required Unit Tests
- VAD segmentation detects speech vs silence on synthetic WAV input.
- `SpeechSegmentEvent` payload validation for required fields and WAV-only constraint.
- ASR schema selection for `ASR_INPUT_TOPIC`.

### Required Integration Tests
- Pipeline B smoke: Ingress → VAD → ASR → Translation.
- Ordering verification: multi-segment audio arrives in `segment_index` order.
- Regression: Pipeline A (legacy) still works when ASR consumes `speech.audio.ingress`.

### Acceptance Criteria
- VAD service runs in Docker and registers `SpeechSegmentEvent` schema.
- `SpeechSegmentEvent` emitted only for speech segments.
- `correlation_id` preserved across VAD → ASR → Translation.
- Success metric: ≥ 30% audio duration reduction on sparse speech dataset.

## Implementation Review (Post-Implementation)

### Code Changes Summary
- Added `SpeechSegmentEvent` schema and `SpeechSegmentPayload` validation.
- Added VAD service (consumer/producer + segmentation logic) with ONNX optional inference.
- Updated ASR to support `ASR_INPUT_TOPIC` and `SpeechSegmentEvent` input.
- Updated Docker Compose to include VAD and default ASR to `speech.audio.speech_segment`.

## Test Coverage Analysis
### New/Modified Code
| File | Function/Class | Test File | Test Case | Coverage Status |
|------|---------------|-----------|-----------|-----------------|
| shared/speech-lib/src/speech_lib/events.py | `SpeechSegmentPayload.validate()` | shared/speech-lib/tests/test_events.py | `test_speech_segment_payload_validation` | COVERED |
| services/vad/src/vad_service/processing.py | `build_segments()` | services/vad/tests/test_processing.py | `test_build_segments_detects_speech` | COVERED |
| services/asr/src/asr_service/main.py | `resolve_input_schema_name()` | services/asr/tests/test_processing.py | `test_resolve_input_schema_name` | COVERED |

### Coverage Gaps
- Legacy Pipeline A regression test not executed (ASR default is VAD topic).
- Ordering verification across Kafka partitions is untested (single-run smoke only).
- Success metric validation (≥ 30% reduction) not executed.

### Comparison to Test Plan
- **Tests Planned**: 6 (3 unit, 3 integration)
- **Tests Implemented**: 5 (3 unit, 2 integration)
- **Tests Missing**: Pipeline A regression
- **Tests Added Beyond Plan**: None

## Test Execution Results
### Analyzer Verification Gate
- **Ruff lint**: Pass (no issues) on VAD/ASR/speech-lib changes plus unit tests and e2e smoke test.

### Unit Tests
- **Command**: pytest shared/speech-lib/tests/test_events.py services/asr/tests/test_processing.py services/vad/tests/test_processing.py
- **Status**: PASS
- **Output**: 6 tests passed.

### Integration Tests
- **Command**: /home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python tests/e2e/vad_pipeline_smoke.py
- **Status**: PASS
- **Output**: PASS: VAD -> ASR -> Translation pipeline produced outputs

## QA Verdict
**QA Failed** — Unit tests and VAD pipeline smoke passed, but legacy Pipeline A regression and success-metric validation are still missing.
