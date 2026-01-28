# Plan Critique: 010-text-to-speech (TTS)

**Artifact**: agent-output/planning/010-text-to-speech-plan.md
**Related Analysis**: agent-output/analysis/010-text-to-speech-plan-analysis.md, agent-output/analysis/012-text-to-speech-claim-check-analysis.md, agent-output/analysis/013-minio-default-credentials-analysis.md
**Related Architecture Findings**: agent-output/architecture/019-text-to-speech-plan-architecture-findings.md, agent-output/architecture/020-claim-check-scope-shift-architecture-findings.md, agent-output/architecture/021-text-to-speech-plan-rev33-architecture-findings.md
**Related Security Review**: agent-output/security/010-text-to-speech-security-pre-implementation.md
**Date**: 2026-01-27
**Status**: APPROVED (Revision 11)

## Changelog

| Date | Handoff | Request | Summary |
|------|---------|---------|---------|
| 2026-01-27 | User → Critic | Critique for clarity/completeness/scope/risks/alignment | Initial critique created. |
| 2026-01-27 | User → Critic | Re-critique after plan revision | Reviewed Plan 010 Rev 24; contract gates mostly resolved; remaining scope/QA/governance items noted. |
| 2026-01-27 | User → Critic | Re-critique after plan revision | Reviewed Plan 010 Rev 25; addressed QA threshold concern and clarified `audio_uri` consumer + expiry behavior; governance note remains. |
| 2026-01-27 | User → Critic | Re-critique after architecture re-review | Reviewed Plan 010 Rev 25 against Findings 017; identified architectural misalignment on speaker context, schema compatibility wording, retention defaults, and `audio_uri` ownership. |
| 2026-01-27 | User → Critic | Re-critique after plan revision | Reviewed Plan 010 Rev 26; Verified alignment with Architecture Findings 017. All blocking issues resolved. |
| 2026-01-27 | User → Critic | Critique for clarity/completeness/scope/risks/alignment | Reviewed Plan 010 Rev 26 against the planner rubric; corrected outdated critique assertions; captured remaining non-blocking risks/questions. |
| 2026-01-27 | User → Critic | Critique for clarity/completeness/scope/risks/alignment | Reviewed Plan 010 Rev 27; confirmed prior open questions resolved (DLQ, rollback constraint, metrics/logging). Added remaining non-blocking clarity gaps. |
| 2026-01-27 | User → Critic | Critique after architecture gate | Reviewed Plan 010 Rev 30 against Architecture Findings 019 and the planner rubric; found core architectural alignment but identified blocking plan text defects (Milestones corruption, schema artifact naming) and minor scope hygiene issues. |
| 2026-01-27 | User → Critic | Critique after plan update | Reviewed Plan 010 Rev 31 after incorporating Findings 020 (Claim Check scope shift). Prior Milestones naming defects appear resolved, but new blocking text corruption/regressions exist in Schema Contract, M4 deliverables, and Verification & Acceptance. |
| 2026-01-27 | User → Critic | Critique after plan repair | Reviewed Plan 010 Rev 31 after text repairs; contract sections are clean and unambiguous. All prior blockers resolved. |
| 2026-01-27 | User → Critic | Critique after security gate update | Reviewed current Plan 010 (header says Rev 34) after adding explicit security constraints; flagged remaining clarity and security-alignment gaps that should be resolved before implementation/release. |
| 2026-01-27 | User → Critic | Re-critique after critique remediation | Reviewed Plan 010 Rev 35; verified the security TTL ambiguity, revision metadata drift, integrity narrative, and key-collision decision have been addressed. |
| 2026-01-27 | User → Critic | Re-critique after security investigation | Reviewed Plan 010 Rev 35 in light of Analysis 013 (MinIO default credentials + compose drift). Plan remains sound; additional release-gating alignment checks recommended. |

## Value Statement Assessment
- **Present and well-formed**: “As a User, I want…, So that…” is clear.
- **Business objective is understandable** (hands-free consumption) and matches the epic intent.

## Overview
Plan 010 is **strongly aligned** with Epic 1.7 in the roadmap (Kokoro ONNX + Claim Check enablement for large TTS outputs) and matches the architecture’s key boundaries (XOR Claim Check semantics; SR governance; edge presigning responsibility).

Security constraints are explicitly captured (secrets hygiene, supply-chain pinning, edge URL policy, logging minimization, integrity metadata) without undermining the edge boundary or the Claim Check semantics.

## Roadmap Alignment
- **Aligned**: Target release `v0.5.0` and Epic 1.7 user story match the roadmap wording.
- **Minor documentation drift risk**: the roadmap “Status Notes” reference older Plan 010 revision numbers, which can confuse cross-team readers during release governance.

## Architectural Alignment
- **Mostly aligned**: Plan references Findings 019 and now also reflects Findings 020 (early Claim Check enablement for TTS).
- **Speaker Context**: Correctly set to "Pass-through" to support future Voice Cloning without contract breakage.
- **Claim Check**: Correctly implements strict inline (<1.25 MiB) vs external (>1.25 MiB) handling.
- **Security boundary**: "Don’t emit presigned URLs from TTS" + "don’t log presigned URLs" constraints are present.
- **Microservices**: Decoupling logic (SynthesizerFactory) from implementation (Kokoro ONNX) is preserved.

