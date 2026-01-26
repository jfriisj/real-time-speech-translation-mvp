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
| 2026-01-26 | User | Mark implementation as PARTIAL | Blocked QA/UAT until plan-critical items are resolved. |
| 2026-01-26 | User | Refactor storage to speech-lib | Moved `ObjectStorage` into `speech-lib`, updated imports/tests, and added boto3 dependency. |
| 2026-01-26 | User | Remove legacy synthesizer | Deleted `synthesizer.py` and `test_legacy_synthesizer.py`; reran unit tests. |

## Implementation Summary (what + how delivers value)
- Existing implementation delivers Kokoro ONNX inference, input caps, and dual-mode payload handling for the TTS pipeline, enabling hands-free playback as described in the plan.
- Refactored storage adapter into shared `speech-lib` to enable reuse across services and reduce TTS-specific dependencies.
**Status Note**: Implementation is **PARTIAL** pending plan-critical clarifications and remaining refactor/integration items.

## Milestones Completed
- [x] Implement Kokoro ONNX real inference (phoneme mapping + ONNX Runtime calls).
- [x] Voice vector parsing and default speaker fallback (`af_bella`).
- [x] Input length cap enforced (500 chars).
- [x] Integration validation for inline payload mode (Kafka + Schema Registry + MinIO + TTS).
- [x] Integration validation for URI payload mode (forced via inline cap override).
- [x] Updated root changelog entry for v0.5.0.

## Files Modified
| Path | Changes | Lines |
|------|---------|-------|
| shared/speech-lib/src/speech_lib/storage.py | New shared `ObjectStorage` adapter | n/a |
| shared/speech-lib/src/speech_lib/__init__.py | Exported `ObjectStorage` | n/a |
| shared/speech-lib/pyproject.toml | Added `boto3` dependency | n/a |
| services/tts/src/tts_service/main.py | Import `ObjectStorage` from `speech_lib` | n/a |
| services/tts/tests/test_storage.py | Pointed storage tests at `speech_lib.storage` | n/a |
| services/tts/tests/conftest.py | Added `speech-lib` to test import path | n/a |
| services/tts/tests/test_legacy_synthesizer.py | Removed legacy tests | n/a |
| services/tts/src/tts_service/synthesizer.py | Removed legacy IndexTTS implementation | n/a |
| services/tts/src/tts_service/synthesizer_kokoro.py | Real inference path, provider/env handling, duration calculation | n/a |
| services/tts/src/tts_service/main.py | Input text cap enforcement | n/a |
| services/tts/tests/test_synthesizer.py | Tokenizer fixture + mocked G2P for unit tests | n/a |
| CHANGELOG.md | Added 0.5.0 release notes | n/a |

## Files Created
| Path | Purpose |
|------|---------|
| shared/speech-lib/src/speech_lib/storage.py | Shared storage adapter for MinIO/S3 |

## Code Quality Validation
- [ ] Ruff lint (changed files): not run in this update.
- [ ] Ruff format: not run (not required).
- [ ] Dead-code scan: not run (optional).
- [ ] Pre-handoff scan: not run in this update.

## Value Statement Validation
**Original**: “As a User, I want to hear the translated text spoken naturally, so that I can consume the translation hands-free.”

**Implementation delivers**: The TTS service now executes real Kokoro ONNX inference and produces WAV audio for downstream playback, enabling hands-free consumption with the dual-mode transport and correlation metadata required for the pipeline.

## Test Coverage (unit/integration)
- **Unit**: `services/tts/tests` suite executed.
- **Integration**: TTS pipeline smoke tests executed for inline and URI payload modes.

## Test Execution Results
| Command | Results | Issues | Coverage |
|---------|---------|--------|----------|
| `/home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python -m pytest services/tts/tests/test_synthesizer.py services/tts/tests/test_main.py services/tts/tests/test_storage.py services/tts/tests/test_audio_helpers.py services/tts/tests/test_tts_processing.py` | PASS (13 tests) | None | n/a |
| `pytest services/tts/tests/test_synthesizer.py services/tts/tests/test_main.py services/tts/tests/test_storage.py services/tts/tests/test_audio_helpers.py services/tts/tests/test_tts_processing.py` (via VS Code test runner) | PASS (11 tests) | None | n/a |
| `/home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python tests/e2e/tts_pipeline_smoke.py` | PASS | None | n/a |
| `EXPECT_PAYLOAD_MODE=URI MINIO_PUBLIC_ENDPOINT=http://127.0.0.1:9000 /home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python tests/e2e/tts_pipeline_smoke.py` | PASS | None | n/a |

## Outstanding Items
- **Plan Critique Criticals**: Resolve CPU/GPU alignment vs roadmap, define observable speed-control outcomes, and remove duplicated Step 5 section in the plan.
- **Integration Validation**: Re-run integration tests using forced URI mode and negative 404/timeout path evidence as required by Rev 13.
- **Lifecycle**: Observe actual MinIO deletion after 24h (rule verified; expiration not yet observed).
- **Access**: Unable to read QA/UAT prompt docs outside workspace; required checks not captured here.

## QA/UAT Blocker
QA and UAT are **blocked** until the plan-critical items and refactor/integration evidence above are resolved.

## Next Steps (QA then UAT)
- QA: Execute QA plan for Plan 010 with focus on integration evidence and lifecycle expiration checks.
- UAT: Validate audio quality and RTF/latency targets on reference hardware.

## Assumption Documentation
### Assumption 1: MinIO lifecycle expiration will match the configured 24h rule
- **Description**: Objects in the `tts-audio` bucket will be deleted after 24 hours as configured.
- **Rationale**: The rule is present and enabled; expiration enforcement is external to the service.
- **Risk**: Storage cleanup could silently fail, impacting data retention guarantees.
- **Validation method**: Re-check object existence after 24h and capture deletion logs.
- **Escalation evidence**: Objects persist beyond 24h → **Moderate** (escalate to infrastructure).
