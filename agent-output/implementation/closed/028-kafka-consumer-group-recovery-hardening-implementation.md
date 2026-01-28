---
ID: 028
Origin: 028
UUID: 4f6b2c1d
Status: Released (v0.5.0)
---

# Implementation 028: Kafka Consumer Group Recovery Hardening

## Plan Reference
- [agent-output/planning/closed/028-kafka-consumer-group-recovery-hardening-plan.md](agent-output/planning/closed/028-kafka-consumer-group-recovery-hardening-plan.md)

## Date
2026-01-28

## Changelog
| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-28 | Begin implementation | Added shared consumer tuning helper + validation, updated service configs + consumer telemetry, and updated TTS smoke modes. |
| 2026-01-28 | Release artifacts | Added Plan 028 entries to CHANGELOG for v0.5.0. |
| 2026-01-28 | Baseline evidence capture | Rebuilt compose stack, captured TTS + VAD baseline recovery telemetry, noted VAD→ASR timeout. |
| 2026-01-28 | ASR pipeline fix | Updated ASR transcriber input handling to avoid transformers num_frames errors; VAD smoke now passes. |
| 2026-01-28 | Stage 1 commit (DevOps) | Implementation document moved to closed/ and marked committed for v0.5.0 release readiness. |
| 2026-01-28 | Release v0.5.0 | Stage 2 release executed; implementation shipped in v0.5.0 and lifecycle status set to Released. |
| 2026-01-28 | Code review fix | Added on-assign support in KafkaConsumerWrapper and removed direct consumer subscribe calls in services. |

## Implementation Summary
Implemented the standardized Kafka consumer tuning interface and low-volume telemetry across ASR/VAD/Translation/TTS. Added a shared, pure consumer tuning builder and validation helper. Updated TTS smoke tooling with explicit steady-state vs cold-start modes and created the baseline evidence artifact template. Added release notes to the v0.5.0 CHANGELOG. Fixed ASR transcriber input handling to avoid transformers `num_frames` errors; VAD pipeline smoke now completes. Added on-assign support in KafkaConsumerWrapper so services no longer access the underlying consumer directly. These changes align with the platform boundary (no shared-lib orchestration) and improve diagnosability of post-restart delays.

## Milestones Completed
- [x] Milestone 2 (consumer tuning + shared helper)
- [x] Milestone 3 (standardized telemetry events)
- [x] Milestone 4 (smoke-mode separation for TTS smoke tooling)
- [x] Milestone 1 baseline measurement (TTS + VAD baseline captured)
- [x] Milestone 5 release artifacts (CHANGELOG updated for v0.5.0)

## Files Modified
| Path | Changes | Lines |
|------|---------|-------|
| agent-output/planning/closed/028-kafka-consumer-group-recovery-hardening-plan.md | Status updated to In Progress | N/A |
| CHANGELOG.md | Added Plan 028 release notes under v0.5.0 | N/A |
| agent-output/analysis/028-kafka-consumer-group-recovery-baseline.md | Recorded baseline recovery telemetry for TTS + VAD | N/A |
| services/asr/src/asr_service/transcriber.py | Adjusted ASR pipeline invocation to avoid Whisper num_frames errors | N/A |
| services/asr/tests/test_transcriber.py | Added/updated unit tests for ASR pipeline input handling | N/A |
| shared/speech-lib/src/speech_lib/__init__.py | Export consumer tuning helpers | N/A |
| services/asr/src/asr_service/config.py | Added consumer tuning env settings | N/A |
| services/asr/src/asr_service/main.py | Added consumer tuning validation/config + telemetry | N/A |
| services/vad/src/vad_service/config.py | Added consumer tuning env settings | N/A |
| services/vad/src/vad_service/main.py | Added consumer tuning validation/config + telemetry | N/A |
| services/translation/src/translation_service/config.py | Added consumer tuning env settings | N/A |
| services/translation/src/translation_service/main.py | Added consumer tuning validation/config + telemetry | N/A |
| services/tts/src/tts_service/config.py | Added consumer tuning env settings | N/A |
| services/tts/src/tts_service/main.py | Added consumer tuning validation/config + telemetry | N/A |
| services/vad/tests/test_processing.py | Updated Settings constructor to include new fields | N/A |
| tests/e2e/tts_pipeline_smoke.py | Added steady-state vs cold-start mode + timeout separation | N/A |
| shared/speech-lib/src/speech_lib/consumer.py | Added on-assign support for KafkaConsumerWrapper | N/A |
| shared/speech-lib/tests/test_consumer.py | Added test for on-assign support | N/A |
| services/asr/src/asr_service/main.py | Use wrapper on-assign instead of direct subscribe | N/A |
| services/vad/src/vad_service/main.py | Use wrapper on-assign instead of direct subscribe | N/A |
| services/translation/src/translation_service/main.py | Use wrapper on-assign instead of direct subscribe | N/A |
| services/tts/src/tts_service/main.py | Use wrapper on-assign instead of direct subscribe | N/A |

