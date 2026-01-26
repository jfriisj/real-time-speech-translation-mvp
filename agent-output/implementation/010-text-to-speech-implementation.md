# Implementation 010: Text-to-Speech (TTS) Service (Kokoro ONNX)

## Plan Reference
agent-output/planning/010-text-to-speech-plan.md

## Date
2026-01-26

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-25 | Implementation report refresh | Updated report to reflect Kokoro ONNX pivot and current implementation state. |
| 2026-01-26 | Implementation report update | Refreshed report for Plan 010 Rev 10 readiness; no code changes in this session. |
| 2026-01-26 | Integration smoke rerun | Fixed Misaki G2P initialization and re-ran TTS pipeline smoke test successfully. |
| 2026-01-26 | Integration validation | Verified MinIO lifecycle rule configuration and URI failure semantics (404 + connection refusal). |

## Implementation Summary (what + how delivers value)
- Replaced IndexTTS-specific runtime wiring with a pluggable `Synthesizer` interface and factory selected via `TTS_MODEL_NAME` for model swaps.
- Implemented a Kokoro ONNX backend scaffold that downloads the ONNX graph and voices assets, initializes ONNX Runtime, and produces WAV bytes for `AudioSynthesisEvent`.
- Updated TTS output contract to include optional `model_name` in [shared/schemas/avro/AudioSynthesisEvent.avsc](shared/schemas/avro/AudioSynthesisEvent.avsc) and [shared/speech-lib/src/speech_lib/events.py](shared/speech-lib/src/speech_lib/events.py).
- Updated Compose and container dependencies to remove IndexTTS/Torch stack and add `onnxruntime`, `misaki`, and `soundfile` for Kokoro ONNX.
- Updated Kokoro synthesizer initialization to handle Misaki G2P signature differences so the container boots successfully.

## Milestones Completed
- [x] Shared schema updates (`AudioSynthesisEvent` + `model_name` optional field).
- [x] TTS service wired to pluggable synthesizer factory.
- [x] Kokoro ONNX synthesizer scaffold and model asset download.
- [x] MinIO lifecycle rule present for 24h retention.
- [x] MinIO lifecycle rule present for 24h retention (rule verified in MinIO).
- [x] Compose config updated for Kokoro ONNX cache path.
- [ ] Version management artifacts (CHANGELOG, release notes) updated for v0.5.0.

## Files Modified
| Path | Changes | Lines |
|------|---------|-------|
| docker-compose.yml | Updated TTS model name + cache path for Kokoro ONNX | n/a (diff unavailable in report session) |
| services/tts/Dockerfile | Removed IndexTTS deps; install ONNX stack; add model cache dir | n/a |
| services/tts/pyproject.toml | Remove IndexTTS/torch deps; add onnxruntime + misaki | n/a |
| services/tts/src/tts_service/config.py | Default `TTS_MODEL_NAME` set to Kokoro | n/a |
| services/tts/src/tts_service/main.py | Factory-based synthesizer, emit `model_name` | n/a |
| services/tts/tests/conftest.py | Mock ONNX runtime + Kafka for tests | n/a |
| shared/schemas/avro/AudioSynthesisEvent.avsc | Add `model_name` optional field | n/a |
| shared/speech-lib/src/speech_lib/events.py | Add `model_name` to `AudioSynthesisPayload` | n/a |
| agent-output/roadmap/product-roadmap.md | Epic 1.7 status + AC updates | n/a |
| agent-output/planning/010-text-to-speech-plan.md | Rev 10 adjustments + checklist updates | n/a |
| agent-output/critiques/010-text-to-speech-plan-critique.md | Updated critique for Plan Rev 10 | n/a |
| services/tts/src/tts_service/synthesizer_kokoro.py | Add compatible G2P initialization helper | n/a |

## Files Created
| Path | Purpose |
|------|---------|
| services/tts/src/tts_service/synthesizer_factory.py | Pluggable synthesizer factory for future model swaps. |
| services/tts/src/tts_service/synthesizer_interface.py | Abstract `Synthesizer` contract for backend implementations. |
| services/tts/src/tts_service/synthesizer_kokoro.py | Kokoro ONNX backend scaffold (download + inference placeholder). |

## Code Quality Validation
- [x] Linting: Ruff scan clean for `services/tts/src/tts_service/synthesizer_kokoro.py`.
- [ ] Formatting: not run in this session.
- [x] Dead-code scan: Vulture scan clean for `services/tts/src/tts_service/synthesizer_kokoro.py`.
- [x] Tests: TTS pipeline smoke test executed.
- [x] Compatibility: TTS smoke test passes (Kafka + Schema Registry + MinIO + TTS).
- [x] Integration: MinIO lifecycle policy inspected; URI 404 + connection refusal observed.
- [ ] Pre-handoff scan: not run in this session.

