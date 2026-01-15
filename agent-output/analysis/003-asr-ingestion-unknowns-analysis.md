# Analysis 003: ASR Ingestion Unknowns

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-15 | Architect | Investigate blocking unknowns for Epic 1.2 (ASR) | Added pre-planning context for CPU inference latency, model caching, and format validation requirements |

## Value Statement and Business Objective
**As** the architect validating Epic 1.2,
**I need** to resolve the performance, packaging, and ingestion-format unknowns that are stalling the CPU-only ASR architecture,
**So that** we can commit to the shared contract, tooling, and infrastructure assumptions without rework in the v0.2.0 release.

## Objective
Answer the following questions before the ASR architecture is finalized:
1. Can `openai/whisper-tiny` running on CPU deliver acceptable latency for 1.5 MiB audio payloads that we plan to cap per `AudioInputEvent`?
2. How should the Whisper model be installed and cached so the ASR container starts deterministically (build-time download vs runtime fetch) without blocking tooling or CI? 
3. Does the `wav`-only mandate require active format validation in `shared/speech-lib`/the ASR consumer or can we safely rely on the `audio_format` metadata and downstream logging?

## Context
- **Plan under review**: agent-output/planning/002-asr-service-plan.md (ASR Service, Epic 1.2).
- **Architecture master**: agent-output/architecture/system-architecture.md (defines canonical topics, contract artifact limits, failure signaling, and CPU-only requirement inherited from v0.1.0).
- **Target area**: `services/asr` ingestion/transcription pipeline + `shared/speech-lib` producer/consumer helpers (constants, payload validation, and Kafka wrappers) because these modules enforce size/format rules and host the interaction with the Whisper model.
- **Constraints**: `AudioInputEvent` must cap inline audio to 1.5 MiB (shared constants reference `AUDIO_PAYLOAD_MAX_BYTES`). The ASR service must run on CPU-only nodes for local/CI builds.

## Root Cause
The architecture decision to keep ASR CPU-only with 1.5 MiB inline audio is blocked because we lack empirical evidence that `openai/whisper-tiny` achieves the required latency on target hardware and because the plan does not prescribe where/how the Whisper model is fetched/cached; without these answers we cannot size resources or trust container startup, nor can we ensure that non-`wav` payloads are handled consistently.

## Methodology
- Reviewed the ASR plan (agent-output/planning/002-asr-service-plan.md) for stated constraints, risks (model download, format complexity), and acceptance criteria.
- Examined the shared contract/infra definitions (agent-output/architecture/system-architecture.md) to confirm the CPU-only + failure-handling mandates and the expectation that the shared `speech-lib` enforces payload invariants.
- Inspected the shared library (`shared/speech-lib/src/speech_lib/`) to understand how constants, event payloads, and Kafka wrappers currently enforce size checks and which fields are available for validation.

## Findings
### Facts
- Plan 002 explicitly requires ASR to consume `AudioInputEvent`, respect the 1.5 MiB payload cap, and run on Python 3.11/3.12 on CPU, while also noting a model-download reliability risk and audio-format complexity risk (see ##3 assumptions & constraints and ##6 risks in the plan).
- The shared library exposes `AUDIO_PAYLOAD_MAX_BYTES` = 1.5 MiB and `KAFKA_MESSAGE_MAX_BYTES` = 2 MiB, and the producer/consumer wrappers raise on serialized payloads that exceed these limits, but there is no enforcement that `audio_format` equals `"wav"` beyond the ASR plan’s “try to process anyway” comment.
- Architecture decisions in system-architecture.md now mandate CLI/script ingestion, pinned topic names, logging+dropping failure semantics, and at-least-once delivery; these contract guarantees assume the ASR service does not stall on model downloads or time-consuming format probing.

### Hypotheses
- `openai/whisper-tiny` running on a CPU-only container may take longer than the max audio duration implied by 1.5 MiB (~45–50 seconds of 16-bit mono PCM) to finish inference, which could break the “low-latency real-time” intent unless we can run it on small audio slices or accept higher latency.
- Downloading the Whisper model at runtime for every container startup will delay the service boot and strain offline/CI workflows; a build-time cache or baked-in weights may be necessary but requires adjusting the Dockerfile and storage expectations.
- Without an explicit validation layer, mislabeled `audio_format` fields (e.g., claiming `wav` but sending FLAC) could reach `openai/whisper-tiny` and either fail or silently degrade quality; the architecture needs to decide whether format validation belongs in the shared contract helpers or inside the ASR consumer.

## Recommendations
1. Benchmark `openai/whisper-tiny` inference on representative CPU hardware using a sample `wav` near 1.5 MiB to quantify the per-second latency and determine whether additional chunking, a smaller model, or GPU acceleration is required for the v0.2.0 real-time objective.
2. Decide on a caching strategy: either fetch the Whisper model during the image build and bake it into the container or prepopulate a shared HF cache volume before running the service, so that startup does not depend on remote downloads; document these steps in the plan and compose file.
3. Clearly assign format validation to a layer: either extend `shared/speech-lib` to raise when `audio_format != "wav"` before ASR consumes it, or have the ASR service inspect byte headers, but ensure that the chosen guardrail is codified in the architecture doc so downstream services know the expectation.

## Open Questions
- What is the average inference time for `openai/whisper-tiny` on the same CPU profile we intend for the ASR container, given the longest allowed `AudioInputEvent` payloads (∼45 seconds)?
- Should the Whisper model be part of the image (build-time download) or cached via a shared volume so that container startup is deterministic and CI tooling stays within quarantine limits?
- Where is the authoritative location for enforcing `audio_format == "wav"`—the shared `speech-lib`, the ASR consumer, or the external producer—and how does that decision affect developer handoffs?

## Handoff
**From**: Analyst
**Artifact**: agent-output/analysis/003-asr-ingestion-unknowns-analysis.md
**Status**: Draft
**Key Context**:
- Epic 1.2 depends on a CPU-only Whisper inference path that respects the 1.5 MiB contract; performance and caching assumptions are not yet validated.
- The shared contract (speech-lib + architecture master) enforces payload size but not format labels, so the unknown about format validation remains unresolved.
**Recommended Action**: Assign someone (Planner/Implementer) to benchmark Whisper CPU latency, decide on model caching strategy, and codify where format validation lives before locking the ASR architecture for v0.2.0.
