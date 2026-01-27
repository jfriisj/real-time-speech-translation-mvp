# Plan Critique: 010-text-to-speech (TTS)

**Artifact**: agent-output/planning/010-text-to-speech-plan.md
**Related Analysis**: agent-output/analysis/010-text-to-speech-plan-analysis.md, agent-output/analysis/011-claim-check-unknowns-analysis.md
**Related Architecture Findings**: agent-output/architecture/019-text-to-speech-plan-architecture-findings.md, agent-output/architecture/020-claim-check-scope-shift-architecture-findings.md
**Date**: 2026-01-27
**Status**: APPROVED (Revision 8)

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
| 2026-01-27 | User → Critic | Critique after plan update | Reviewed Plan 010 Rev 31 after incorporating Analysis 011 / Findings 020 (Claim Check scope shift). Prior Milestones naming defects appear resolved, but new blocking text corruption/regressions exist in Schema Contract, M4 deliverables, and Verification & Acceptance. |
| 2026-01-27 | User → Critic | Critique after plan repair | Reviewed Plan 010 Rev 31 after text repairs; contract sections are clean and unambiguous. All prior blockers resolved. |

## Value Statement Assessment
- **Present and well-formed**: “As a User, I want…, So that…” is clear.
- **Business objective is understandable** (hands-free consumption) and matches the epic intent.

## Overview
Plan 010 (Rev 31) is **architecturally aligned** with the Claim Check scope shift (v0.5.0 pilot for TTS; v0.6.0 platform rollout). Prior text corruption in contract-defining sections has been repaired, and no blocking issues remain.

## Roadmap Alignment
- **Aligned**: Target release `v0.5.0` and Epic 1.7 user story match the roadmap wording.
- **Minor documentation drift risk**: the roadmap “Status Notes” mention an older plan revision; this does not block the plan but can confuse cross-team readers.

## Architectural Alignment
- **Mostly aligned**: Plan references Findings 019 and now also reflects Findings 020 (early Claim Check enablement for TTS).
- **Speaker Context**: Correctly set to "Pass-through" to support future Voice Cloning without contract breakage.
- **Claim Check**: Correctly implements strict inline (<1.25 MiB) vs external (>1.25 MiB) handling.
- **Security**: "Don't log presigned URLs" constraint is present.
- **Microservices**: Decoupling logic (SynthesizerFactory) from implementation (Kokoro ONNX) is preserved.

## Completeness (Contract Decision Gates)
- **Message/schema contract**: Present (producer/consumer, evolution rules, Registry `BACKWARD`).
- **Speaker context propagation**: Present (explicit pass-through requirement).
- **Data retention & privacy**: Present (24h default target + configurable; “do not log presigned URLs”).
- **Observability**: Present (trace propagation + required log fields). Consider adding minimal metrics as a future refinement (non-blocking).
 - **Observability**: Present (trace propagation + required log fields, including latency/RTF). Metrics are explicitly optional for v0.5.0, which removes ambiguity.

## Scope Assessment
- Scope is properly constrained to the TTS service implementation.
- Integration points with Gateway (for URI presigning) and MinIO (for object storage) are clearly defined.
- Future dependencies (Voice Cloning) are enabled by the contract but excluded from current processing scope, which is appropriate for MVP.

## Clarity Notes
- The plan is generally clear and structured.
- The “Verification & Acceptance” section still includes concrete test actions; consider moving procedural steps to QA artifacts while keeping plan-level outcomes.

## Technical Debt Risks
- **Low**: The updated plan mitigates the major debt risk (contract divergence) by strictly adhering to the "Backward Compatible" and "Pass-through" strategies.

## Risks & Rollback Thinking
- Risks are plausible and include mitigations (model download/caching; tokenization complexity).
- Rollback is now unambiguous and consistent with the strategic constraint: rollback is via version revert / feature disable, and the mock engine is explicitly demo/test-only.

## Findings

### Critical (Blocking)