## Files Created
| Path | Purpose |
|------|---------|
| shared/speech-lib/src/speech_lib/consumer_config.py | Pure consumer tuning builder + validator |
| shared/speech-lib/tests/test_consumer_config.py | TDD tests for consumer tuning helper |
| agent-output/analysis/028-kafka-consumer-group-recovery-baseline.md | Baseline evidence template (measurements pending) |

## Code Quality Validation
- [x] Targeted unit tests executed
- [ ] Full unit test suite (not run)
- [x] Integration/E2E smoke (TTS cold-start pass; VAD pipeline pass)

## Value Statement Validation
**Original**: “As an operator/contributor, I want services to recover Kafka consumption quickly after restarts, so that end-to-end smoke tests and development bring-up are reliable and do not fail due to predictable consumer group stabilization delays.”

**Implementation delivers**:
- Standardized consumer tuning knobs with validation to reduce restart tail latency.
- Low-volume, structured telemetry to pinpoint where delays occur.
- Smoke tooling now explicitly separates steady-state vs cold-start scenarios.

## TDD Compliance

| Function/Class | Test File | Test Written First? | Failure Verified? | Failure Reason | Pass After Impl? |
|----------------|-----------|---------------------|-------------------|----------------|------------------|
| `ConsumerTuning` | `shared/speech-lib/tests/test_consumer_config.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `build_consumer_config()` | `shared/speech-lib/tests/test_consumer_config.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `validate_consumer_tuning()` | `shared/speech-lib/tests/test_consumer_config.py` | ✅ Yes | ✅ Yes | ModuleNotFoundError | ✅ Yes |
| `Transcriber.transcribe()` | `services/asr/tests/test_transcriber.py` | ✅ Yes | ✅ Yes | AssertionError (missing raw/stride input contract) | ✅ Yes |
| `KafkaConsumerWrapper.from_confluent()` | `shared/speech-lib/tests/test_consumer.py` | ✅ Yes | ✅ Yes | TypeError (missing on_assign arg) | ✅ Yes |

## Test Coverage
- Unit: consumer tuning helper tests added and passing.
- Integration/E2E: not run in this implementation step.

## Test Execution Results

1) TDD gate (expected fail):
- `pytest shared/speech-lib/tests/test_consumer_config.py`
- Result: **ModuleNotFoundError** for `speech_lib.consumer_config` (expected pre-implementation)

2) Post-implementation targeted tests:
- `pytest shared/speech-lib/tests/test_consumer_config.py services/vad/tests/test_processing.py`
- Result: **8 passed** (after fixing Settings fixture and required args)

3) Compose rebuild + smoke evidence:
- `docker compose up -d --build`
- `TTS_SMOKE_MODE=steady-state python tests/e2e/tts_pipeline_smoke.py` → **PASS**
- `TTS_SMOKE_MODE=cold-start python tests/e2e/tts_pipeline_smoke.py` → **PASS**

4) ASR transcriber unit tests (TDD):
- `PYTHONPATH=services/asr/src python -m pytest services/asr/tests/test_transcriber.py`
- Result: **2 passed**

5) ASR rebuild + VAD smoke:
- `docker compose up -d --build asr-service`
- `python tests/e2e/vad_pipeline_smoke.py` → **PASS**

6) Kafka consumer wrapper on-assign tests (TDD):
- `PYTHONPATH=shared/speech-lib/src python -m pytest shared/speech-lib/tests/test_consumer.py -k from_confluent_passes_on_assign`
- Result: **failed** (TypeError: `from_confluent()` unexpected `on_assign`) before implementation
- Result: **passed** after implementation

## Outstanding Items
- QA/UAT prompt files in `~/.config/Code/User/prompts/` are not accessible from the workspace; QA/UAT steps should be validated when those prompts are available.

## Next Steps
1. Capture baseline and post-change measurements per Plan 028 (update baseline artifact).
2. Run wider test suite and any required E2E smoke for cold-start vs steady-state modes.
3. Update release artifacts (CHANGELOG + versioned files) for v0.5.0.
4. Hand off to QA, then UAT.