## Value Statement Validation
**Original**: “As a User, I want to hear the translated text spoken naturally, so that I can consume the translation hands-free.”

**Implementation delivers**: The TTS service now produces `AudioSynthesisEvent` with the correct envelope and supports inline-or-URI payload transport plus speaker context propagation. The Kokoro synthesizer is still a scaffold (voice loading and phoneme/token mapping are not fully implemented), so “natural” audio is not yet proven.

## Test Coverage
- **Unit**: Not executed in this session.
- **Integration**: TTS pipeline smoke test executed successfully; MinIO lifecycle rule inspection; URI failure checks (404 + connection refusal).

## Test Execution Results
| Command | Results | Issues | Coverage |
|---------|---------|--------|----------|
| `/home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python tests/e2e/tts_pipeline_smoke.py` | PASS | None | n/a |
| `docker run --rm --network real-time-speech-translation-mvp_speech_net --entrypoint /bin/sh minio/mc:latest -c "mc alias set local http://minio:9000 minioadmin minioadmin >/dev/null && mc ilm ls local/tts-audio"` | PASS | Lifecycle rule present (`expire-tts-audio`, 1 day) | n/a |
| `/home/jonfriis/github/real-time-speech-translation-mvp/.venv/bin/python -c "...missing_object + connection_refused checks..."` | PASS | Missing object returned 403; connection refused produced URLError | n/a |
| `docker exec speech-tts-service python -c "...presigned missing object check..."` | PASS | Presigned missing object returned 404 | n/a |

## Outstanding Items
- Fix `process_event` in [services/tts/src/tts_service/main.py](services/tts/src/tts_service/main.py) to remove the invalid `producer.publish_event(...)` call with mismatched signature.
- Implement real Kokoro preprocessing (phoneme/token mapping, voice vector loading) in [services/tts/src/tts_service/synthesizer_kokoro.py](services/tts/src/tts_service/synthesizer_kokoro.py); current output is mocked noise.
- Clarify v0.5.0 CPU/GPU deployment profile and provider selection per Findings 013 and roadmap AC.
- Add explicit duration/speed control behavior (epic AC) or document deferral.
- Run unit tests with coverage before QA handoff.
- Update version artifacts (root CHANGELOG / release notes) if required by the plan.
- Resolve plan critique criticals: treat Findings 013 as primary architecture reference and add explicit “no raw audio bytes in logs” redaction rule.
- Determine line-level change stats for the report (git diff not available in this session).
- Observe MinIO lifecycle deletion after 24h (rule verified, but expiration behavior not yet observed).

## Next Steps
- QA: Run code-quality scans and integration tests for Kafka + MinIO + TTS flow.
- UAT: Validate Kokoro audio output quality and RTF/latency targets on reference hardware.

## Assumption Documentation
### Assumption 1: Kokoro voices.bin format can be loaded without Torch
- **Description**: The Kokoro voices file is loadable via a lightweight approach (numpy/structured binary) without introducing Torch dependencies.
- **Rationale**: The container is now CPU-lightweight and avoids Torch; voice-loading should not require large ML runtimes.
- **Risk**: If voices.bin requires Torch or a proprietary loader, synthesis will fail or produce wrong voice styles.
- **Validation method**: Implement a real loader and verify voice vectors against Kokoro reference samples.
- **Escalation evidence**: voices.bin cannot be parsed without Torch → **Moderate** (revisit dependencies or model variant).

### Assumption 2: Phoneme/token mapping can be derived from Kokoro config
- **Description**: The phoneme/token mapping required by Kokoro can be derived from model assets or config and implemented deterministically.
- **Rationale**: Required to produce intelligible audio and satisfy “natural speech” outcome.
- **Risk**: Incorrect mapping leads to unintelligible output or runtime errors.
- **Validation method**: Implement mapping and validate output on a small phrase set; compare against Kokoro reference.
- **Escalation evidence**: Output remains unintelligible after mapping fixes → **Major** (escalate to planner for model swap or scope adjustment).

### Assumption 3: QA/UAT prompt criteria were not available in this session
- **Description**: QA/UAT evaluation prompts could not be loaded from the local config path.
- **Rationale**: File access was denied outside the workspace.
- **Risk**: Implementation report may miss required QA/UAT expectations.
- **Validation method**: Re-open or provide the prompt files in workspace for inclusion.
- **Escalation evidence**: QA/UAT rejects due to missing criteria → **Minor** (update report + rerun QA).
