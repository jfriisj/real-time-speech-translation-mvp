# Implementation 010: Text-to-Speech (TTS) Service

## Plan Reference
agent-output/planning/010-text-to-speech-plan.md

## Date
2026-01-25

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-25 | Implement plan | Implemented TTS service, schema updates, MinIO integration, and pass-through speaker context across pipeline. |
| 2026-01-25 | Refresh report | Confirmed alignment with Plan 010 Revision 6; no new code changes in this update. |
| 2026-01-25 | Resolve implementation unknowns | Added presigned MinIO URLs, integration smoke test, release artifacts, and compose fixes. |
| 2026-01-25 | Enforce IndexTTS-2 | Replaced HF pipeline with IndexTTS2 runtime, enforced IndexTeam/IndexTTS-2 usage, and updated container deps. |
| 2026-01-25 | Warmup + smoke attempt | Added TTS model warmup, fixed IndexTTS2 test stub, reran unit tests, and attempted smoke test (timeout during model download). |

## Implementation Summary (what + how delivers value)
- Replaced the generic transformers pipeline with IndexTTS2’s official runtime (`indextts.infer_v2.IndexTTS2`) to satisfy the requirement to use IndexTeam/IndexTTS-2.
- Enforced IndexTTS-2 usage in the TTS service startup and Compose configuration, preventing unsupported model swaps.
- Added IndexTTS-2 model download + prompt handling logic to honor speaker reference inputs while providing a safe default prompt fallback.
- Added a TTS warmup hook to download and load the IndexTTS-2 model before Kafka consumption, preventing long poll stalls on first request.
- Updated the container build to install IndexTTS2 dependencies and the upstream package from GitHub.

## Milestones Completed
- [x] Shared schema updates + new `AudioSynthesisEvent`.
- [x] Speaker context pass-through in ASR/Translation/VAD.
- [x] TTS service implementation with dual-mode transport and MinIO integration.
- [x] MinIO lifecycle rule for 24h retention.
- [x] Tests for new logic and payload semantics.

## Files Modified
| Path | Changes | Lines |
|------|---------|-------|
| docker-compose.yml | Enforced IndexTTS-2 + cache settings + HF_TOKEN passthrough | +3/-1 |
| services/tts/Dockerfile | Install IndexTTS2 deps + package | +7/-1 |
| services/tts/pyproject.toml | Added IndexTTS2 dependencies | +10 |
| services/tts/src/tts_service/synthesizer.py | Implemented IndexTTS2 runtime + warmup hook | +70/-53 |
| services/tts/src/tts_service/main.py | Enforced IndexTTS-2 + warmup before consume | +13/-1 |
| services/tts/src/tts_service/config.py | Added model dir/cache settings | +4 |
| services/tts/tests/test_synthesizer.py | Updated tests for IndexTTS2 stub | +31/-46 |
| services/tts/tests/test_main.py | Patched IndexTTS2 synthesizer | +1 |
| services/tts/README.md | Documented model dir/cache env vars + HF_TOKEN | +3 |

## Files Created
| Path | Purpose |
|------|---------|
| tests/e2e/tts_pipeline_smoke.py | End-to-end TTS pipeline smoke test (inline/URI) |
| package.json | Root-level version metadata (v0.5.0-rc) |
| CHANGELOG.md | Root changelog entry for v0.5.0-rc |
| agent-output/releases/v0.5.0.md | Draft release notes for v0.5.0 |

## Code Quality Validation
- [x] Linting: Ruff lint on updated Python files via analyzer gate.
- [ ] Formatting: Ruff format not executed.
- [x] Dead-code scan: Vulture scan clean on updated Python files via analyzer gate.
- [x] Tests: Unit tests executed (see Test Execution Results).
- [ ] Compatibility: TTS smoke test attempted; timed out during IndexTTS-2 model warmup (see Test Execution Results).
- [x] Pre-handoff scan: TODO/FIXME/mock matches observed in .venv, .pytest_cache, and existing agent-output docs; no new markers introduced in modified source files.

## Value Statement Validation
**Original**: “As a User, I want to hear the translated text spoken naturally, so that I can consume the translation hands-free.”  
**Implementation delivers**: TTS microservice consumes `TextTranslatedEvent` and produces `AudioSynthesisEvent` (inline or MinIO URI), preserves `correlation_id`, and propagates optional speaker context—completing the speech-to-speech loop for hands-free consumption.

## Test Coverage
- **Unit**: Speech-lib, ASR, Translation, VAD, and TTS unit tests updated/added.
- **Integration**: Attempted TTS smoke test; timed out during IndexTTS-2 warmup download.

## Test Execution Results
| Command | Results | Issues | Coverage |
|---------|---------|--------|----------|
| runTests (services/tts/tests) | 14 passed, 0 failed | None reported | Not measured in this run |
| `python tests/e2e/tts_pipeline_smoke.py` | FAILED | Timed out waiting for AudioSynthesisEvent while IndexTTS-2 warmup download was still in progress; logs captured in agent-output/live-testing/artifacts | Not measured |

## Outstanding Items
- IndexTTS-2 runtime validation still pending; warmup download in `speech-tts-service` is slow without HF_TOKEN and the smoke test timed out. Rerun after model download completes or with authenticated HF Hub access.
- MinIO retention lifecycle (24h) is configured, but expiry behavior has not yet been validated with time-based observation.

## Next Steps
- QA: Run integration tests and smoke checks for Kafka + MinIO + TTS flow.
- UAT: Validate audio output quality + latency targets on reference hardware.

## Assumption Documentation
### Assumption 1: IndexTTS-2 downloads and runs in the service container
- **Description**: Service downloads IndexTTS-2 checkpoints via `huggingface_hub.snapshot_download` and runs with `indextts.infer_v2.IndexTTS2`.
- **Rationale**: Plan 010 mandates IndexTTS-2; the runtime now uses its official inference API.
- **Risk**: Dependency or checkpoint download failure blocks synthesis.
- **Validation method**: Run `tests/e2e/tts_pipeline_smoke.py` with full IndexTTS-2 download and confirm audio output.
- **Escalation evidence**: IndexTTS-2 fails to initialize after download → **Major** (escalate to planner).

### Assumption 2: Presigned URLs satisfy downstream retrieval needs
- **Description**: `audio_uri` now uses presigned MinIO URLs so playback clients can retrieve without public bucket policies.
- **Rationale**: Compose stack lacks anonymous bucket policy; presigned URLs enable immediate consumption.
- **Risk**: Presigned expiry or URL rewriting errors could break playback.
- **Validation method**: Keep smoke tests for URI mode and verify retrieval against the public endpoint.
- **Escalation evidence**: 403/404 responses during normal operation → **Moderate** (fix + QA).
