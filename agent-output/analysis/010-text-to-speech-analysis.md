# Analysis 010: Text-to-Speech (Kokoro pivot)

**Plan Reference (if any)**: [agent-output/planning/010-text-to-speech-plan.md](agent-output/planning/010-text-to-speech-plan.md)
**Status**: Draft

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-25 | Analyst | Investigate Kokoro pivot unknowns | Surveyed existing TTS service wiring and surfaced the knowledge gaps blocking the Kokoro-82M refactor. |

## Objective
Document the technical unknowns that must be resolved before replacing the IndexTTS-2 pipeline with `hexgrad/Kokoro-82M` so that the plan can be executed with confidence that latency, size, and voice-mapping expectations are realistic.

## Context
- Relevant modules: `services/tts/src/tts_service/synthesizer.py` (model loader), `main.py` (settings + Kafka loop), `services/tts/pyproject.toml` (dependencies), `docker-compose.yml` (runtime env/config).
- Current constraint: plan metrics target $RTF < 0.5$ and Latency P50 < 1,000 ms, while code today gears toward an 800+ MB IndexTTS-2 model that trips over timeouts.
- Pending pivot: replace `indextts` usage with a lightweight Kokoro implementation while keeping dual-mode payload handling/MinIO logic intact.

## Methodology
- Reviewed `synthesizer.py` and `main.py` to understand how the model is loaded, consumed, and connected to Kafka events.
- Inspected `pyproject.toml` and `docker-compose.yml` to enumerate current dependencies and live configuration flags (e.g., `TTS_MODEL_NAME`, `HF_TOKEN`).
- Cross-referenced plan requirements (speaker context pass-through, observability contract, dual-mode transport) against the implementation that currently enforces `IndexTTS` exclusively.

## Findings

### Facts
- The synthesizer layer is hardwired to `IndexTeam/IndexTTS-2`, will raise `ValueError` if `TTS_MODEL_NAME` differs, and depends on the `indextts` package plus waveform prompt handling via `soundfile`.
- `main.py` instantiates `IndexTTS2Synthesizer`, warms it up once, and never exposes a pluggable interface; the service also enforces `correlation_id`-keyed Kafka output and dual-mode (inline vs URI) publishing with MinIO fallback.
- The current dependency set (see `pyproject.toml`) lacks the Kokoro-specific packages (`kokoro`, `phonemizer`, etc.) that the revised plan explicitly mentions.

### Hypotheses
- The Kokoro pipeline will require a different call pattern (text → phonemes → waveform) and needs explicit voice/style names; we must confirm what dependency (`kokoro` vs huggingface `transformers` pipelines) and configuration knobs are required to replicate the existing `synthesize(text, bytes)` signature.
- Speaker context mapping ($speaker_id$ → Kokoro style) is undefined today; the plan implies mapping to voices such as `af_bella`, but we do not yet know the canonical list of supported styles or how to supply them to the inferred API.
- Kokoro-82M still needs weight download; the service currently relies on `HF_TOKEN`, but we need to confirm that the new repo `hexgrad/Kokoro-82M` honors the same token semantics and whether caching/warmup requirements differ (e.g., local checkpoints, CPU-only operations).

## Recommendations
- Before locking the Kokoro plan, prototype the `kokoro` inference path (or read its documentation) to understand: initialization time, CPU/memory footprint, how to select style/voice, and whether it natively produces PCM suitable for the dual-mode pipeline.
- Capture the canonical voice/style IDs in a shared config map so the plan can specify what `speaker_id`s map to (e.g., `af_bella` default) and include fallback behavior when the mapping is missing.
- Expand the plan with a short spike that measures Kokoro-82M inference latency on the target hardware (warming up once and timing a representative phrase) to validate the $RTF$ and Latency targets before committing to the new synthesizer.

## Open Questions
- Which Python package actually hosts the Kokoro inference API (plain `kokoro`, `hexgrad`, or a custom wrapper) and what arguments does it expect for selecting styles? We need a reference usage snippet.
- Does Kokoro-82M support the same speaker prompt strategy (audio-in, zero-shot) that IndexTTS-2 offered, or must we rely solely on `speaker_id` style keys for now?
- Are there additional license, download, or HF token requirements for `hexgrad/Kokoro-82M` beyond the existing `HF_TOKEN` flow? If the model requires gating, plan needs to capture that dependency.
- Will the current `minio` dual-mode logic require adjustments if Kokoro produces longer audio (e.g., larger file sizes) even for short sentences, affecting when we switch to URI mode?