## Completeness (Contract Decision Gates)
- **Message/schema contract**: Present (producer/consumer, evolution rules, Registry `BACKWARD`).
- **Speaker context propagation**: Present (explicit pass-through requirement).
- **Data retention & privacy**: Present (24h default target + configurable; “do not log presigned URLs”).
- **Observability**: Present (trace propagation + required log fields, including latency/RTF). Metrics are explicitly optional for v0.5.0, which removes ambiguity.
- **Security constraints**: Present as a dedicated “Security Controls (Pre-Implementation Gate)” section and consistent with the configuration table and edge contract.

## Scope Assessment
- Scope is properly constrained to the TTS service implementation.
- Integration points with Gateway (for URI presigning) and MinIO (for object storage) are clearly defined.
- Future dependencies (Voice Cloning) are enabled by the contract but excluded from current processing scope, which is appropriate for MVP.

## Clarity Notes
- The plan is generally clear and structured.
- The “Verification & Acceptance” section includes some procedural verification steps (specific scripts/paths). This is not necessarily wrong, but it is close to the repo rubric’s “plans are WHAT/WHY, QA is HOW”. Consider reframing to outcomes + pointers to QA artifacts.

## Technical Debt Risks
- **Low**: The updated plan mitigates the major debt risk (contract divergence) by strictly adhering to the "Backward Compatible" and "Pass-through" strategies.

## Risks & Rollback Thinking
- Risks are plausible and include mitigations (model download/caching; tokenization complexity).
- Rollback is now unambiguous and consistent with the strategic constraint: rollback is via version revert / feature disable, and the mock engine is explicitly demo/test-only.

## Findings

### Critical (Blocking)

#### C1 — Security gate introduces a TTL/ownership ambiguity
**Status**: RESOLVED

**Description**: Previously, the plan mixed “short-lived client presigns” with a 24h presign setting in a way that could be read as endorsing long-lived presigned URLs.

**Resolution**: Plan Rev 35 explicitly distinguishes:
- Gateway client policy (short TTL; never persisted/logged)
- `MINIO_PRESIGN_EXPIRY_SECONDS` as **internal/testing-only** with a note that Gateway applies a separate, shorter client-facing TTL.

**Impact**: Removes ambiguity that could lead to long-lived URL exposure.

### Medium

#### M1 — Plan revision metadata drift
**Status**: RESOLVED

**Description**: Previously, the plan revision header did not reflect post-security edits.

**Impact**: Auditability and cross-document traceability suffer (roadmap, architecture findings, and security review all cite specific revs).

**Resolution**: Plan header is now Rev 35 and includes a security reference.

#### M2 — Integrity metadata is introduced but not fully integrated into the contract narrative
**Status**: RESOLVED

**Description**: Previously, integrity metadata was introduced in milestones without consumer guidance.

**Impact**: Implementers may treat integrity fields as “nice-to-have” and omit downstream validation, reducing their value and leaving a false sense of safety.

**Resolution**: Schema Contract now includes integrity metadata guidance and non-fatal handling expectations.

#### M3 — Key collision risk remains a known integrity issue
**Status**: RESOLVED

**Description**: The plan’s canonical key format `tts/{correlation_id}.wav` is stable and simple, but collision-prone under replay/retry scenarios.

**Impact**: Potential overwrites or confusing “wrong audio served for the right correlation_id”, undermining trust and traceability.

**Resolution**: Plan Rev 35 explicitly accepts overwrite (“Last Write Wins”) as v0.5.0 MVP debt with rationale.

### Low

#### L1 — Plan/QA coupling is borderline
**Status**: ADDRESSED

**Description**: The plan still references specific scripts/paths as evidence pointers in a few places.

**Impact**: Minor; primarily maintainability and governance drift.

**Recommendation**: Keep the current light-touch approach (outcome-first, scripts as examples). If this becomes a recurring maintenance pain, migrate procedural steps to QA artifacts.

## Recommendations
- **Proceed to implementation/release gating**: Plan 010 Rev 35 is clear, complete on contract decisions, and aligned with roadmap/architecture/security.
- **Track MVP debt explicitly**: The accepted overwrite behavior for `tts/{correlation_id}.wav` should be carried as a known debt item into the Epic 1.8 rollout.

## Additional Risks (Non-Blocking, from Analysis 013)

### R1 — Default MinIO credentials are easy to cargo-cult beyond localhost
**Status**: OPEN

**Description**: The plan’s security controls correctly state MinIO defaults must not be used outside localhost. Analysis 013 confirms the repo’s local compose uses `minioadmin/minioadmin` in both MinIO and the TTS service, which is fine for local dev but risky if copied to any shared/staging environment.

**Impact**: Confidentiality/integrity risk (audio objects can be read/overwritten/deleted with well-known credentials).

**Recommendation**: Keep plan approved, but treat this as a release-gating checklist item: document a required non-local secrets injection mechanism and ensure any non-local compose/deployment config explicitly overrides defaults.

### R2 — Infrastructure config drift against plan constraints
**Status**: OPEN

**Description**: The plan requires v0.5.0 to use `TTS_AUDIO_URI_MODE=internal` and requires container pinning (no `:latest`). The current `docker-compose.yml` still uses `minio/minio:latest` / `minio/mc:latest` and sets `TTS_AUDIO_URI_MODE` default to `presigned`.

**Impact**: Confusing behavior for QA/UAT (URI semantics differ from the contract) and avoidable supply-chain drift.

**Recommendation**: This is not a plan defect, but it is an implementation/release alignment risk. Ensure the implementation report and QA/UAT evidence explicitly confirm the runtime config matches the plan constraints.

## Questions (Non-Blocking)
1. Do we want to explicitly state a default posture for `text_snippet` (e.g., schema may carry it, but logs do not emit it by default) to align privacy guidance end-to-end?