#### C1 — Speaker Context Propagation Misaligned with Architecture
**Status**: RESOLVED

**Resolution**: Plan Rev 26 now explicitly states: "The service receives optional `speaker_reference_bytes` ... and propagates it to `AudioSynthesisEvent`. (Even if Kokoro does not use it)." This aligns with the "Pass-through" architecture requirement.

#### C2 — QA Thresholds Missing
**Status**: RESOLVED

**Resolution**: Plan Rev 26 includes explicit performance verification intent (RTF measured/recorded) without over-specifying plan-level benchmark protocols.

#### C3 — Retention Default Conflicts with Architecture Guardrail
**Status**: RESOLVED

**Resolution**: Plan Rev 26 updates retention to "24h default (configurable)", aligning with the architecture guardrail.

#### C4 — Schema Compatibility Conflicts with Registry Policy
**Status**: RESOLVED

**Resolution**: Plan Rev 26 specifies "Schema Compatibility: BACKWARD", matching the platform Registry policy.

#### C5 — Milestones section contains corrupted/duplicated text
**Status**: RESOLVED

**Resolution**: Plan 010 Rev 31 Milestones are cleanly structured (M1–M5) without the prior stray header/corrupted duplication.

#### C6 — M1 deliverable naming conflicts with the contract source-of-truth
**Status**: RESOLVED

**Resolution**: Plan 010 Rev 31 M1 deliverables correctly distinguish:
- Schema artifact path: `shared/schemas/avro/AudioSynthesisEvent.avsc`
- Schema Registry subject: `speech.tts.audio-value` (TopicNameStrategy)

#### C7 — Schema Contract section is corrupted (source-of-truth and `audio_uri` semantics)
**Status**: RESOLVED

**Resolution**: Schema Contract now cleanly identifies `shared/schemas/avro/AudioSynthesisEvent.avsc` as source-of-truth and defines `audio_uri` as an internal object key (Gateway presigns).

#### C8 — M4 deliverables are corrupted (Claim Check fallback and observability enforcement)
**Status**: RESOLVED

**Resolution**: M4 now lists three explicit Claim Check cases (inline, URI/key, log-and-drop).

#### C9 — Verification & Acceptance section is corrupted/duplicated
**Status**: RESOLVED

**Resolution**: Verification & Acceptance is clean and non-duplicated.

### Major (Important)

#### M5 — URI Ownership/Expiry Strategy Fragile
**Status**: RESOLVED

**Resolution**: Plan Rev 26 adopts the "Internal Key (Preferred)" strategy where the Gateway is responsible for presigning at read-time, addressing the fragility of long-lived presigned URLs.

#### M6 — “Exactly-one-of” payload invariant not explicit
**Status**: RESOLVED

**Resolution**: Plan Rev 30 explicitly states the XOR invariant in the Schema Contract.

#### M7 — Field naming drift risks contract confusion
**Status**: RESOLVED

**Resolution**: Plan Rev 31 uses `sample_rate_hz`, matching the canonical schema naming convention.

**Impact**: Small naming drift is a common integration failure mode (especially across services and generated models).

**Recommendation**: In M1 deliverables, align field names to the canonical schema file names/fields (or explicitly link to the schema file as source of truth).

## Recommendations
- **Proceed to implementation**: Blocking defects are resolved; implementation can start.
- **Reduce plan/QA coupling**: Keep acceptance criteria as observable outcomes; move step-by-step test procedure (script paths, exact phrase lists) into QA artifacts unless they are explicitly contract-level requirements.
- **Gateway alignment**: Keep the “internal key + gateway presigning” rule explicit and consistent across Schema Contract + Retention sections.

## Questions (Non-Blocking)
1. Should the plan remove the “QA Script path” requirement and instead reference a QA artifact location, to match the repo plan rubric (plans are WHAT/WHY, QA docs are HOW)?
2. Should M1 list fields at all (risk of drift), or should it only point to `shared/schemas/avro/AudioSynthesisEvent.avsc` as the single source-of-truth?