## Handoff
The synthesizer and main loop currently enforce IndexTTS-2. Swapping to Kokoro-82M requires (1) replacing `indextts` dependency with the correct Kokoro package, (2) understanding voice/style mapping for `speaker_id`, and (3) validating the new model meets the RTF and latency goals on CPU.

## Handoff to Implementer
**From**: Analyst
**Artifact**: agent-output/analysis/010-text-to-speech-analysis.md
**Status**: Draft
**Key Context**:
- The service is tightly bound to `IndexTeam/IndexTTS-2` and `indextts`; the plan’s Kokoro pivot demands a pluggable synthesizer that can accept `speaker_id` style hints while keeping the existing dual-mode logic.
- Dependencies/metrics in `pyproject.toml` and `docker-compose.yml` must be realigned (new packages, `TTS_MODEL_NAME`, `HF_TOKEN` usage).
**Recommended Action**: Research the Kokoro inference API and voice/style signals, prototype a `KokoroSynthesizer`, and document any new runtime requirements (license, warmup, voice mapping) so the plan can be finalized.# Analysis 010: Text-to-Speech (Kokoro pivot)

**Plan Reference (if any)**: [agent-output/planning/010-text-to-speech-plan.md](agent-output/planning/010-text-to-speech-plan.md)
**Status**: Draft

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-25 | Analyst | Investigate Kokoro pivot unknowns | Surveyed existing TTS service wiring and surfaced the knowledge gaps blocking the Kokoro-82M refactor. |

## Objective
Document the technical unknowns that must be resolved before replacing the IndexTTS-2 pipeline with `hexgrad/Kokoro-82M` so that the plan can be executed with confidence that latency, size, and voice-mapping expectations are realistic.

## Context
- Relevant modules: `services/tts/src/tts_service/synthesizer.py` (model loader), `main.py` (settings + Kafka loop), `services/tts/pyproject.toml` (dependencies), `docker-compose.yml` (runtime env/config).
- Current constraint: plan metrics target $RTF < 0.5$ and Latency P50 < 1,000 ms, while code today gears toward an 800+ MB IndexTTS-2 model that trips over timeouts.
- Pending pivot: replace `indextts` usage with a lightweight Kokoro implementation while keeping dual-mode payload handling/MinIO logic intact.

## Methodology
- Reviewed `synthesizer.py` and `main.py` to understand how the model is loaded, consumed, and connected to Kafka events.
- Inspected `pyproject.toml` and `docker-compose.yml` to enumerate current dependencies and live configuration flags (e.g., `TTS_MODEL_NAME`, `HF_TOKEN`).
- Cross-referenced plan requirements (speaker context pass-through, Observability contract, dual-mode transport) against the implementation that currently enforces `IndexTTS` exclusively.

## Findings

### Facts
- The synthesizer layer is hardwired to `IndexTeam/IndexTTS-2`, will raise `ValueError` if `TTS_MODEL_NAME` differs, and depends on the `indextts` package plus waveform prompt handling via `soundfile`.
- `main.py` instantiates `IndexTTS2Synthesizer`, warms it up once, and never exposes a pluggable interface; the service also enforces `correlation_id`-keyed Kafka output and dual-mode (inline vs URI) publishing with MinIO fallback.
- The current dependency set (see `pyproject.toml`) lacks the Kokoro-specific packages (`kokoro`, `phonemizer`, etc.) that the revised plan explicitly mentions.

### Hypotheses
- The Kokoro pipeline will require a different call pattern (text → phonemes → waveform) and needs explicit voice/style names; we must confirm what dependency (`kokoro` vs huggingface `transformers` pipelines) and configuration knobs are required to replicate the existing `synthesize(text, bytes)` signature.
- Speaker context mapping ($speaker_id$ → Kokoro style) is undefined today; the plan implies mapping to voices such as `af_bella`, but we do not yet know the canonical list of supported styles or how to supply them to the inferred API.
- Kokoro-82M still needs weight download; the service currently relies on `HF_TOKEN`, but we need to confirm that the new repo `hexgrad/Kokoro-82M` honors the same token semantics and whether caching/warmup requirements differ (e.g., local checkpoints, CPU-only operations).

