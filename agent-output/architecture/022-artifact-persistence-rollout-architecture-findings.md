# Architecture Findings 022: Epic 1.8 Artifact Persistence — Platform Rollout (Claim Check)

**Date**: 2026-01-27
**Epic**: Epic 1.8 (Artifact Persistence / Observability & Persistence)
**Related Roadmap**: agent-output/roadmap/product-roadmap.md
**Related Prior Findings**: 013 (Epic 1.8 constraints), 020 (scope shift: pilot in Epic 1.7)
**Related Plan (future)**: agent-output/planning/022-artifact-persistence-rollout-plan.md
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Trigger | Summary |
|------|---------|---------|
| 2026-01-27 | Start Epic 1.8 (pre-planning) | Approves platform-wide rollout of artifact persistence using the Claim Check pattern, with required constraints on contract evolution, URI/key semantics, lifecycle/retention, and failure behavior. |

## Context

Epic 1.7 has already pulled forward the **enablement** layer:
- Optional MinIO/S3 infrastructure in local compose
- A thin `ObjectStorage` capability in the shared library
- Claim Check semantics piloted for `AudioSynthesisEvent` (TTS output)

Epic 1.8 is now a **platform rollout** epic: extend persistence and Claim Check usage across pipeline stages to support thesis-grade auditability, without violating Kafka message-size invariants.

In scope for rollout (minimum):
- Ingress audio artifacts (Gateway → `AudioInputEvent`)
- VAD speech segment artifacts (`SpeechSegmentEvent`)
- Synthesized speech artifacts (`AudioSynthesisEvent`) — already piloted, but ensure consistency

## Architectural Implications

### 1) Contract evolution must be uniform and backwards-compatible

**Requirement**: Blob-carrying events MUST implement a consistent “inline bytes XOR external reference” semantics.
- Exactly-one-of invariant (XOR): either inline bytes are present OR an object reference is present
- Include explicit `content_type` for any referenced or inline blob
- Schema evolution MUST be additive to preserve Schema Registry compatibility (`BACKWARD` or stricter)

**Recommended (non-binding) contract shape**:
- Prefer a reusable record type (e.g., `BlobRef`) that can be embedded in events that carry artifacts, rather than introducing one-off fields per event.

### 2) `*_uri` semantics must not leak credentials

**Requirement**: Events MUST NOT carry long-lived public URLs by default.
- Events SHOULD carry an internal object reference (key/path + bucket) or a non-secret URI.
- Presigned URL generation/refresh SHOULD be an edge concern (Ingress Gateway when serving clients), not a responsibility of internal producers.
- Presigned URLs MUST NOT be logged in full.

### 3) Lifecycle/retention is a platform concern (not bespoke per service)

**Requirement**: Artifact retention MUST be time-bounded.
- Default target: 24 hours, configurable by environment
- Preferred enforcement: object-store lifecycle policies (centralized), not per-service delete loops

**Requirement**: Key naming must support auditability and correlation.
- Canonical key scheme MUST be documented and consistent across services.
- Keys MUST incorporate `correlation_id` and stage identity (e.g., `gateway`, `vad`, `tts`).
- Keys MUST NOT encode PII.

### 4) Failure behavior must be deterministic (and protect Kafka invariants)

Object storage introduces a new operational dependency. The rollout MUST define explicit producer behavior for these cases:

- **Storage disabled**:
  - If payload fits within inline size policy: produce inline bytes.
  - If payload would exceed inline policy: MUST NOT attempt to publish an oversized Kafka message; must fail deterministically (clear error log + traceable signal).

- **Storage enabled but unavailable**:
  - Same as above: do not publish oversized payloads.
  - Degrade with clear logs keyed by `correlation_id` and stage.

**Note**: Whether the traceable signal is an error event, a dead-letter topic, or a metrics/log-only approach is a planning choice, but it MUST be consistent across services.

### 5) Shared library scope must stay thin

**Constraint**: The shared library may provide storage primitives and minimal helpers, but MUST NOT become an application SDK.
- Avoid embedding orchestration policy (routing, retries, per-service workflows) in shared.
- If a shared helper is introduced for key naming, it must be purely deterministic formatting (no business branching), and must remain optional.

## Required Changes (Blockers for Planning)

1) **Define the canonical object reference representation**
   - Decide: internal key reference (preferred) vs presigned URL allowed in events
   - Decide: where presigning happens (recommended: Gateway/edge)

2) **Define and document the canonical key scheme**
   - Must support correlation-centric audits and stage separation
   - Must not embed secrets/PII

3) **Define consistent failure behavior across producers**
   - Oversize protection is non-negotiable
   - Storage outage semantics must be explicit

4) **Define lifecycle evidence requirements**
   - Minimum: documented lifecycle configuration + retention default
   - Avoid ad-hoc deletion logic proliferation

## Integration Requirements

- Shared contract artifact must evolve to support Claim Check consistently for ingress, VAD segment, and TTS output artifacts.
- Gateway must be treated as the edge boundary for any client-facing access to stored artifacts (presigning/authorization).
- QA must validate at least:
  - Inline mode (storage disabled)
  - Claim Check mode (storage enabled)
  - Storage outage behavior (enabled but unreachable)
  - No oversized Kafka publish attempts

## Consequences

- Improves auditability and enables post-hoc qualitative inspection of pipeline stages.
- Adds operational complexity (new dependency + lifecycle configuration).
- Raises governance requirements for sensitive audio handling; TTL and log hygiene are mandatory.
