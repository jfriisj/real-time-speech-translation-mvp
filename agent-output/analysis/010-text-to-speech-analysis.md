# Analysis 010: Text-to-Speech Unknowns

**Plan Reference (if any)**: agent-output/planning/010-text-to-speech-plan.md
**Status**: Draft

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-26 | Planner | Identify open technical unknowns for Plan 010 completion | Captured the current implementation state and surfaced the remaining verification/refactor work needed to close the plan. |

## Objective
Identify the specific technical unknowns that must be resolved before Plan 010 can be marked complete.

## Context
- Relevant modules/files: [services/tts/src/tts_service/main.py](services/tts/src/tts_service/main.py), [services/tts/src/tts_service/synthesizer_kokoro.py](services/tts/src/tts_service/synthesizer_kokoro.py), [services/tts/src/tts_service/storage.py](services/tts/src/tts_service/storage.py), [shared/speech-lib/src/speech_lib/__init__.py](shared/speech-lib/src/speech_lib/__init__.py), [tests/e2e/tts_pipeline_smoke.py](tests/e2e/tts_pipeline_smoke.py).
- Known constraints: dual-mode transport with an inline payload cap near 1.5 MB, a 24 h MinIO lifecycle rule for the `tts-audio` bucket, and the expectation that `speech-lib` can expose reusable adapters following the latest plan revision.

## Methodology
- Reviewed [agent-output/planning/010-text-to-speech-plan.md](agent-output/planning/010-text-to-speech-plan.md) to understand the remaining plan steps (real inference validation, integration tests, and cleanup/refactor).
- Inspected the current TTS service implementation (`main.py`, `synthesizer_kokoro.py`, `storage.py`) plus the shared library entry point to determine which requirements are already satisfied versus still pending.
- Studied the integration smoke script (`tests/e2e/tts_pipeline_smoke.py`) to assess what payload scenarios are currently exercised.

## Findings

### Facts
- [services/tts/src/tts_service/main.py](services/tts/src/tts_service/main.py) already implements dual-mode payload selection, imports a service-local `ObjectStorage`, and handles inline vs. MinIO uploads before publishing the `AudioSynthesisEvent` with `model_name`.
- [services/tts/src/tts_service/synthesizer_kokoro.py](services/tts/src/tts_service/synthesizer_kokoro.py) downloads the Kokoro assets, initializes `misaki` and `onnxruntime`, and runs inference, but the voice dictionary currently only retains the reshaped first vector (labelled `af_bella`), so any `speaker_id` beyond that key falls back to the same style vector.
- [tests/e2e/tts_pipeline_smoke.py](tests/e2e/tts_pipeline_smoke.py) validates that exactly one of `audio_bytes` or `audio_uri` is populated and can fetch the URI when present, but it does not force the URI path via the inline cap, nor does it intentionally trigger MinIO/consumer 404 or timeout scenarios.
- [shared/speech-lib/src/speech_lib/__init__.py](shared/speech-lib/src/speech_lib/__init__.py) exposes Kafka helpers and schema utilities but has no storage adapters exported yet, so there is no shared place to move `ObjectStorage` into without adding new APIs and dependencies.

### Hypotheses
- The plan’s voice-mapping requirement cannot be satisfied without a deterministic mapping from `speaker_id` to the real vectors inside `voices.bin`; the current loader discards the majority of those vectors, so we need to discover which IDs exist and how to surface them safely.
- The `TTS_SPEED` tunable is still missing—the Kokoro backend always feeds a constant `speed` tensor of `1.0` into ONNX—so the “Audio Control” acceptance criterion is not yet met until this env var is wired through the model inputs.
- The integration validation step (Plan Step 4) is incomplete: there is no automated run that pushes >1.5 MB text, confirms MinIO upload/fetch, and logs what happens when downstream consumers hit a 404/timeout, so the failure-resilience and observability contracts remain unproven.

