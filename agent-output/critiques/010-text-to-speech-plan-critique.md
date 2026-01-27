# Plan Critique 010: Text-to-Speech (TTS) Service (Kokoro ONNX)

**Artifact**: agent-output/planning/010-text-to-speech-plan.md
**Related Analysis**: agent-output/analysis/010-text-to-speech-analysis.md
**Related Roadmap**: agent-output/roadmap/product-roadmap.md
**Related Architecture (master)**: agent-output/architecture/system-architecture.md
**Related Findings**: agent-output/architecture/013-tts-kokoro-onnx-architecture-findings.md (primary), agent-output/architecture/014-tts-plan-rev16-architecture-findings.md (pre-implementation gate)
**Date**: 2026-01-26
**Status**: APPROVED_WITH_CHANGES (Plan Revision 20)

This critique follows the rubric in `.github/chatmodes/planner.chatmode.md` (plans describe **WHAT/WHY**, include explicit contract gates, avoid QA/test-case content, avoid implementation “HOW”).

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-25 | User requested critique | Created critique for Plan 010 Revision 9 (Kokoro ONNX pivot), focusing on roadmap alignment, contract gates, scope, and risks. |
| 2026-01-26 | User requested updated critique | Updated critique for Plan 010 Revision 14 (“Value Validation Recovery”) to flag rubric drift and document clarity defects. |
| 2026-01-26 | User requested updated critique | Re-reviewed Plan 010 Revision 15; identified blocking rubric drift and unresolved CPU/GPU + bounds ambiguity. |
| 2026-01-26 | User requested critique (plan complete) | Re-reviewed Plan 010 Revision 17; confirms Findings 014 MUST items addressed and records remaining scope/alignment risks. |
| 2026-01-26 | User requested critique (plan complete) | Re-reviewed Plan 010 Revision 18 after UAT failure; flags value-statement verifiability and roadmap/measurability misalignment introduced by relaxed gates. |
| 2026-01-26 | User requested plan revision + critique | Re-reviewed Plan 010 Revision 19; notes improvements (speaker origin pinned, input behavior pinned, plan/QA boundary improved) and remaining blocker: “intelligible” still not observable under acceptance criteria. |
| 2026-01-26 | User requested critique (plan complete) | Re-reviewed Plan 010 Revision 20; notes added evidence artifacts (intelligibility + MinIO retention) and GPU follow-up tracking, and flags remaining clarity/scope/rubric drift items. |

## Value Statement Assessment
Plan Rev 20 keeps the value statement “intelligible spoken audio” (a constrained, more testable interpretation of the roadmap’s “spoken naturally”) and adds an explicit **human confirmation** method (5 samples) plus a named evidence artifact location.

Remaining issue: the plan now contains **conflicting statements** about whether human listening/intelligibility is deferred (see “Metric 4” vs the “Validation (Acceptance Criteria)” section). This is a clarity/DoD ambiguity that should be reconciled.

Minor clarity: consider splitting the story into 2 lines for readability (non-blocking).

## Overview
Plan 010 (Rev 20) is structurally strong in its contract sections and reflects the pre-implementation architectural gate from Findings 014 (CPU-only profile pinned, explicit input bound, latency boundary clarified).

Rev 20 strengthens closure on Analysis 010 gaps:
- Speaker context origin is pinned.
- Input-bound enforcement behavior is pinned.

Additionally, Rev 20 adds:
- A specific retention evidence artifact for MinIO lifecycle.
- A concrete intelligibility evidence artifact (human verification log).
- A follow-up tracking document for deferred GPU validation.

Remaining weaknesses are primarily (a) internal consistency of acceptance criteria vs measurement method, (b) small amounts of QA/execution detail inside the plan, and (c) roadmap wording vs v0.5.0 delivery expectations for CPU/GPU reliability.

The remaining blocker is value verifiability: the plan still asserts “intelligible audio” while deferring intelligibility validation.

The remaining changes requested below are primarily about (a) tightening a few contract decisions and (b) reconciling roadmap language around CPU/GPU stability to avoid release acceptance ambiguity.

## Architectural Alignment
**Strong alignment (✅)**
- Matches the master architecture’s TTS flow and boundary: `TextTranslatedEvent` → `AudioSynthesisEvent`.
- Matches the payload policy: dual-mode output (`audio_bytes` vs `audio_uri`) to respect Kafka caps.
- Schema governance is explicit (optional union-with-null; BACKWARD compatibility intent).
- Speaker context propagation, redaction, and retention intent are present.