## Recommendations
- Before locking the Kokoro plan, prototype the `kokoro` inference path (or read its documentation) to understand: initialization time, CPU/memory footprint, how to select style/voice, and whether it natively produces PCM suitable for the dual-mode pipeline.
- Capture the canonical voice/style IDs in a shared config map so the plan can specify what `speaker_id`s map to (e.g., `af_bella` default) and include fallback behavior when the mapping is missing.
- Expand the plan with a short spike that measures Kokoro-82M inference latency on the target hardware (warming up once and timing a representative phrase) to validate the $RTF$ and Latency targets before committing to the new synthesizer.

## Open Questions
- Which Python package actually hosts the Kokoro inference API (plain `kokoro`, `hexgrad`, or a custom wrapper) and what arguments does it expect for selecting styles? We need a reference usage snippet.
- Does Kokoro-82M support the same speaker prompt strategy (audio-in, zero-shot) that IndexTTS-2 offered, or must we rely solely on `speaker_id` style keys for now?
- Are there additional license, download, or HF token requirements for `hexgrad/Kokoro-82M` beyond the existing `HF_TOKEN` flow? If the model requires gating, plan needs to capture that dependency.
- Will the current `minio` dual-mode logic require adjustments if Kokoro produces longer audio (e.g., larger file sizes) even for short sentences, affecting when we switch to URI mode?

## Handoff
The synthesizer and main loop currently enforce IndexTTS-2. Swapping to Kokoro-82M requires (1) replacing `indextts` dependency with the correct Kokoro package, (2) understanding voice/style mapping for `speaker_id`, and (3) validating the new model meets the RTF and latency goals on CPU.

