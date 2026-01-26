# Plan Critique 010: Text-to-Speech (TTS) Service (Kokoro ONNX)

**Artifact**: agent-output/planning/010-text-to-speech-plan.md
**Related Analysis**: agent-output/analysis/010-text-to-speech-analysis.md
**Related Roadmap**: agent-output/roadmap/product-roadmap.md
**Related Architecture (master)**: agent-output/architecture/system-architecture.md
**Related Findings**: agent-output/architecture/013-tts-kokoro-onnx-architecture-findings.md (primary), agent-output/architecture/014-tts-plan-rev16-architecture-findings.md (pre-implementation gate)
**Date**: 2026-01-26
**Status**: APPROVED_WITH_CHANGES (Plan Revision 17)

This critique follows the rubric in `.github/chatmodes/planner.chatmode.md` (plans describe **WHAT/WHY**, include explicit contract gates, avoid QA/test-case content, avoid implementation “HOW”).

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-25 | User requested critique | Created critique for Plan 010 Revision 9 (Kokoro ONNX pivot), focusing on roadmap alignment, contract gates, scope, and risks. |
| 2026-01-26 | User requested updated critique | Updated critique for Plan 010 Revision 14 (“Value Validation Recovery”) to flag rubric drift and document clarity defects. |
| 2026-01-26 | User requested updated critique | Re-reviewed Plan 010 Revision 15; identified blocking rubric drift and unresolved CPU/GPU + bounds ambiguity. |
| 2026-01-26 | User requested critique (plan complete) | Re-reviewed Plan 010 Revision 17; confirms Findings 014 MUST items addressed and records remaining scope/alignment risks. |

## Value Statement Assessment
The value statement matches Epic 1.7 and is user-centric (“hear translated text spoken naturally … hands-free”).

Minor clarity: consider splitting the story into 2 lines for readability (non-blocking).

## Overview
Plan 010 (Rev 17) is materially clearer than Rev 15/16 and now reflects the pre-implementation architectural gate from Findings 014:
- CPU/GPU delivery strategy is pinned for v0.5.0.
- An explicit input bound exists.
- Latency measurement boundary is defined as an end-to-end service metric.

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

## Scope Assessment
Scope is appropriate for v0.5.0 (complete the output loop with synthesis) and correctly covers contracts, service delivery, integration, and evidence collection.

Scope watch-outs:
- The “promote storage adapter to `speech-lib`” step can become a cross-service dependency surface; keep it strictly as a generic adapter (no business logic), consistent with system architecture constraints.
- The plan reads partially like an execution tracker (many `[x]` items). Non-blocking, but it increases drift risk over time.

## Clarity Assessment
Rev 17 fixes the prior corrupted Operational Constraints section and clarifies the latency boundary.

Remaining clarity nits:
- Input bound behavior says “truncated or rejected (soft failure)”; choose one as the contract behavior to avoid inconsistent implementations.
- “Output duration implicitly capped by text length” is directionally true but should be treated as an operational assumption, not a strict bound.

## Completeness Assessment
**Contract decisions (✅)**
- Speaker context representation + pass-through requirement are defined.
- Dual-mode transport and URI failure semantics are described.
- Schema evolution expectations are stated.
- Retention and log redaction are explicit.

**Remaining contract decisions to pin (⚠️)**
1) **Speaker context origin**: The plan requires pass-through, but does not explicitly state which component is the source of truth for `speaker_id` / `speaker_reference_bytes` (e.g., Gateway vs client). This is a contract gate in the rubric when speaker context is in scope.
2) **Observability scope**: The plan lists mandatory log fields; it does not explicitly state whether any additional trace propagation beyond `correlation_id` is required (may be fine, but should be explicit).

## Risk & Technical Debt Assessment
The plan’s risk list aligns well with Analysis 010. The highest residual risks are:
- Voice mapping determinism (`speaker_id` → style vector inventory and fallback).
- Dual-mode failure coverage (URI fetch/upload error behavior must be evidenced).
- Roadmap acceptance ambiguity around CPU/GPU “reliable runtime”.

## Findings

### Medium

1) **Roadmap vs plan acceptance ambiguity (CPU/GPU reliability)**
- **Status**: OPEN
- **Description**: Roadmap Epic 1.7 frames CPU/GPU stability as a thesis requirement; plan Rev 17 defers GPU validation and pins a CPU-only image for v0.5.0.
- **Impact**: Release gate disputes (stakeholders may expect GPU runtime proof in v0.5.0).
- **Recommendation**: Explicitly reconcile “v0.5.0 acceptance” with the roadmap wording (either by clarifying the roadmap acceptance criteria or by adding a follow-up epic/plan reference for GPU profile validation).

2) **Speaker context origin not explicitly pinned**
- **Status**: OPEN
- **Description**: Pass-through requirement exists, but the upstream “owner” of `speaker_id` / `speaker_reference_bytes` is not explicitly stated.
- **Impact**: Integration ambiguity; multiple producers could set conflicting values.
- **Recommendation**: Pin the origin-of-truth (even if it is “Gateway sets it; if absent, treat as null”).

3) **Input-bound enforcement behavior is underspecified**
- **Status**: OPEN
- **Description**: “Truncate or reject” leaves two incompatible behaviors.
- **Impact**: Makes latency/payload bounds non-reproducible and complicates downstream UX.
- **Recommendation**: Choose one behavior as the contract; treat the other as a later enhancement.

4) **Plan includes some implementation-adjacent guidance**
- **Status**: OPEN
- **Description**: A few items (e.g., “downgrade Python if necessary”, some testing strategy specifics) still read like execution guidance rather than outcomes.
- **Impact**: Mild rubric drift; increases maintenance burden in the plan artifact.
- **Recommendation**: Keep the plan focused on outcomes/constraints; move environment/tooling contingencies to implementation notes.

### Low

5) **Internal layering invariant not explicit (Findings 013 SHOULD)**
- **Status**: OPEN
- **Description**: Findings 013 recommends explicitly stating orchestration/synthesizer/storage layering.
- **Impact**: Low near-term, but helps prevent service boundary creep.
- **Recommendation**: Add a short statement of the layering invariant.

## Questions
1) For v0.5.0, should the roadmap’s “reliable on CPU and GPU” be interpreted as “architecture supports both providers”, or “GPU runtime is validated and evidenced”?
2) Which component is the single source of truth for `speaker_id` and `speaker_reference_bytes`?
3) For the 500-character bound, is the desired behavior “reject with logged warning” or “truncate and proceed”?

## Risk Assessment
- **Overall**: Low-to-Medium
- **Primary risk driver**: Acceptance ambiguity (CPU/GPU) and speaker context origin.

## Recommendations
- Treat Rev 17 as acceptable to proceed, but close the remaining contract pinning items to avoid integration disputes.
- Reconcile roadmap language vs plan delivery regarding CPU/GPU stability to prevent a release gate mismatch.

## Revision History

| Revision | Date | Status | Notes |
|---------:|------|--------|-------|
| 9 | 2026-01-25 | NOT APPROVED | Initial Kokoro ONNX pivot critique (alignment + contract gates). |
| 14 | 2026-01-26 | NOT APPROVED | Value validation recovery introduced but added rubric drift and clarity defects. |
| 15 | 2026-01-26 | NOT APPROVED | Blocking rubric drift and unresolved CPU/GPU + bounds ambiguity. |
| 17 | 2026-01-26 | APPROVED_WITH_CHANGES | Findings 014 MUST items reflected; remaining alignment/contract clarifications documented. |