**Remaining alignment risks (⚠️)**
- Findings 013 recommends an explicit internal layering invariant (orchestration / synthesizer / storage adapter). Rev 17 implies this but does not state it as an invariant.

## Roadmap Alignment
Epic 1.7’s roadmap language states Kokoro ONNX is selected to ensure reliable runtime on **both CPU and GPU** (“Thesis Requirement”). Rev 17 pins a **CPU-only image** for v0.5.0 and defers GPU support to a later deployment profile.

This is not necessarily wrong, but it creates a **definition-of-done ambiguity** unless the roadmap acceptance criteria (or a follow-up plan) explicitly captures what “reliable on both CPU and GPU” means for v0.5.0 vs later.

In Rev 20, the plan still documents CPU-focus for v0.5.0 and GPU deferral, and it adds a follow-up tracking document. This reduces the risk of “silent deferral”, but the roadmap acceptance interpretation still needs to be explicit to avoid release-gate mismatch.

## Scope Assessment
Scope is appropriate for v0.5.0 (complete the output loop with synthesis) and correctly covers contracts, service delivery, integration, and evidence collection.

Scope watch-outs:
- The “promote storage adapter to `speech-lib`” step can become a cross-service dependency surface; keep it strictly as a generic adapter (no business logic), consistent with system architecture constraints.
- The plan reads partially like an execution tracker (many `[x]` items). Non-blocking, but it increases drift risk over time.

## Clarity Assessment
Rev 17 fixes the prior corrupted Operational Constraints section and clarifies the latency boundary.

Remaining clarity nits:
- The plan includes two separate “truth sources” for value validation (Measurement Method vs Acceptance Criteria) that partially disagree; reconcile into a single, auditable DoD.
- “Output duration implicitly capped by text length” is directionally true but should be treated as an operational assumption, not a strict bound.

## Completeness Assessment
**Contract decisions (✅)**
- Speaker context representation + pass-through requirement are defined.
- Dual-mode transport and URI failure semantics are described.
- Schema evolution expectations are stated.
- Retention and log redaction are explicit.

**Remaining contract decisions to pin (⚠️)**
1) **Observability scope**: The plan lists mandatory log fields; it does not explicitly state whether any additional trace propagation beyond `correlation_id` is required (may be fine, but should be explicit).

**Acceptance criteria completeness note (⚠️)**
- Rev 18 introduces “optional” evidence artifacts and defers human listening. If the plan keeps the current value statement, it needs at least one observable acceptance criterion for intelligibility/naturalness that can be evidenced in a constrained environment.

## Risk & Technical Debt Assessment
The plan’s risk list aligns well with Analysis 010. The highest residual risks are:
- Voice mapping determinism (`speaker_id` → style vector inventory and fallback).
- Dual-mode failure coverage (URI fetch/upload error behavior must be evidenced).
- Roadmap acceptance ambiguity around CPU/GPU “reliable runtime”.

## Findings

### Critical

1) **DoD ambiguity: intelligibility evidence is both required and deferred**
- **Status**: OPEN
- **Description**: Rev 20 adds “Metric 4: Verifiable synthesis + Human Confirmation” (with an evidence artifact), but the Acceptance Criteria section still states human listening is deferred.
- **Impact**: Teams can “finish” the epic without the core value claim being evidenced, recreating the earlier UAT deadlock.
- **Recommendation**: Make a single explicit decision: either (a) intelligibility evidence is a v0.5.0 requirement (and the acceptance criteria must say so), or (b) v0.5.0 value is reduced to a purely functional claim and intelligibility becomes an explicitly deferred follow-up epic with an artifact.

2) **Rollback triggers introduce non-contract thresholds into a plan artifact**
- **Status**: OPEN
- **Description**: The rollback section uses specific numeric thresholds (e.g., P95 latency, error rate) that are not otherwise pinned as contracts and may be environment-specific.
- **Impact**: Encourages gate disputes and brittle “false failures” on constrained hardware, and conflicts with the “plans avoid tuning thresholds unless contract” rubric.
- **Recommendation**: Keep rollback guidance at a high level (“rollback on sustained elevated error rate/latency regression”), or explicitly mark these as non-binding operational defaults owned by runbooks/QA.

3) **Rubric: plan/QA boundary improved**
- **Status**: ADDRESSED
- **Description**: Rev 19 reduces plan-side testing content to “Testability Constraints”, which better matches the planning rubric.
- **Impact**: Lowers doc drift risk between plan and QA artifacts.
- **Recommendation**: Keep this section narrowly focused on testability constraints only.

