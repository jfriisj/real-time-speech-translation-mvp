# Implementation 010: Text-to-Speech (TTS) Service (Kokoro ONNX)

## Plan Reference
agent-output/planning/010-text-to-speech-plan.md

## Date
2026-01-26

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-26 | Planner | Implement Plan 010 Rev 10 | Implemented real Kokoro inference, enforced input caps, updated tests, and ran integration smoke tests (inline + URI). |
| 2026-01-26 | User | Align report to Plan 010 Rev 11 | Documented critique constraints and clarified outstanding items; no code changes. |
| 2026-01-26 | User | Deliver implementation report for Plan 010 Rev 13 | Refreshed report to reflect Rev 13 requirements and critique; no new code changes in this update. |
| 2026-01-26 | User | Refactor storage to speech-lib | Moved `ObjectStorage` into `speech-lib`, updated imports/tests, and added boto3 dependency. |
| 2026-01-26 | User | Remove legacy synthesizer | Deleted `synthesizer.py` and `test_legacy_synthesizer.py`; reran unit tests. |
| 2026-01-26 | User | Implement Rev 20 deltas | Reject overlong input text, add unit coverage, capture MinIO lifecycle evidence, and log GPU validation follow-up. |

## Implementation Summary (what + how delivers value)
- Enforced plan-aligned input handling by rejecting `payload.text` over 500 characters with a soft failure and warning, preserving deterministic pipeline behavior.
- Added unit coverage for the new input-length behavior.
- Captured MinIO lifecycle retention proof and documented the GPU validation follow-up plan for the deferred GPU profile.

## Milestones Completed
- [x] Implement Kokoro ONNX real inference (phoneme mapping + ONNX Runtime calls).
- [x] Voice vector parsing and default speaker fallback (`af_bella`).
- [x] Input length cap enforced (500 chars) with soft failure behavior.
- [x] Integration validation for inline payload mode (Kafka + Schema Registry + MinIO + TTS).
- [x] Integration validation for URI payload mode (forced via inline cap override).
- [x] MinIO lifecycle rule inspected and recorded.
- [x] GPU validation follow-up artifact created.

## Files Modified
| Path | Changes | Lines |
|------|---------|-------|
| services/tts/src/tts_service/main.py | Reject overlong input text; log soft failure | n/a |
| services/tts/tests/test_tts_processing.py | Added overlong text rejection test | n/a |

## Files Created
| Path | Purpose |
|------|---------|
| agent-output/validation/retention-proof.md | Evidence of MinIO 24h lifecycle rule |
| agent-output/planning/future/011-gpu-validation.md | Follow-up plan for GPU profile validation |

## Code Quality Validation
- [x] Ruff lint (changed files): clean (`main.py`, `test_tts_processing.py`).
- [x] Dead-code scan (changed files): no high-confidence findings.
- [x] Pre-handoff scan: TODO/FIXME/mock hits are limited to documentation and agent instructions; no new code scaffolding introduced.

## Value Statement Validation
**Original**: “As a User, I want to receive intelligible spoken audio for translated text, so that I can consume the translation without reading.”

**Implementation delivers**: The TTS service produces WAV audio via Kokoro ONNX with dual-mode transport and now enforces input guards. Intelligibility evidence remains pending (see Outstanding Items).

## Test Coverage (unit/integration)
- **Unit**: `services/tts/tests` suite executed.
- **Integration**: Not re-run in this update (prior evidence exists).

## Test Execution Results
| Command | Results | Issues | Coverage |
|---------|---------|--------|----------|
| `/home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python -m pytest services/tts/tests/test_tts_processing.py services/tts/tests/test_synthesizer.py services/tts/tests/test_main.py services/tts/tests/test_storage.py services/tts/tests/test_audio_helpers.py` | PASS (14 tests) | None | n/a |

## Outstanding Items
- **Value evidence**: `agent-output/validation/quality_report.md` (human intelligibility verification) not captured.
- **Performance evidence**: service-level latency/RTF baseline in `agent-output/validation/performance_report.md` still reflects synthesis-only timing.
- **Speed control evidence**: service-level `TTS_SPEED` validation not captured.
- **Lifecycle expiry**: 24h deletion observed in MinIO is not yet evidenced (rule is verified).

## Next Steps (QA then UAT)
- QA: Re-run integration smoke tests if required and validate service-level observability fields.
- UAT: Capture intelligibility, speed-control, and service-latency evidence on reference hardware.

## Assumption Documentation
### Assumption 1: MinIO lifecycle expiration will match the configured 24h rule
- **Description**: Objects in the `tts-audio` bucket will be deleted after 24 hours as configured.
- **Rationale**: The lifecycle rule is present and enabled (see retention proof).
- **Risk**: Storage cleanup could silently fail, impacting data retention guarantees.
- **Validation method**: Re-check object existence after 24h and capture deletion evidence.
- **Escalation evidence**: Objects persist beyond 24h → **Moderate** (escalate to infrastructure).