## Recommendations
- Add or extend the integration smoke test to deliberately exceed the inline cap (`EXPECT_PAYLOAD_MODE=URI`), fetch the produced `audio_uri` from MinIO, and exercise the 404/timeout branches (e.g., by rewriting the URI) to prove the production/logging behavior required by the plan.
- Explore Kokoro’s style-vector assets to document available voice IDs, implement a lookup that maps `speaker_id` → vector (with a default fallback), and propagate `TTS_SPEED` (default `1.0`) from the env into the `speed` tensor so the inference path honors the “Audio Control” requirement.
- Move `ObjectStorage` into `speech-lib` (e.g., `shared/speech-lib/src/speech_lib/storage.py`), update that package’s exports and dependencies (adding `boto3`), and update the TTS service imports to use the shared adapter while deleting the deprecated `services/tts/src/tts_service/synthesizer.py`/`services/tts/tests/test_legacy_synthesizer.py` per plan Step 5.

## Open Questions
## Research Gaps & Unverified Assumptions
- **Speaker/style mapping** (Plan Step 3 assumes Kokoro’s `voices.bin` exposes easily consumable `speaker_id` keys beyond the default `af_bella`). The existing loader retains a single vector, so there is no fact-backed inventory of acceptable IDs nor an automated map to style vectors. Without this inventory, the “speaker context propagation” contract cannot be enforced or validated.
- **Speed control observability** (Plan Step 7 lists a `TTS_SPEED` check, but the code still feeds a constant `1.0` into the Kokoro ONNX input tensor). The plan assumes the knob can produce a ≥10% duration delta, yet neither implementation nor tests currently confirm the parameter has any effect. This is a research gap before the “Audio Control” acceptance criterion can be certified.
- **Dual-mode failure resilience** (Plan Step 4 promises graceful handling of MinIO upload/fetch errors and 404/timeout logging). The current smoke script (`tests/e2e/tts_pipeline_smoke.py`) only verifies the happy path and does not intentionally force the inline cap/URI path or downstream 404. Thus, there is no empirical evidence that the logging/fallback behavior works as specified.
- **GPU delivery profile** (Roadmap + Findings 013 require runnable images for both CPU and GPU, yet Plan 010 defers GPU support to configuration. There is no documented verification of `onnxruntime-gpu` compatibility or explicit packaging/profile strategy; the assumption that the service can switch providers via configuration remains unvalidated.)
- **MinIO retention evidence** (Plan Step 2 mandates a 24 h lifecycle rule, but no existing artifact verifies the rule’s presence or what observer should be consulted to confirm it. The plan assumes MinIO bucket policies are in place, yet there is no record or test to prove it.)

1) What are the authoritative Kokoro voice/style identifiers beyond `af_bella`, and how should `speaker_id` map to them? **Success criteria**: The service resolves at least one additional voice/style vector, the mapping is driven by data in the asset (or a config), and tests cover the fallback case.
2) How should we prove the dual-mode URI path and the downstream 404/timeout handling so that Plan Step 4’s acceptance criteria are satisfied? **Success criteria**: A scripted run can set `EXPECT_PAYLOAD_MODE=URI`, fetch the MinIO object from the public endpoint, and trigger the logging path for a missing/expired key.
3) What does the package-level refactor to `speech-lib` require (exports, dependencies, import paths) so that `ObjectStorage` can be shared and the legacy synthesizer/test removed? **Success criteria**: `speech-lib` exports `ObjectStorage`, lists `boto3`, and the TTS service imports from `speech_lib.storage` without breaking other references.
4) What evidence is acceptable for the 24 h MinIO retention requirement? **Success criteria**: A verified lifecycle rule (e.g., `expire-tts-audio`) with 24-hour expiration is recorded in QA artifacts or infrastructure docs.
## Handoff
This analysis documents the remaining verification/refactor work needed to finalize Plan 010; the open questions must be resolved before the feature can be promoted to a passing QA status.

## Handoff to Implementer
**From**: Analyst
**Artifact**: agent-output/analysis/010-text-to-speech-analysis.md
**Status**: Complete
**Key Context**:
- Dual-mode delivery is wired into `main.process_event`, but the large-payload/URI path still lacks integration coverage and failure logging proof.
- The Kokoro backend downloads assets and runs inference, yet does not yet map `speaker_id`s beyond `af_bella` or honor a configurable `TTS_SPEED`.
- Storage logic is still service-local; plan Step 5 explicitly expects it to live in `speech-lib` and to remove the deprecated `synthesizer.py`/`test_legacy_synthesizer.py`.
**Recommended Action**: Answer the open questions above by adding the required tests, completing the Kokoro voice/speed wiring, moving the storage adapter into `speech-lib`, and documenting the 24 h MinIO retention so the plan can be closed.