## Handoff to Implementer
**From**: Analyst
**Artifact**: agent-output/analysis/010-text-to-speech-analysis.md
**Status**: Draft
**Key Context**:
- The service is tightly bound to `IndexTeam/IndexTTS-2` and `indextts`; the plan’s Kokoro pivot demands a pluggable synthesizer that can accept `speaker_id` style hints while keeping the existing dual-mode logic.
- Dependencies/metrics in `pyproject.toml` and `docker-compose.yml` must be realigned (new packages, `TTS_MODEL_NAME`, `HF_TOKEN` usage).
**Recommended Action**: Research the Kokoro inference API and voice/style signals, prototype a `KokoroSynthesizer`, and document any new runtime requirements (license, warmup, voice mapping) so the plan can be finalized. # Value Statement and Business Objective
 The Text-to-Speech Epic 1.7 plan is delivering a `tts-service` that speaks translated text naturally for a hands-free speech-to-speech loop. The implementation must surface measurable proof (RTF, latency, payload mode) while honoring dual-mode transport, speaker context propagation, and contract guardrails.

 ## Changelog
 | Date | Summary |
 |------|---------|
 | 2026-01-25 | Initial analysis surfaced schema-evolution, URI failure semantics, and dataset provenance gaps identified by Critique 010 Revision 4. |
 | 2026-01-25 | Added implementation blockers: runtime verification of speaker-reference handling, MinIO/URI & retention integration, and the release artifact strategy implied by Plan 010. |

 ## Objective
 Document the technical unknowns encountered during the TTS implementation so the Planner and QA teams can resolve them before the feature is marked ready for UAT.

 ## Context
 - Plan 010 (Text-to-Speech) mandates dual-mode transport, speaker context pass-through, schema compatibility, a 24h MinIO lifecycle, and explicit observability/metrics.
 - Architecture Findings 011/006 reinforce the need for inline vs URI switching, `audio_uri` failure semantics, and optional speaker metadata across services.
 - QA Report 010 notes QA Failed because Kafka + Schema Registry + MinIO integration tests and object-store retrieval exercises have not been run yet, leaving the large-payload path and MinIO lifecycle assertions unverified.
 - Implementation Report 010 highlights assumptions about the IndexTTS-2 pipeline accepting speaker references and the dual-mode path working end-to-end and remarks that root-level release/version artifacts described in the plan do not exist in this repo structure.
 - Blocker: uncertain runtime behavior of `speaker_reference_bytes` (services/tts/src/tts_service/synthesizer.py and main.py) and the large-payload `audio_uri` path (services/tts/src/tts_service/storage.py, services/tts/minio-lifecycle.json) because integration tests have not exercised those flows.

 ## Root Cause
 - The `HuggingFaceSynthesizer` wrapper inspects the huggingface pipeline signature at runtime but has not yet been validated against the deployed `IndexTeam/IndexTTS-2` model, so it is unknown whether speaker cloning input is accepted or silently ignored.
 - The MinIO + Kafka integration path (large inline payload -> upload -> `audio_uri`) is still untested, so we lack evidence that downstream consumers observe a valid URI, respect the 24h retention lifecycle, or log/handle fetch failures as the plan stipulates.
 - Plan Step 5 (version management) references root-level release assets that do not exist in this workspace, leaving the release/version story undefined for TTS and making it unclear how to drive the `v0.5.0` target.

 ## Methodology
 - Reviewed Plan 010 Revision 6, Implementation 010, and QA Report 010 to understand the commitments, completed changes, and outstanding blockers.
 - Read the service code (`main.py`, `synthesizer.py`, `storage.py`, `config.py`) plus the MinIO lifecycle rule to map implementation details to the gate expectations.
 - Inspected shared schema, speech-lib, and test artifacts to confirm what parts of the pipeline are covered and where gaps remain.

 ## Findings
 ### Facts
 - `main.process_event()` and `HuggingFaceSynthesizer` try to pass `speaker_reference_bytes` to the huggingface pipeline when the signature advertises `speaker_wav`/`speaker_sampling_rate`, but no end-to-end run has yet confirmed that `IndexTeam/IndexTTS-2` uses those parameters (services/tts/src/tts_service/synthesizer.py).
 - The object-store path uploads to MinIO (services/tts/src/tts_service/storage.py) and relies on `services/tts/minio-lifecycle.json` for the 24h retention, yet QA shows integration tests that would create/upload a >1.5MB audio payload and then fetch it back have not been executed, so the consumer-facing behavior under normal and failure conditions remains undocumented.
 - The repo lacks the top-level `package.json`/`CHANGELOG.md` artifacts referenced in Plan Step 5, so the release/versioning work is currently blocked by not knowing where to record `v0.5.0` (Implementation Report 010, Outstanding Items).

 ### Hypotheses
 - If `IndexTeam/IndexTTS-2` does not support the speaker reference parameters that the wrapper enables, voice cloning will never trigger and the promised speaker context feature would degrade silently; the runtime logs or manual synthesis run will reveal whether the pipeline accepts `speaker_wav`/`speaker_sampling_rate`.
 - Without bringing up Kafka + Schema Registry + MinIO + TTS together, we cannot verify that consumers retrieving `audio_uri` log the configured `correlation_id`, gracefully skip on 404/timeouts, or proactively expire URIs after 24h; this places the dual-mode resilience requirements in limbo.
 - Because the release plan expects global version metadata but the repo currently tracks only service-level pyproject/smaller manifests, we might need to recalibrate the plan (Document a `VERSION` file or use `services/tts/pyproject.toml`) so that QA can cite a concrete artifact for `v0.5.0` delivery.

 ## Recommendations
 - Run a lightweight experiment (either an in-repo script or notebook) that instantiates the huggingface pipeline for `IndexTeam/IndexTTS-2` with a curated speaker reference bytes payload to confirm which `kwargs` it accepts and whether our fallback log path is exercised.
 - Execute the intended integration scenario with Docker Compose (Kafka+Schema Registry+MinIO+TTS) to upload a >1.5MB payload, download the resulting `audio_uri`, and simulate MinIO lifecycle/404 cases; capture logs/metrics so we can reason about `audio_uri` failure semantics and update the contract if necessary.
 - Clarify where the release/version target is declared (root-level versus service-level) and either create the missing `package.json`/`CHANGELOG.md` or adjust the plan to point at the existing `services/tts/pyproject.toml` so the version-management milestone can be marked as done.

 ## Open Questions
 - What are the exact parameter names and data shapes that `IndexTeam/IndexTTS-2` requires for speaker cloning, and does the current wrapper meet them? Is there a need for resampling or mono conversion before calling the pipeline?
 - How should downstream consumers (Translation, VAD, playback clients) detect and react when fetching `audio_uri` fails because the object was expired, missing, or MinIO was unreachable? Should they retry, drop with a logged error, or fall back to inline audio when available?
 - Which file or artifact does the plan expect us to bump for `v0.5.0`? Should we create a dedicated repo-level version manifest or rely on the existing service-level metadata to anchor the release? # Value Statement and Business Objective
