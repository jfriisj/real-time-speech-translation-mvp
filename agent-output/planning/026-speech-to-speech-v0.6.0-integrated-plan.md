---
ID: 026
Origin: 026
UUID: 01accc6c
Status: Active
---

# Plan 026: Speech-to-Speech v0.6.0 Integrated Delivery (Stability → Persistence → TTS)

**Target Release**: v0.6.0
**Epic Alignment**: Epic 1.3 (Diagnostics/Stabilization), Epic 1.9 (Startup Resilience), Epic 1.8 (Artifact Persistence), Epic 1.7 (TTS)
**Status**: Active
**Plan Owner**: Planner Agent
**Date**: 2026-01-28

## Changelog
| Date | Agent | Request | Summary |
|------|-------|---------|---------|
| 2026-01-28 | Planner | Create integrated plan | Consolidates sequencing and delivery for Epics 1.3, 1.9, 1.8, 1.7 under Target Release v0.6.0. |

## 1. Value Statement and Business Objective
**As** an Operator/Contributor,
**I want** a single, stable, end-to-end speech-to-speech pipeline (Translation → TTS) with predictable startup and auditable artifacts,
**so that** the system can be validated reliably (thesis-grade evidence) without roadmap/plan drift or flaky bring-up.

## 2. Objective
Deliver a v0.6.0 release train where:
- The platform starts deterministically (startup resilience invariant upheld).
- Translation is stable enough to act as a reliable upstream for TTS.
- Artifact persistence (Claim Check) is rolled out across the pipeline stages that carry large/valuable artifacts.
- TTS produces `AudioSynthesisEvent` without violating Kafka payload invariants.

## 3. Context & Roadmap Alignment
The roadmap enforces dependency order:
- **Epic 1.9 → Epic 1.8 → Epic 1.7**

This plan adopts **Option A** governance choice:
- **Target Release is v0.6.0**, and Epic 1.7 (TTS) is treated as part of the v0.6.0 delivery train (v0.6.x) to avoid a release-target contradiction where 1.7 depends on 1.8.

## 4. Inputs (Prior Art)
This integrated plan consolidates and references existing artifacts (kept for traceability):
- Plan 003: Translation Diagnostics/Stabilization (`agent-output/planning/003-translation-service-plan.md`)
- Plan 025: Startup Resilience (`agent-output/planning/025-service-startup-resilience-plan.md`)
- Plan 022: Artifact Persistence Rollout (`agent-output/planning/022-artifact-persistence-rollout-plan.md`)
- Plan 010: TTS Detailed Design (`agent-output/planning/010-text-to-speech-plan.md`)

## 5. Assumptions & Constraints
Architecture guardrails (non-negotiable):
- Shared library remains thin (schemas/bindings/serialization primitives; no orchestration policies).
- Audio format policy (MVP): `audio_format == "wav"` only; unsupported formats are logged and dropped.
- Claim Check guardrails:
  - Events carry **non-secret** object references (e.g., `s3://bucket/key`), not presigned URLs.
  - XOR invariant: exactly one of inline bytes vs URI/reference.
  - Retention is time-bounded (default 24h) and centrally owned.
- Startup resilience is a platform invariant (bounded waits, clear logs, non-zero exit on timeout).

## 6. Plan (Milestones)

### Milestone 0: Release Governance Alignment
**Objective**: Remove release-target contradictions and ensure the roadmap and release artifacts are consistent with the enforced dependency order.
- Confirm Epic placement for v0.6.0 train: 1.3 stabilization → 1.9 invariant upheld → 1.8 rollout → 1.7 enablement.
- Update roadmap/release documentation to reflect Epic 1.7 is delivered as part of the v0.6.0 train (v0.6.x) rather than v0.5.0, if necessary.

**Acceptance Criteria**:
- A single source-of-truth statement exists for the order and release grouping (v0.6.0 train).

### Milestone 1: Translation Stability as a TTS Prerequisite (Epic 1.3)
**Objective**: Ensure translation is stable enough to act as an upstream dependency for TTS.
- Ensure translation service startup is resilient to Schema Registry/Kafka readiness races.
- Ensure diagnostics/regression validation can be executed in the target environment (containerized where required).

**Acceptance Criteria**:
- Translation produces `TextTranslatedEvent` reliably with correlation continuity.
- Diagnostic evidence is recorded as an auditable artifact (location and format defined by implementer/QA/UAT conventions).

### Milestone 2: Startup Resilience Invariant Verified (Epic 1.9)
**Objective**: Ensure the platform remains predictably startable as new dependencies (MinIO) and services (TTS) are introduced.
- Confirm readiness gating exists and is consistently configured across gateway/vad/asr/translation/tts.
- Confirm bounded waits and safe logging.

**Acceptance Criteria**:
- Cold-start convergence is repeatable enough for downstream E2E verification.
- Failure mode is controlled (timeouts produce non-zero exits; no infinite hangs).

### Milestone 3: Artifact Persistence Rollout (Claim Check) (Epic 1.8)
**Objective**: Roll out Claim Check across Gateway/VAD/ASR (and align TTS outputs) to enable auditability and enforce Kafka payload safety.
- Standardize `*_uri` semantics and required metadata for referenced blobs.
- Centralize lifecycle/retention ownership (MinIO init + policy evidence).
- Standardize trace propagation via Kafka headers.

**Acceptance Criteria**:
- Oversized payloads are never published to Kafka.
- Claim Check references are non-secret and retrievable within retention.

### Milestone 4: TTS Enablement (Kokoro ONNX) (Epic 1.7)
**Objective**: Implement or finalize the TTS service so it consumes translation output and emits synthesized audio safely.
- Keep synthesizer pluggable (factory) and runtime stable on CPU.
- Enforce payload transport policy (inline vs URI) and align with platform Claim Check semantics.

**Acceptance Criteria**:
- `AudioSynthesisEvent` is produced with XOR invariant respected.
- No Kafka payload invariant violations occur during synthesis.

### Milestone 5: End-to-End Speech-to-Speech Demonstration Readiness
**Objective**: Validate the integrated pipeline is “demo-ready” as a coherent system.
- Ensure the full path Gateway/VAD/ASR/Translation/TTS runs under the same governance constraints (correlation, tracing, payload policies).

**Acceptance Criteria**:
- End-to-end flow is observable and explainable (correlation continuity; stage logs/traces).

### Milestone 6: Version Management & Release Artifacts (v0.6.0)
**Objective**: Ship the v0.6.0 release train with consistent versioning and documentation.
- Update version files and changelog.
- Ensure release documentation reflects the integrated scope.

**Acceptance Criteria**:
- Version artifacts match v0.6.0.
- CHANGELOG includes the combined deliverables and sequencing rationale.

## 7. Validation (High Level)
- Static checks (lint/format) for changed services and shared library.
- Automated checks at appropriate granularity (unit + integration + end-to-end) to confirm pipeline viability.
- Operational validation: cold-start bring-up and controlled dependency-failure behavior.

## 8. Risks & Mitigations
- **Risk**: Release-target drift (1.7 vs 1.8 ordering).
  - **Mitigation**: Lock v0.6.0 train as source-of-truth; document explicitly in roadmap/release artifacts.
- **Risk**: Shared-lib creep while standardizing Claim Check.
  - **Mitigation**: Keep shared-lib limited to primitives; keep orchestration and retries at service boundary.
- **Risk**: New dependency (MinIO) introduces new failure modes.
  - **Mitigation**: Deterministic drop/no-produce behavior when storage is unavailable; strong startup gating.

## 9. Open Questions
- None (Target Release choice confirmed: Option A / v0.6.0).
