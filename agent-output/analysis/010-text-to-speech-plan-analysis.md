# Analysis 010: Text-to-Speech (TTS) Plan Unknowns

## Value Statement and Business Objective
As a User, I want to hear the translated text spoken naturally so that I can consume the translation hands-free. The service must deliver Kokoro-82M-powered audio (inline or via Claim Check) with observability to prove synthesis latency/RTF and retention behavior.

## Changelog
| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | Planner → Analyst | Plan validation | Surface the remaining technical unknowns blocking implementation of Plan 010 (Rev 28) and capture success criteria for each. |

## Root Cause
Key implementation contracts lack sufficient detail: the tokenizer expectations, fallback behavior when object storage is absent, inline payload sizing guidance, GPU runtime prerequisites, and RTF evidence collection are not yet documented, making it impossible to finalize the service without assumptions.

## Context
- Relevant modules/files: `services/tts` (Dockerfile, synthesizer, processing), `shared/schemas/avro/AudioSynthesisEvent.avsc`, `agent-output/planning/010-text-to-speech-plan.md` (Rev 28).
- Known constraints: Claim Check is mandated for payloads > 1.25 MiB, storage is optional (inline-only mode must still work), and `.env` toggles (e.g., `DISABLE_STORAGE`) are not currently described in the plan.

## Questions to Answer
1. **Tokenizer alignment** – What exact tokenizer (audio preprocessing sequence) does Kokoro-82M expect and how do we initialize it reliably in the Docker image? _Success_: publish the tokenizer name/version, include initialization steps (phonemizer with `espeak-ng`), and confirm packaging/licensing in `services/tts`.
2. **Storage fallback behavior** – When MinIO/S3 is unavailable or `DISABLE_STORAGE=true`, what is the defined behavior when a payload exceeds `MAX_INLINE_BYTES`? _Success_: document the flag, describe the warning log, and ensure the plan states “log and drop” instead of crashing or sending incomplete data.
3. **Inline payload duration guidance** – Given 24 kHz/16-bit mono WAV, what is the maximum synth duration that fits within 1.25 MiB (and its equivalent text length)? _Success_: provide a calculator or table (bytes ↔ seconds) plus a user-facing warning threshold for `text` length.
4. **GPU runtime prerequisites** – If the plan ever switches to `onnxruntime-gpu`, which CUDA/cuDNN versions and drivers must be present, and how does the container detect GPU support? _Success_: list supported driver versions, required packages, and a detection strategy (e.g., `onnxruntime-gpu` provider availability) so rollout decisions are informed.
5. **Latency/RTF evidence collection** – What exact commands or synthetic load should QA/UAT run to record `synthesis_latency_ms` and `rtf`, and which sample phrases prove intelligibility? _Success_: define the script/test harness, list sentences, and specify where to persist the metrics/log excerpt for evidence.

## Methodology
- Reviewed Plan 010 (Rev 28) for defined contracts around schema, observability, data retention, and input behavior.
- Examined `services/tts/Dockerfile` to confirm runtime dependencies (`espeak-ng`, `libsndfile1`) and noted lack of documentation for storage toggles.
- Cross-referenced prior implementation notes (UAT/QA feedback) indicating missing latency/RTF proof and storage retention artifacts.

## Findings
### Facts
1. The plan now mandates phonemizer-backed tokenization with `espeak-ng` in the runtime image but does not specify how to configure it nor how to verify completeness after deployment.
2. The schema contract explicitly states `audio_bytes` XOR `audio_uri`, and Claim Check must be packaged even though storage can be disabled; without a documented fallback, teams may implement inconsistent behavior when buckets are absent.
3. Observability requirements include logging `synthesis_latency_ms` and `rtf`, however no test or script exists in the plan to produce the metrics/charts required for QA/UAT evidence.

### Hypotheses
1. Kokoro’s tokenizer likely relies on specific lexicon files or stress markers; without shipping the same `tokenizer.json` bundle and a reproducible phonemization pipeline, inference may produce garbled audio.
2. A bytes→seconds helper (24 kHz × 2 bytes per sample) will show that 1.25 MiB covers ~26 seconds of mono audio; linking this to the 500-character hard cap may require validation against actual synthesized durations.
3. GPU readiness will hinge on driver availability, so safe rollout requires reporting `onnxruntime.get_available_providers()` at startup and installing `cuda-toolkit` versions that match cluster drivers.