The Text-to-Speech Epic 1.7 plan promises that users will hear translated text spoken naturally by implementing a `tts-service` with IndexTTS-2, dual-mode transport, and speaker-context propagation. This aligns with the platform goal of delivering a hands-free speech-to-speech loop while generating measurable evidence (RTF, latency, payload compliance) for the thesis.

## Context
- The latest architecture findings (011) define required constraints: dual-mode transport (D2), WAV-only output, correlation preservation, and explicit decisions around speaker context and failure semantics.
- The plan revision 3 attempts to close the previous critique gaps but still leaves research questions about schema evolution/compatibility and URI failure behavior.
- The critique (Revision 4) explicitly flags those gaps plus the need for a documented phrase dataset provenance.

## Identified Research Gaps
1. **Schema evolution/backward-compatibility strategy** for the newly added fields (`speaker_reference_bytes`, `speaker_id`, `audio_uri`, etc.) across shared Avro contracts and topic envelopes (Decision Gate 4.1).
2. **Object-store URI retrieval failure semantics**, especially how downstream consumers should react when a referenced MinIO URI is missing, expired, or otherwise unreachable (Architecture Findings 011.F).
3. **Dataset provenance for `tests/data/metrics/tts_phrases.json`** to ensure reproducible RTF/latency evidence and guardrails for naturalness.

## Investigation Approach
- Reviewed the plan (Revision 3) and critique (Revision 4) to collect the stated requirements, constraints, and outstanding blockers.
- Cross-referenced Architecture Findings 011 + 006 to understand the contract decision expectations concerning speaker context, failure semantics, and schema requirements.
- Examined the roadmap and existing artifacts to identify whether schema evolution guidance or dataset definitions already exist elsewhere in the repo (none found, so these remain assumptions).

## Findings
1. **Schema Evolution Expectation Remains Underspecified**
   - Plan adds optional speaker context fields to multiple topics but does not mention Schema Registry compatibility mode, versioning strategy, or how existing consumers/producers must handle the new optional fields.
   - Architecture guidelines stress strict contract decisions (Section 4.1). Without explicit guidance, downstream clients risk schema incompatibility or misinterpretation of new metadata.
2. **URI Retrieval Failure Policy is Incomplete**
   - Plan now answers what happens when the service cannot upload (log + default voice) but does not describe how downstream consumers must behave when `audio_uri` turns out to be stale/missing/unreachable.
   - Findings 011.F explicitly requires failure semantics for object store usage; lacking this raises resilience and observability risks.
3. **Dataset Provenance is Not Documented**
   - Plan references `tests/data/metrics/tts_phrases.json` but does not describe the source, curation criteria, or how the phrases exercise relevant lengths/languages. Thesis reproducibility depends on this documentation.

## Recommendations
1. Extend the plan’s contract section to explicitly state the Schema Registry compatibility expectations (e.g., maintain backward compatibility, treat new fields as optional, register with backward-compatible mode) and call out which producers/consumers must handle the new fields.
2. Add a consumer-facing failure policy for `audio_uri` retrieval:** specify what downstream components/logs should do when fetching a URI fails (retry window, fallback logging, correlation_id context), and describe how to detect/report such failures.
3. Document the phrase dataset contents/provenance (language, length, transcription source) either in the plan or a referenced file so the metrics are reproducible; include a guardrail for "naturalness" evaluation (e.g., sample list and evaluation steps).

## Open Questions
- Should schema evolution be gated through the existing Schema Registry CI workflow, or do these new optional fields require separate staging/testing before signing off?
- Which downstream components (e.g., clients consuming `AudioSynthesisEvent`) are responsible for attempting URI retrieval, and how should they expose failure metrics/logs for broken URIs?
- Can the dataset file be sourced from existing translation benchmarks, or does it need to be created anew? If new, who curates it and how is quality/coverage ensured?

## Next Steps
- Update the plan with the above contract clarifications and dataset documentation, then resubmit to the critic for verification.
- Optionally, capture the dataset definition in `tests/data/metrics/tts_phrases.json` (or a companion README) to make the metrics reference concrete.
