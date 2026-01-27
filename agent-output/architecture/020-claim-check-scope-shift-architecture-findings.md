# Architecture Findings 020: Epic 1.7 ↔ Epic 1.8 Dependency — Claim Check / Object Storage Scope Shift

**Date**: 2026-01-27
**Epic(s)**: Epic 1.7 (TTS), Epic 1.8 (Artifact Persistence)
**Related Roadmap**: agent-output/roadmap/product-roadmap.md
**Related Plan (future)**: agent-output/planning/010-text-to-speech-plan.md (Plan 010)
**Related Findings**: 013 (Epic 1.8), 019 (Plan 010)
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Trigger | Summary |
|------|---------|---------|
| 2026-01-27 | Dependency clarification (Epics 1.7/1.8) | Confirms TTS requires Claim Check + object storage sooner than v0.6.0; approves scope shift: deliver minimal MinIO/ObjectStorage enablement with Epic 1.7, keep Epic 1.8 as platform-wide rollout. |

## Context

The roadmap sequencing implies Epic 1.8 (Artifact Persistence / MinIO) happens after Epic 1.7 (TTS). Architecturally, this creates a hard dependency mismatch:
- Realistic TTS outputs can exceed Kafka payload invariants.
- The platform already adopts (and needs) the **Claim Check** pattern for blob artifacts.

Therefore, Epic 1.7 must either (a) impose fragile demo-only duration caps, or (b) introduce the minimal object storage capability earlier.

This review assesses the architectural implications of **pulling forward the minimal object storage + Claim Check enablement required by TTS**, while keeping the broader “persist artifacts across the whole pipeline” goal in Epic 1.8.

## Findings

### What Fits

- **De-risking Kafka invariants**: Introducing Claim Check for `AudioSynthesisEvent` avoids produce failures and keeps message size policy coherent.
- **Boundary integrity**: Treating this as “enablement in Epic 1.7” vs “rollout in Epic 1.8” preserves microservice independence while enabling auditability.
- **Graceful degradation**: Keeping storage optional (inline path when small; explicit behavior when large and storage disabled) aligns with the platform’s operability guardrail.

### Must Change (Required)

1) **Architecture master must reflect decision timing**
- The architecture master currently frames Claim Check as v0.6.0-first.
- Required: explicitly record that Claim Check is *piloted in v0.5.0 for TTS output* and becomes *platform-wide in v0.6.0*.

2) **Define the ownership model for URIs/keys (avoid credential leakage)**
- Required: events SHOULD carry an internal object key/reference, not a long-lived public URL.
- Required: presigned URL generation belongs at the edge (Gateway) when serving clients.
- Required: presigned URLs MUST NOT be logged.

3) **Standardize claim-check semantics; do not introduce ad-hoc fields**
- Required: blob-carrying events use consistent “inline bytes XOR reference” semantics, with explicit metadata (at minimum `content_type`, strongly recommended `sha256`).
- Required: schema evolution remains additive and compatible with Schema Registry `BACKWARD`.

4) **Retention, lifecycle, and deletion responsibilities must be explicit**
- Required: 24h default target retention (configurable).
- Required: lifecycle enforcement should be centralized (object store lifecycle policies preferred) rather than bespoke deletion logic in every service.

### Risks (To Track)

- **Operational dependency earlier**: v0.5.0 now depends on MinIO availability for large outputs. This is acceptable only if the inline-only fallback is still valid for small outputs and failure behavior is deterministic.
- **Shared-lib creep**: expanding `ObjectStorage` into a broader SDK will reintroduce coupling. Keep it thin and optional.
- **Security surface**: object store endpoints must remain internal-by-default in compose; avoid “public bucket” patterns.

## Required Integration Requirements (for future planning)

- Roadmap must state the scope split clearly:
  - Epic 1.7: minimal MinIO/ObjectStorage enablement + Claim Check for `AudioSynthesisEvent`.
  - Epic 1.8: extend Claim Check/persistence across Gateway/VAD/ASR + contracts where needed.
- Plan 010 must treat storage as optional and define explicit large-output behavior when storage is disabled.

## Consequences

- Epic 1.7 can ship with realistic TTS outputs without violating Kafka payload policy.
- Epic 1.8 remains valuable, but becomes a **platform rollout** epic rather than the enabling prerequisite.
