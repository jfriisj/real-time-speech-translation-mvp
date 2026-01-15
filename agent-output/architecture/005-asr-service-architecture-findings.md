# Architecture Findings 005: Audio-to-Text Ingestion (ASR Service) — Pre-Planning Review

**Date**: 2026-01-15
**Epic**: 1.2 Audio-to-Text Ingestion (ASR Service)
**Roadmap Reference**: agent-output/roadmap/product-roadmap.md
**Existing Plan (mapping)**: agent-output/planning/002-asr-service-plan.md
**Assumed Future Plan Name (per request)**: agent-output/planning/005-asr-service-plan.md
**Architecture Master**: agent-output/architecture/system-architecture.md

**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Trigger | Summary |
|------|---------|---------|
| 2026-01-15 | Roadmap Epic 1.2 pre-planning gate | Identified required plan alignment to prevent contract/topic drift; pinned MVP audio format + failure signaling + delivery semantics |

## Scope of Review
This review assesses architectural implications and non-negotiable constraints for Epic 1.2 before further planning:
- Contract adherence (`AudioInputEvent` → `TextRecognizedEvent`), including payload size policy
- Topic taxonomy and Schema Registry governance alignment with v0.1.0 infrastructure
- Service boundary (what belongs in ASR vs the shared contract artifact)
- Operational constraints (CPU-only, containerization, model distribution)

## What Fits (No Change Required)
- **Event-driven service boundary**: ASR as a consumer/producer microservice aligns to the walking-skeleton architecture.
- **Contract fields**: The schema fields used in the plan (`audio_bytes`, `audio_format`, `sample_rate_hz`, `language_hint`) match the canonical Avro schema.
- **Payload size enforcement**: The plan correctly enforces the 1.5 MiB cap and drop behavior.

## Must Change (Required)

1. **Topic names must match the architecture master**
   - Current plan text uses topics `audio-input` and `text-recognized`.
   - Architecture master (and the v0.1.0 smoke test) pins:
     - Input topic: `speech.audio.ingress`
     - Output topic: `speech.asr.text`
   - Requirement: update the plan to use the pinned topic taxonomy everywhere (including any tests and examples).

2. **Clarify MVP audio format support (avoid multi-format creep)**
   - The current plan suggests “try to process anyway” if `audio_format` is not `wav`.
   - Requirement: for MVP, accept only `audio_format == "wav"`; otherwise log and drop.
   - Rationale: multi-format decode expands dependencies (`ffmpeg`/codecs), increases non-determinism, and creates integration ambiguity.

3. **Do not introduce new error-event schemas in Epic 1.2**
   - The roadmap/plan language mentions “error logs/events”. There is no canonical error-event schema in the contract set.
   - Requirement: MVP failure behavior is logging + dropping (no crash, no new schemas). If error events are needed, introduce a dedicated epic and schema set.

## Should Change (Strong Recommendations)

1. **Make the “external producer” an explicit boundary**
   - The architecture expects an external producer/CLI/script to publish `AudioInputEvent`.
   - Recommendation: keep audio capture/upload out of the ASR service for MVP (avoid building an HTTP ingestion API unless explicitly required by the demo).

2. **Pin model identity for reproducibility**
   - Recommendation: specify an explicit model identifier/version (and caching strategy) so dev/CI runs are stable.

3. **Plan for at-least-once delivery**
   - Recommendation: document that duplicate events are acceptable in MVP and should not break downstream processing.

## Key Risks
- **Topic drift risk**: If ASR uses `audio-input` / `text-recognized`, it will not interoperate with the v0.1.0 smoke-tested topic taxonomy.
- **Operational risk (model download)**: First-run downloads can be slow/flaky; plan should describe caching/volumes.
- **Surface area creep**: Supporting arbitrary audio formats and/or adding error-event schemas increases shared-contract churn.

## Alternatives Considered
- **Multiple audio formats in MVP**: Rejected (adds codec/tooling complexity and increases failure modes).
- **Emit error events for failures**: Deferred (requires new schema contract, compatibility rules, and consumer behaviors).

## Integration Requirements (Non-Negotiable)
- Use canonical topics:
  - `speech.audio.ingress` (input)
  - `speech.asr.text` (output)
- Preserve `correlation_id` from input to output.
- Enforce payload size: drop events with `len(audio_bytes) > 1.5 MiB`.
- CPU-only execution for local/CI.
- Shared contract artifact remains narrow (schemas + serialization/envelope/correlation helpers only).

## Architecture Master Updates
- The architecture master was updated with Epic 1.2 guardrails (topics, audio format, failure signaling, and delivery semantics): agent-output/architecture/system-architecture.md

## Handoff Notes (Planner / Implementer)
- Treat topic names as part of the contract surface; do not “rename for readability”.
- Keep the ASR service focused on transcription; keep ingestion/demo publishing in a producer script or a separate ingress component.
- If you need error events or large-audio reference patterns, escalate to a new epic + architecture decision.
