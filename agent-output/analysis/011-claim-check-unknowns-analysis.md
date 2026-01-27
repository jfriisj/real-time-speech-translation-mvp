# Analysis 011: Claim Check Scope Shift Unknowns

**Plan Reference (if any)**: agent-output/planning/010-text-to-speech-plan.md
**Status**: Draft

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | Architect/Planner | Investigate architectural unknowns | Captured blocking questions about object storage lifecycle, fallback behavior, and URI semantics before we finalize the Claim Check scope shift. |

## Objective

Determine which architectural unknowns still block the decision to pull the minimal Claim Check/object-storage enablement into Epic 1.7 (TTS) while keeping Epic 1.8 as the platform-wide rollout.

## Context

- Relevant modules/files: agent-output/planning/010-text-to-speech-plan.md, agent-output/architecture/system-architecture.md, shared/schemas/avro/AudioSynthesisEvent.avsc, shared/storage utilities.
- Known constraints: Claim Check semantics already mandated for blob-carrying events (inline bytes XOR external URI); MinIO/S3 infrastructure is optional for v0.5.0 but required for larger payloads; retention guardrail targets 24h and presigned URLs must not be logged.

## Methodology

- Reviewed the current TTS plan to surface missing requirements around object storage integration, fallback behavior, and schema metadata.
- Cross-referenced the architecture master and Findings 013/019/020 to understand existing guardrails (Claim Check, TTL, security) and where detail gaps remain.
- Examined shared storage helper expectations to identify what still needs alignment before we treat TTS as the Claim Check pilot.

## Findings

### Facts
- The plan has already defined `audio_bytes` XOR `audio_uri`, enforces the XOR invariant, and says Claim Check is mandatory for payloads > 1.25 MiB, but it does not describe how URIs are created nor how long they remain valid.
- The architecture master requires a default 24-hour retention and prohibits logging presigned URLs, but it does not yet say who owns lifecycle enforcement or how keys should be formed for the early TTS pilot.
- MinIO/ObjectStorage is delivered with Epic 1.7 as an optional dependency, yet no plan text spells out fallback behavior (e.g., `DISABLE_STORAGE=true` case) or what TTS should do when the bucket is unavailable.

### Hypotheses
- Without a defined key/naming scheme and lifecycle owner, each service may invent its own format, creating orphaned objects or forcing duplicate retrieval logic in Epic 1.8.
- Without explicit storage failure behavior, implementers might crash or downgrade silently when MinIO is absent, undermining the architecture’s requirement that the service remain operable without storage.
- Without clear guidance that TTS should emit internal object keys (not permanent URLs) and let the Gateway re-sign when serving clients, we risk leaking credentials or introducing inconsistent refresh logic.

## Recommendations
- Define the ownership model for object keys and lifecycle: decide whether TTS should generate time-bounded object keys per `correlation_id` and whether a central job or MinIO lifecycle policy handles TTL/cleanup.
- Document the fallback behavior when storage is disabled/unavailable: the service should log-and-drop large outputs while continuing to serve inline payloads for smaller texts, and QA must have a test to verify the warning log.
- Clarify that `audio_uri` should reference an internal object key (no long-lived public URL) and that Gateway (or another edge boundary) is responsible for presigning/refreshing access when needed.
- Capture retention expectations in plan-level acceptance criteria (24h default, configurable) so that Epic 1.7’s pilot carries the same guardrail as the platform rollout.

## Open Questions

1. Who owns the object storage lifecycle for TTS-created artifacts (key naming, TTL, deletion) before Epic 1.8 expands persistence to other services?
2. What should TTS do when MinIO is unreachable but the text requires Claim Check (payload > 1.25 MiB)—log-and-drop, fall back to inline with warning, or block synthesis?
3. Should `audio_uri` always carry an internal object key/ID, or may TTS emit a presigned URL directly, and if so, how do we prevent logging/exposure of that secret?

## Handoff

## Handoff to Planner/Architect

**From**: Analyst
**Artifact**: agent-output/analysis/011-claim-check-unknowns-analysis.md
**Status**: Draft
**Key Context**:
- TTS is now the Claim Check pilot, but several integration details remain unspecified: lifecycle ownership, failure modes when storage is missing, and `audio_uri` semantics.
**Recommended Action**: Answer the open questions above and document the required guardrails before we lock in the architecture decision for Epic 1.7.