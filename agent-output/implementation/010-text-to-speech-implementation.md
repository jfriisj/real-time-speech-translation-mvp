# Implementation Report: 010-text-to-speech

## Plan Reference
- Plan: agent-output/planning/010-text-to-speech-plan.md (Rev 35)
- Critique: agent-output/critiques/010-text-to-speech-plan-critique.md (Revision 11)

## Date
2026-01-28

## Changelog
| Date | Handoff | Request | Summary |
|------|---------|---------|---------|
| 2026-01-27 | User → Implementer | Start implementation | Implemented Claim Check key alignment and internal key handling; updated tests and smoke path handling; ran lint + unit tests. |
| 2026-01-27 | User → Implementer | Refresh report for approved plan | Updated report references to Plan Rev 35 / Critique Rev 10; no new code changes in this refresh. |
| 2026-01-28 | User → Implementer | Continue implementation + evidence | Added integrity metadata, pinned model revision, aligned compose defaults, ran unit + e2e smoke tests, and captured MinIO lifecycle evidence. |

## Implementation Summary (what + how delivers value)
Extended the TTS output contract with optional integrity metadata (`audio_sha256`, `audio_size_bytes`) and emitted these values on each synthesized event. Pinned the Kokoro model revision to a fixed commit hash and surfaced it via `TTS_MODEL_REVISION` for supply-chain stability. Aligned compose defaults with the v0.5.0 contract by defaulting `TTS_AUDIO_URI_MODE=internal` and pinning MinIO images by digest while allowing credential overrides. Ran unit tests, coverage, and end-to-end smoke tests for inline and URI payload paths. These changes reinforce Claim Check correctness and security while providing concrete evidence of both transport modes.

## Milestones Completed
- [x] M1: Schema Definition & Shared Contract — added integrity metadata to schema + shared payload model
- [x] M4: Event Loop & Payload Management (Claim Check) — key alignment + fallback behavior + integrity metadata
- [ ] M2: TTS Service Scaffold & Pluggable Factory
- [ ] M3: Kokoro ONNX Integration & Tokenization
- [ ] M5: Version Management & Release

## Files Modified
| Path | Changes | Lines |
|------|---------|-------|
| docker-compose.yml | Pinned MinIO images by digest; default `TTS_AUDIO_URI_MODE=internal`; added model revision env; made MinIO creds overridable. | N/A |
| shared/schemas/avro/AudioSynthesisEvent.avsc | Added optional `audio_sha256` + `audio_size_bytes` fields. | N/A |
| shared/speech-lib/src/speech_lib/events.py | Added integrity metadata to `AudioSynthesisPayload` + validation. | N/A |
| services/tts/src/tts_service/config.py | Added `TTS_MODEL_REVISION` setting. | N/A |
| services/tts/src/tts_service/factory.py | Passed model revision into Kokoro synthesizer. | N/A |
| services/tts/src/tts_service/kokoro.py | Pinned HF downloads to model revision. | N/A |
| services/tts/src/tts_service/main.py | Emit `audio_sha256` + `audio_size_bytes` in payload/logs. | N/A |
| services/tts/src/tts_service/processing.py | Added integrity metadata fields to payload + output mapping. | N/A |
| services/tts/tests/test_config.py | Added model revision assertions. | N/A |
| services/tts/tests/test_kokoro.py | Updated synthesizer tests for revision. | N/A |
| services/tts/tests/test_processing.py | Added integrity metadata assertions. | N/A |

## Files Created
| Path | Purpose |
|------|---------|
| _None_ | _No new files created in this change._ |

## Code Quality Validation
- [x] Ruff lint (local CLI; analyzer tool unavailable) on modified files: no issues.
- [ ] Dead-code scan (Vulture) not run (optional).
- [x] Unit tests: pytest (17 tests) passed.
- [x] E2E tests: inline + URI payload smoke tests passed.
- [ ] Integration tests not run (Kafka/Schema Registry/MinIO required beyond smoke path).
Note: TODO/FIXME scan matched existing `MockSynthesizer` references and historical docs; no new TODO/FIXME markers were introduced in the updated files.

## Value Statement Validation
**Original**: As a User, I want to hear the translated text spoken naturally, So that I can consume the translation hands-free.

**Status**: Partially validated. Claim Check behavior now aligns with the contract, but service-level audio evidence and integration runs are still outstanding.

## Test Coverage (unit/integration)
- Unit: services/tts/tests/test_processing.py, services/tts/tests/test_main.py, services/tts/tests/test_kokoro.py, services/tts/tests/test_config.py
- Integration: Not run

## Test Execution Results
| Command | Result | Issues |
|---------|--------|--------|
| /home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python -m pytest services/tts/tests/test_processing.py services/tts/tests/test_main.py services/tts/tests/test_kokoro.py services/tts/tests/test_config.py | Pass (17 tests) | None |
| /home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python -m pytest services/tts/tests/test_processing.py --cov=tts_service.processing --cov-report=term-missing | Pass (96% coverage) | Missing lines 83-85 (storage failure guard) |
| TTS_SMOKE_PHRASE_SET=curated TTS_SMOKE_PHRASE_LIMIT=5 /home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python tests/e2e/tts_pipeline_smoke.py | Pass (5/5) | None |
| EXPECT_PAYLOAD_MODE=URI TTS_SMOKE_PHRASE_SET=curated TTS_SMOKE_PHRASE_LIMIT=3 /home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python tests/e2e/tts_pipeline_smoke.py | Pass (3/3) | None |
| docker run --rm -v /tmp/mc-config:/root/.mc --network real-time-speech-translation-mvp_speech_net minio/mc@sha256:a7fe349ef4bd8521fb8497f55c6042871b2ae640607cf99d9bede5e9bdf11727 ilm ls --json local/tts-audio | Pass (JSON shows Days=1 rule) | Output: {"config":{"Rules":[{"Expiration":{"Days":1},"ID":"expire-tts-audio","Status":"Enabled"}]}} |

## Outstanding Items
- Capture service-level latency/RTF logs for curated phrase set and record artifacts.
- Capture intelligibility evidence (manual listening) and speed-control behavior at service level.
- Confirm non-local environments override default MinIO credentials and enforce `TTS_AUDIO_URI_MODE=internal`.

## Next Steps
1. Capture latency/RTF logs and intelligibility evidence for UAT.
2. Re-run QA/UAT after evidence capture.

## Assumption Documentation
| Description | Rationale | Risk | Validation Method | Escalation |
|-------------|-----------|------|-------------------|------------|
| Internal `audio_uri` is a key (not URL) for all services | Matches plan and Findings 020 | Integration break if a consumer expects URLs | Validate via integration tests and Gateway presign path | SAME-DAY |
