# Analysis 010: Text-to-Speech (Kokoro pivot)

**Plan Reference (if any)**: [agent-output/planning/010-text-to-speech-plan.md](agent-output/planning/010-text-to-speech-plan.md)

**Status**: Draft

## Value Statement and Business Objective

Deliver the Epic 1.7 `tts-service` so translated text is spoken naturally with measurable RTF/latency evidence, dual-mode transport, and speaker context propagation. The Kokoro ONNX pivot must prove the new synthesizer fits into the existing Kafka → MinIO → consumer pipeline without regressing the contracts that downstream services rely on.

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-25 | Analyst | Investigate Kokoro pivot unknowns | Surveyed the IndexTTS-2 implementation, uncovered voice-mapping, schema, and contract gaps that prevent the Kokoro refactor from landing. |
| 2026-01-26 | Analyst | Capture integration/test blockers | Verified QA still marks the feature as Failed because Kafka/Schema/MinIO integration tests have not run, leaving `audio_uri`, retention, and Kokoro inference behavior unvalidated despite analyzer/coverage successes. |

## Objective

Record the remaining technical unknowns after the Kokoro scaffold and analyzer/coverage gates pass so planners and implementers can close the integration, asset, and observability blocks before UAT handoff.

## Context

- Plan 010 mandates dual-mode transport, optional speaker metadata, MinIO lifecycle (24h), `model_name` observability, and a pluggable synthesizer factory anchored on Kokoro-82M.
- QA Report [agent-output/qa/010-text-to-speech-qa.md](agent-output/qa/010-text-to-speech-qa.md) still shows **QA Failed** because Kafka + Schema Registry + MinIO integration tests were never run; unit tests + coverage (77.59% on `main.py`) and Ruff/Vulture reports are green.
- Blocker: the integration scenario (large payload → MinIO upload → `audio_uri` retrieval) is untested, and the Kokoro backend is currently scaffolded with mocked inference, so the real asset/voice/style requirements remain unknown.
- Files/symbols involved: `services/tts/src/tts_service/main.py::process_event`, `build_output_event`, `ObjectStorage.upload_bytes`, `synthesizer_kokoro.py::KokoroSynthesizer.synthesize`, plus Docker Compose / QA artifacts that tie integration tests to Kafka/Schema/MinIO.

## Root Cause

- Integration-level automation (Kafka + Schema Registry + MinIO + TTS) has not been executed in this cycle, so `audio_uri` delivery, MinIO retention, and consumer failure semantics remain unvalidated.
- `KokoroSynthesizer` currently downloads assets and initializes misaki/onnxruntime, but the inference step is mocked, the voice file loader is a placeholder, and the real style-vector mapping / `speaker_reference_bytes` semantics are unknown.
- Without explicit instrumentation or tests covering the `model_name` metadata and `audio_uri` fallback, we cannot prove downstream consumers or QA metrics observe the new fields as promised.

## Methodology

- Reviewed `services/tts/src/tts_service/main.py` (`process_event`, `build_output_event`) and the Kokoro backend (`synthesizer_kokoro.py`) to understand the new `model_name` propagation, dual-mode logic, and placeholder inference behavior.
- Consulted the latest QA report and metrics JSON to capture the current gate status (unit tests passing, integration tests not run, QA still failed).
- Cross-referenced the plan’s contracts (dual-mode transport, MinIO lifecycle, speaker context) against what the new code paths currently exercise.

## Findings

### Facts
- QA still reports **QA Failed** because integration tests for Kafka + Schema Registry + MinIO have not been run (see [agent-output/qa/010-text-to-speech-qa.md](agent-output/qa/010-text-to-speech-qa.md)); the unit-level analyzer/coverage duties now succeed, but the large-payload path remains unverified.
- `process_event` now passes `model_name` from settings into `build_output_event` and decides between inline bytes and `ObjectStorage.upload_bytes` uploads, but no integration validation exercises the `audio_uri` download, MinIO retention, or consumer QoS for failure cases.
- `KokoroSynthesizer` downloads Kokoro assets and configures an ONNX session, but the inference code is stubbed (random noise) and the voice loader/`speaker_reference_bytes` pathway is unimplemented, so the actual asset/voice/voice-style requirements are still unknown.

### Hypotheses
- Without bringing up Kafka + Schema Registry + MinIO, we cannot confirm that consumers successfully fetch `audio_uri`, that 404/timeout handling honors the plan’s failure policy, or that the 24h lifecycle rule actually expires objects after upload.
- The real Kokoro voices asset may be in a non-NumPy format or require additional dependencies (e.g., PyTorch) so the current `_load_voices` stub will fail once real assets are used; downstream voice/style mapping and `speaker_id` fallback behavior must be explicitly verified.
- Downstream consumers may not yet understand the new `model_name` field, so we should confirm their schemas tolerate it and that logging/metrics actually surface it for RTF/latency tracing.

## Recommendations
- Run the Docker Compose integration stack (Kafka + Schema Registry + MinIO + TTS) to produce a large payload, upload it to MinIO, and fetch the resulting `audio_uri`. Capture logs/metrics for `correlation_id`, `payload_mode`, and any 404/timeout events so we can validate the failure semantics and retention lifecycle.
- Finish the Kokoro synthesizer spike: parse the actual `voices.bin`/style assets, confirm supported `speaker_id` values, wire in real inference inputs (token IDs, style vectors, optional `speaker_reference_bytes`), and ensure warmup/asset downloads succeed in CI.
- Add integration-level assertions or instrumentation that record when `model_name` is emitted and when `audio_uri` uploads happen so QA can prove the observability contract holds for both inline and URI payloads.

## Open Questions
- What are the authoritative Kokoro voice/style IDs, and how should unknown `speaker_id`s or speaker references map to them (e.g., fallback voice, silence, or default style)?
- When a downstream consumer gets a MinIO `audio_uri` that is expired/missing, what is the expected behavior: retry window, skip playback, or fallback to inline audio if still cached?
- Which artifact (repo-level manifest, `services/tts/pyproject.toml`, or a new VERSION file) will anchor the `v0.5.0` release so the plan and QA teams can verify compliance with Step 5 of the plan?

## Handoff
QA is blocked solely by the missing integration tests and the unresolved Kokoro inference/voice mapping behavior. Once the integration stack proves `audio_uri` retrieval, MinIO retention, and failure handling, the plan can be considered for UAT prep.

## Handoff to Implementer
**From**: Analyst
**Artifact**: agent-output/analysis/010-text-to-speech-analysis.md
**Status**: Draft
**Key Context**:
- The Kokoro pivot has been wired into `main.process_event` and the synthesizer factory, but the large-payload path, MinIO upload/download cycle, and `model_name` observability still lack integration coverage.
- Kokoro assets are downloaded, but the inference path is currently mocked and the voice loader lacks knowledge of the real format, so the `speaker_id` → style vector contract is undefined.
**Recommended Action**: Spike the Kokoro backend to confirm real asset/loading behavior and bring up the Kafka/Schema/MinIO integration stack to exercise `audio_uri` uploads/downloads, retention, and downstream logging/metrics before handing QA a passing report.
