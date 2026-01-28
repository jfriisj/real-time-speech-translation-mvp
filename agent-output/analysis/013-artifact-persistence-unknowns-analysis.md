# Analysis 013: Artifact Persistence Unknowns

**Plan Reference (if any)**: agent-output/planning/010-text-to-speech-plan.md
**Status**: Draft

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | Planner/Architect | Investigate architectural unknowns | Surface the open questions that still block the Claim Check artifact-persistence decision for Epic 1.8 rollout.

## Objective

Answer the concrete unknowns that must be resolved before finalizing the Claim Check/object-storage architecture (Epic 1.8 rollout, leveraging the TTS pilot). The questions are:

1. Should `audio_uri` and similar fields emit internal storage keys (bucket+path) or full presigned URLs? Where is the presigning responsibility placed?
2. Who owns the lifecycle (naming, retention, cleanup) of the objects created for the Claim Check pattern before Epic 1.8 expands persistence across the pipeline?
3. What is the required behavior when storage is disabled or unreachable while a payload exceeds the inline Kafka limit (1.25 MiB)?

Target area: shared storage helper + Claim Check event transport (TTS service and the broader pipeline with Gateway/VAD/ASR).

## Context

- Relevant modules/files: `agent-output/planning/010-text-to-speech-plan.md` (Claim Check assumptions), `shared/speech-lib/src/speech_lib/storage.py` (current ObjectStorage helper), `agent-output/architecture/system-architecture.md` (Claim Check guardrails) and the newly created Epic 1.8 architecture findings.
- Known constraints: Kafka inline payload limit of 1.5 MiB, Claim Check requirement for payloads > 1.25 MiB, 24-hour retention guardrail, presigned URLs must not be logged, services must remain operable without storage.

## Methodology

- Reviewed the TTS plan to itemize existing assumptions about storage behavior, key naming, and fallback modes.
- Inspected the shared `ObjectStorage` helper to understand how it currently surfaces object references and presigned URLs.
- Cross-referenced architecture guardrails (Decisions about Claim Check, retention, and presigned URLs) to see which questions remain unanswered.

## Findings

### Facts

- Plan 010 forces the Claim Check pilot to live inside Epic 1.7: `TTS_AUDIO_URI_MODE` currently defaults to emitting an internal key (`tts/{correlation_id}.wav`) and leaves presigning to the Gateway, but this contract is not enforced or validated (Plan section “Contract Decisions” and “Assumptions”).
- The shared `ObjectStorage.upload_bytes` helper currently returns a presigned URL by default (`presign_get`) unless `return_key` is requested; there is no exposed option to request just the internal bucket/key (shared/speech-lib/src/speech_lib/storage.py).
- Architecture decisions now demand that Claim Check references be either inline bytes or a non-secret reference, with presigned URLs generated at the edge and not logged. The recent Findings 022 reiterate this, but no enforcement strategy exists yet.

### Hypotheses

- Without clarifying the return value of `ObjectStorage.upload_bytes`, implementers may continue to publish presigned URLs directly in events, conflicting with the non-secret guardrail and increasing credential leakage risk.
- Lifecycles are currently left to MinIO bucket policies (`minio-lifecycle.json`), but it is unclear which service (TTS vs. platform operations) owns the naming, TTL configuration, and cleanup validation, leaving room for orphaned objects or inconsistent retention.
- With storage disabled/unavailable, the plan’s “log-and-drop” fallback is described informally, but the broader pipeline may need a more deterministic signal to avoid hidden data loss or silent correlation breaks.

## Recommendations

- Explicitly update the shared storage helper (or wrapper) so that the default Claim Check path emits the internal bucket/key reference and optionally allows presigned URLs only when explicitly requested by the edge. Document this change and align all services accordingly.
- Define the lifecycle ownership (key naming format, TTL config, cleanup verification) in the architecture/plan documents so that future rollout (Epic 1.8) can reuse the same invariant rather than introducing conflicting schemes per service.
- Capture deterministic failure semantics for storage-down scenarios as part of Epic 1.8 planning: e.g., `raise OversizePayloadError`, emit a warning metric/log with the `correlation_id`, and keep the inline path as the only valid fallback; do not allow silent drops.

## Open Questions

1. Should the Claim Check helper return only non-secret bucket+key references, or do some services still need to embed presigned URLs (and if so, who logs/refreshes them)?
2. Who is responsible for managing object lifecycle policy (key naming, TTL, cleanup validation) inside the current v0.5.0 pilot so Epic 1.8 can extend it safely? (TTS service ownership vs. dedicated platform ops/deployment in MinIO?)
3. What exact signal should we emit when Claim Check storage is unavailable for an oversized payload: log + drop (status quo), an error event, or a dead-letter entry?

## Handoff

## Handoff to Planner/Architect

**From**: Analyst
**Artifact**: agent-output/analysis/013-artifact-persistence-unknowns-analysis.md
**Status**: Draft
**Key Context**:
- The pilot already assumes Claim Check, but key semantics, lifecycle ownership, and failure signaling remain unspecified.
**Recommended Action**: Resolve the three open questions above and document the guardrails in the forthcoming plan/architecture updates so that Epic 1.8’s Claim Check rollout has a solid, consistent foundation.
