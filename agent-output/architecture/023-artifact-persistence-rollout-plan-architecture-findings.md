# Architecture Findings 023: Plan 022 — Artifact Persistence (Claim Check) Platform Rollout (Pre-Implementation Review)

**Related Plan (if any)**: agent-output/planning/022-artifact-persistence-rollout-plan.md
**Related Architecture**: agent-output/architecture/system-architecture.md
**Related Prior Findings**: 013, 020, 022
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | Planner | Pre-implementation architecture review | Plan is directionally correct and fits the Epic 1.8 guardrails, but must resolve naming/contract consistency and tighten shared-lib boundaries before implementation. |

## Context

- **What is being assessed**: Plan 022 rollout of Claim Check / artifact persistence across Gateway, VAD, ASR (and retrofitting TTS) using MinIO/S3.
- **Affected modules/boundaries**:
  - Event contracts in Schema Registry (Avro schemas)
  - Gateway, VAD, ASR, TTS services (producer/consumer behavior)
  - Shared `speech-lib` storage primitive boundary
  - Infrastructure `minio-init` (bucket + lifecycle policy ownership)

## Findings

### Must Change

1) **Eliminate bucket naming drift (`ingress` vs `audio-ingress`)**
- Plan WP2 names buckets `audio-ingress`, `vad-segments`, `asr-transcripts`, `tts-audio`, but WP3 examples use `s3://ingress/...`.
- **Requirement**: Choose the canonical bucket names and use them consistently in:
  - `s3://{bucket}/{key}` values carried in events
  - `minio-init` bootstrap + lifecycle config
  - documentation + QA evidence.

2) **Constrain shared library scope (avoid “SDK creep”)**
- WP1 proposes a reusable `ClaimCheckPayload` primitive.
- **Requirement**: Shared library MAY provide only:
  - deterministic formatting helpers (key/URI building),
  - thin storage primitives (put/get/head), and
  - a pure function for “inline vs reference” selection.
- Shared library MUST NOT embed orchestration policy (topic routing, retries, per-service branching, or service-specific workflows).

3) **Make failure behavior deterministic at the service boundary (not via uncaught exceptions)**
- Architecture requires: if payload exceeds inline cap and storage is unavailable/disabled, producers must **not publish oversized Kafka messages** and must emit a consistent failure signal.
- **Requirement**: Any shared-lib “oversize requires storage” error MUST be caught at the producer boundary and converted to:
  - drop/no-produce behavior,
  - structured error log keyed by `correlation_id`, and
  - a counter (at least `claim_check_failures_total`).

4) **Pin “traceparent propagation” mechanism**
- Plan requires `traceparent` propagation, but does not specify the transport.
- **Requirement**: Standardize on Kafka message headers for `traceparent` propagation (preferred) and require all services to copy incoming headers to outgoing messages.

5) **Ensure contract completeness for referenced blobs**
- Architecture guardrail requires explicit `content_type` metadata for any inline or referenced blob.
- **Requirement**: For every `*_uri` added/used, the schema MUST also carry or imply:
  - `content_type` (e.g., `audio/wav`, `application/json`), and
  - (if relevant) encoding / sample-rate metadata to keep downstream deterministic.

### Risks

- **Retrofit risk (WP6)**: Refactoring the TTS pilot concurrently with rollout increases regression probability; mitigate with strict backwards-compatible schema evolution and focused smoke tests.
- **YAGNI risk (WP5)**: ASR transcripts rarely exceed the cap; the work is acceptable only if it is near-zero incremental complexity via shared primitives.
- **Collision semantics**: “Last write wins” is acceptable for MVP, but it weakens auditability under retries; document as explicit limitation.

### Alternatives Considered

- **Use a reusable record type (e.g., `BlobRef`) instead of `*_uri` strings**
  - Pros: stronger schema validation, fewer one-off fields.
  - Cons: more schema churn now.
  - Decision: `*_uri` strings are acceptable for MVP, provided the grammar is pinned (`s3://bucket/key`) and metadata is explicit.

## Integration Requirements

- Schema evolution MUST remain additive and compatible with Schema Registry `BACKWARD` (or stricter) mode.
- All blob-carrying events MUST satisfy XOR semantics (inline bytes XOR URI).
- Presigned URLs MUST NOT appear in events; presigning remains an edge concern (Ingress Gateway read-path).
- Lifecycle/retention MUST be enforced centrally via `minio-init` and validated with reproducible evidence.

## Consequences

- Approving this plan (with changes) keeps the architecture consistent with Epic 1.8 guardrails (non-secret references, centralized retention, deterministic oversize protection).
- The required changes prevent cross-service drift (bucket naming) and prevent accidental shared-lib orchestration.

## Handoff

## Handoff to Implementer

**From**: Architect
**Artifact**: agent-output/architecture/023-artifact-persistence-rollout-plan-architecture-findings.md
**Status**: APPROVED_WITH_CHANGES
**Key Context**:
- `s3://bucket/key` is the canonical non-secret reference; presigned URLs are edge-only.
- Bucket names and metadata requirements must be consistent across schemas, infra, and services.

**Recommended Action**: Apply the “Must Change” items above as prerequisites, then proceed with implementation of Plan 022.