## Recommendations
1. Document the tokenizer/phonemizer setup in the plan (name/version, initialization, license) and ensure the Dockerfile and runtime mirror this configuration.
2. Add an explicit `DISABLE_STORAGE` flag to the plan, describe log messages when Claim Check is unavailable, and confirm that the service logs the object key (never full presigned URI) before dropping events.
3. Include an inline cap reference (e.g., 1.25 MiB ≈ 26 s mono audio at 24 kHz) and guidance linking it to text length validation so downstream teams can estimate warnings.
4. Capture GPU dependency info in a supplemental doc (driver versions, required packages, detection code) so future rollouts to `onnxruntime-gpu` know what to install and how to gate execution.
5. Define a QA script harness (curl/pytest) that emits test phrases, captures logs for `synthesis_latency_ms`/`rtf`, and stores them in `report-output/` for UAT evidence.

## Open Questions
- Should we create an integration smoke test that automatically uploads audio to MinIO and verifies retention policies, or is manual verification acceptable for v0.5.0?
- Is a DLQ required later when text exceeds 500 characters, or should Log-and-Drop remain the permanent behavior for the MVP?
- Where should stored latency/RTF evidence live so QA/UAT reviewers can easily find it (artifact path, naming convention)?

## Handoff
**From**: Analyst
**Artifact**: agent-output/analysis/010-text-to-speech-plan-analysis.md
**Status**: Complete
**Key Context**:
- Plan 010 now names `phonemizer` but lacks tokenizer setup steps, storage fallback docs, inline cap guidance, GPU prerequisites, and QA measurement scripts.
**Recommended Action**: Planner/Implementer should augment the plan with the above details, reference Docker/runtime configuration, and define the QA evidence workflow before handing off to implementation.# Analysis 010: Text-to-Speech (TTS) Plan Unknowns

**Date**: 2026-01-27
**Related Plan**: agent-output/planning/010-text-to-speech-plan.md
**Purpose**: Surface technical unknowns that must be resolved before executing the plan.

## Questions to Answer
1. **Model tokenization requirements**
   - Question: Does the Kokoro ONNX bundle expect phonemized input or raw text, and what tokenizer/token set must we ship to the service? (Success = document the tokenizer, lexicon, and how it is initialized in the container.)
2. **Object storage availability & fallback**
   - Question: In environments without MinIO/S3, what is the documented behavior when a large payload exceeds `MAX_INLINE_BYTES`? (Success = ship documented fallback behavior and configuration flag that disables URI generation.)
3. **Quantifying WAV duration per byte**
   - Question: What duration of synthesized WAV (sample rate 24k, 16-bit) fits within the 1.25 MiB inline budget, so we can sensibly warn users before dropping payloads? (Success = provide bytes-to-duration reference table/formula.)
4. **GPU runtime readiness**
   - Question: What runtime dependencies (CUDA/cuDNN) are required when switching to `onnxruntime-gpu`, and how will the container detect support? (Success = list required packages, driver versions, and detection strategy.)
5. **Latency/RTF measurement baseline**
   - Question: What script or load pattern should we use to capture service-level latency/RTF for the curated phrase set (serving as QA evidence)? (Success = provide command plus metrics to record.)

## Methodology
- Interviewed Architect notes (Findings 011/013/015).
- Reviewed master architecture to capture message-size invariants and claim-check requirements.
- Studied Plan 010 to identify missing data (tokenization, fallback behavior, automation hooks).

## Findings
1. **Tokenization**: Kokoro requires phoneme sequences; we need to bundle the same tokenizers as the model release and confirm license. Without confirmation, implementing `KokoroSynthesizer` risks mismatch.
2. **Storage Fallback**: Plan now states storage is optional, but no configuration entry exists; implementation must add env flag and doc for what happens when the bucket is missing.
3. **Duration Guidance**: Inline cap is 1.25 MiB but duration depends on sample rate; we need a helper to convert to seconds to provide warnings.
4. **GPU Dependencies**: No hardware/driver guidance currently; we need to document which CUDA/cuDNN versions are compatible and how the plan ensures `onnxruntime-gpu` only runs where `CUDAExecutionProvider` is available.
5. **Performance Evidence**: QA requires latency and RTF numbers; define script/resolution.

## Recommendations
1. Capture tokenizer spec and embed within `services/tts` (vendor license check). Create issue for confirming input format.
2. Add plan section explaining `DISABLE_STORAGE=true` fallback plus log behavior.
3. Provide helper function or doc for bytes→seconds (24kHz, 16-bit stereo/mono) to enforce inline caps.
4. Add future plan (011) details as references for GPU readiness; include driver/package table.
5. Define test script (curl + faker event) to record latency/RTF.

## Next Steps
- Confirm Kokoro tokenizer requirements and embed steps in plan.
- Document storage fallback behavior (env flag, log/drop).
- Provide duration reference for inline payload.
- Reference GPU runtime requirements and detection strategy.
- Draft latency/RTF measurement script for QA evidence.