### Medium

1) **Roadmap vs plan acceptance ambiguity (CPU/GPU reliability)**
- **Status**: OPEN
- **Description**: Roadmap Epic 1.7 frames CPU/GPU stability as a thesis requirement; plan Rev 17 defers GPU validation and pins a CPU-only image for v0.5.0.
- **Impact**: Release gate disputes (stakeholders may expect GPU runtime proof in v0.5.0).
- **Recommendation**: Keep the new Rev 20 follow-up tracking document, and ensure the roadmap acceptance criteria explicitly reflect what is delivered (CPU validated now; GPU evidence later) so “thesis requirement” does not silently slip.

2) **Speaker context origin not explicitly pinned**
 - **Status**: ADDRESSED
 - **Description**: Rev 19 pins the Ingress Gateway as the source of truth for speaker context.
 - **Impact**: Reduces integration ambiguity.
 - **Recommendation**: Keep the contract stable across services.

3) **Input-bound enforcement behavior is underspecified**
 - **Status**: ADDRESSED
 - **Description**: Rev 19 pins the behavior to “Reject (Soft Failure)”.
 - **Impact**: Improves determinism.
 - **Recommendation**: Ensure downstream documentation/UAT aligns with this contract.

4) **Plan contains QA/execution detail that belongs in QA/implementation artifacts**
- **Status**: OPEN
- **Description**: Items like specific env flags (`EXPECT_PAYLOAD_MODE=URI`), dataset file paths, and “establish validation tooling” read like test protocol or implementation runbook material.
- **Impact**: Rubric drift (plans should be WHAT/WHY), and higher churn risk as tests evolve.
- **Recommendation**: Keep only the required outcomes (“prove URI mode + failure semantics with evidence”) and point to QA artifacts for the procedures.

### Low

5) **Internal layering invariant not explicit (Findings 013 SHOULD)**
- **Status**: OPEN
- **Description**: Findings 013 recommends explicitly stating orchestration/synthesizer/storage layering.
- **Impact**: Low near-term, but helps prevent service boundary creep.
- **Recommendation**: Add a short statement of the layering invariant.

## Questions
1) Should “intelligible” be a v0.5.0 outcome, or should the value statement be reduced to “produces spoken audio output” for v0.5.0?
2) For v0.5.0, should the roadmap’s “reliable on CPU and GPU” be interpreted as “architecture supports both providers”, or “GPU runtime is validated and evidenced”?
3) If GPU validation is deferred, is there a named follow-up epic/plan that closes the thesis requirement with evidence?

## Risk Assessment
- **Overall**: Medium
- **Primary risk drivers**: Value-statement verifiability (quality/intelligibility deferred), acceptance ambiguity (CPU/GPU and performance evidence), and speaker context origin.

## Recommendations
- Reconcile the plan’s internal inconsistency about intelligibility evidence (required vs deferred).
- Reduce QA/execution detail in the plan and shift it to QA/implementation artifacts.
- Ensure roadmap wording and v0.5.0 acceptance explicitly match the CPU-only deliverable + GPU follow-up tracking.

## Revision History

| Revision | Date | Status | Notes |
|---------:|------|--------|-------|
| 9 | 2026-01-25 | NOT APPROVED | Initial Kokoro ONNX pivot critique (alignment + contract gates). |
| 14 | 2026-01-26 | NOT APPROVED | Value validation recovery introduced but added rubric drift and clarity defects. |
| 15 | 2026-01-26 | NOT APPROVED | Blocking rubric drift and unresolved CPU/GPU + bounds ambiguity. |
| 17 | 2026-01-26 | APPROVED_WITH_CHANGES | Findings 014 MUST items reflected; remaining alignment/contract clarifications documented. |
| 18 | 2026-01-26 | NOT APPROVED | Value/measurement gates relaxed in a way that makes the stated value outcome non-verifiable; QA strategy content reintroduced. |
| 19 | 2026-01-26 | NOT APPROVED | Value statement improved and key contracts pinned, but “intelligible” remains non-observable (validation deferred); roadmap CPU+GPU stability acceptance still ambiguous. |
| 20 | 2026-01-26 | APPROVED_WITH_CHANGES | Adds intelligibility/retention evidence artifacts and GPU follow-up tracking; remaining issues are DoD ambiguity (intelligibility required vs deferred), QA/execution detail in plan, and roadmap CPU/GPU acceptance interpretation. |
