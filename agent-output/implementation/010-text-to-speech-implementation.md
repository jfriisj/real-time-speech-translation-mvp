# Implementation Report: 010-text-to-speech (TTS)

## Plan Reference
- Plan: agent-output/planning/010-text-to-speech-plan.md (Rev 26)
- Critique: agent-output/critiques/010-text-to-speech-plan-critique.md (Approved, Revision 4)
- Architecture Findings: agent-output/architecture/017-text-to-speech-plan-architecture-findings.md

## Date
- 2026-01-27

## Changelog
| Date | Handoff | Request | Summary |
|------|---------|---------|---------|
| 2026-01-27 | User → Implementer | Implementation report creation | Initialized implementation report scaffold for Plan 010 (TTS). |

## Implementation Summary (What + How it delivers value)
- Implemented the `tts` service to consume `TextTranslatedEvent` and emit `AudioSynthesisEvent` using a pluggable synthesizer with Kokoro ONNX as the default engine. Added claim-check payload handling (inline vs URI) with optional object storage, speaker context pass-through, and trace header propagation to preserve end-to-end context. Updated shared contracts and helpers to enforce the 1.25 MiB payload guardrail and to support internal object keys or presigned URLs.

## Milestones Completed
- [x] M1: Schema Definition & Shared Contract
- [x] M2: TTS Service Scaffold & Pluggable Factory
- [x] M3: Kokoro ONNX Integration & Tokenization
- [x] M4: Event Loop & Payload Management (Claim Check)
- [x] M5: Version Management & Release

## Files Modified
| Path | Changes | Lines |
|------|---------|-------|
| shared/speech-lib/src/speech_lib/constants.py | Align inline payload cap to 1.25 MiB. | N/A |
| shared/speech-lib/src/speech_lib/events.py | Add speaker context + text snippet to `AudioSynthesisPayload`. | N/A |
| shared/speech-lib/src/speech_lib/producer.py | Support optional Kafka headers. | N/A |
| shared/speech-lib/src/speech_lib/storage.py | Add internal key option + presign helper. | N/A |
| shared/schemas/avro/AudioSynthesisEvent.avsc | Add speaker context + text snippet fields. | N/A |
| docker-compose.yml | Align payload limits + add `TTS_AUDIO_URI_MODE`. | N/A |
| tests/e2e/tts_pipeline_smoke.py | Handle internal `s3://` keys via presign. | N/A |
| CHANGELOG.md | Update 0.5.0 release notes. | N/A |
| package.json | Bump version to 0.5.0. | N/A |

## Files Created
| Path | Purpose |
|------|---------|
| services/tts/README.md | TTS service documentation. |
| services/tts/Dockerfile | TTS service container build. |
| services/tts/pyproject.toml | TTS service package metadata. |
| services/tts/minio-lifecycle.json | MinIO lifecycle rule (24h retention). |
| services/tts/src/tts_service/__init__.py | Package init. |
| services/tts/src/tts_service/audio.py | WAV encoding + speed handling utilities. |
| services/tts/src/tts_service/config.py | TTS runtime configuration. |
| services/tts/src/tts_service/factory.py | Synthesizer factory. |
| services/tts/src/tts_service/kokoro.py | Kokoro ONNX synthesizer + tokenizer. |
| services/tts/src/tts_service/processing.py | Request extraction + payload building. |
| services/tts/src/tts_service/synthesizer.py | Synthesizer interface + mock engine. |
| services/tts/src/tts_service/main.py | TTS service entrypoint. |
| services/tts/tests/test_processing.py | Unit tests for TTS processing. |

## Code Quality Validation
- [x] Linting (Ruff): Clean on changed Python files.
- [x] Tests: `services/tts/tests`.
- [ ] Compatibility Checks: ONNX runtime not installed in Python 3.14 env (expected; Docker uses Python 3.11).

## Value Statement Validation
- **Original**: As a User, I want to hear the translated text spoken naturally, So that I can consume the translation hands-free.
- **Implementation Delivers**: The service now synthesizes audio from translated text and emits `AudioSynthesisEvent` with inline or URI payloads, enabling hands-free consumption once runtime model validation is completed.

## Test Coverage (Unit/Integration)
- **Unit Tests**: `services/tts/tests/test_processing.py`
- **Integration Tests**: Not run in this handoff.

## Test Execution Results
| Command | Result | Issues | Coverage |
|---------|--------|--------|----------|
| `/home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python -m pytest /home/jonfriis/github/real-time-speech-translation-mvp/services/tts/tests` | Pass (7 tests) | None | N/A |

## Outstanding Items
- Confirm Kokoro tokenizer requirements and validate output quality with real model runtime.
- Capture service-level latency/RTF evidence and intelligibility proof for UAT.
- Capture MinIO lifecycle retention proof artifact.
- Clarify non-blocking critique questions (DLQ for >500 chars, rollback policy vs constraint, minimal metrics contract).

## Next Steps
- Run service-level smoke tests (TTS pipeline) and capture evidence artifacts.
- Update QA/UAT artifacts after evidence capture.
- Prepare QA handoff and subsequent UAT.

## Assumptions & Open Questions
| Description | Rationale | Risk | Validation Method | Escalation |
|-------------|-----------|------|-------------------|------------|
| Tokenizer requirements for Kokoro ONNX must be confirmed. | Plan depends on correct phonemization pipeline. | Incorrect synthesis or model mismatch. | Validate with model docs and smoke test. | SAME-DAY |
| Storage fallback behavior is log-and-drop for large payloads when storage disabled. | Plan states drop with warning, but DLQ behavior not specified. | Data loss without traceability. | Decide DLQ vs log-only with product owner. | SAME-DAY |
| Rollback to “system-speech fallback / mock” may conflict with “must use Kokoro-82M” constraint. | Plan allows rollback; critique flagged potential conflict. | Release constraint violation. | Confirm scope: demo-only vs release. | SAME-DAY |
| Minimal metrics contract (counters/histograms) in v0.5.0 is optional. | Plan mandates logging/tracing but not metrics. | Reduced observability. | Align with roadmap/architect. | MINOR |
