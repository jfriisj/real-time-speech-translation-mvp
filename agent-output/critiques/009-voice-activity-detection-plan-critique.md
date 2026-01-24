# Plan Critique 009: Voice Activity Detection (VAD) Service

**Artifact**: agent-output/planning/009-voice-activity-detection-plan.md
**Related Architecture Findings**: agent-output/architecture/009-voice-activity-detection-architecture-findings.md
**Related Schemas (baseline)**: shared/schemas/avro/AudioInputEvent.avsc
**Date**: 2026-01-19
**Status**: Approved (Revision 5)

> Note: Reviewer guidance file `.github/chatmodes/planner.chatmode.md` was not found in this workspace path, so this critique follows the standard critique rubric (clarity, completeness, scope, risks, alignment) and the workspace’s existing critique patterns.

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-19 | User requested critique | Initial critique of Plan 009 for clarity, completeness, scope, risks, and alignment |
| 2026-01-19 | User requested re-critique | Reviewed revised Plan 009; marked prior blockers addressed and raised new clarity issues introduced in the edit |
| 2026-01-19 | User requested re-critique | Reviewed Revision 2 of Plan 009; confirmed all text corruption and schema path errors are resolved. Plan is APPROVED. |
| 2026-01-19 | User requested re-critique | Reviewed Revision 3 (“QA hardening”); confirmed alignment with Architecture Findings 010 and closed remaining open clarity/path issues. || 2026-01-19 | User requested re-critique | Reviewed Revision 4 (measurement methodology clarification); confirmed Finding 8 addressed with comprehensive measurement specification. |
## Value Statement Assessment
The value statement is clear and aligned with the roadmap:
- **Who**: System Architect
- **What**: Filter silence before ASR
- **Why**: Reduce compute waste and improve latency

The value is also measurable: the plan now includes a ≥ 30% reduction target for “total audio duration processed by ASR” on a sparse-speech test set. This materially improves clarity and thesis alignment.

## Overview
Plan 009 is directionally sound and aligns with the system architecture’s intent to introduce a VAD stage via a new topic and event (`SpeechSegmentEvent` on `speech.audio.speech_segment`). It also correctly calls out critical ordering and backwards-compatibility constraints.

The revised plan now includes comprehensive measurement methodology (duration computation, dataset definition, WER guardrails) that provides thesis-grade rigor for validating the efficiency claims.

**Verdict**: **APPROVED** (All findings resolved. Plan 009 is implementation-ready with clear success criteria, comprehensive QA coverage, and measurable outcomes).

## Architectural Alignment
Strong alignment with the pre-planning architecture guardrails:
- Uses the pinned topic taxonomy (`speech.audio.ingress` → `speech.audio.speech_segment`).
- Preserves the core invariants: `correlation_id`, WAV-only, minimal failure semantics.
- Includes the explicit partitioning/ordering requirement (key by `correlation_id`).

The revised plan now aligns `SpeechSegmentEvent` field naming with the established conventions (`audio_bytes`, `audio_format`, `sample_rate_hz`) and includes `segment_id`.

## Scope Assessment
Scope is mostly appropriate for Epic 1.6:
- New VAD service + wiring in compose.
- New event contract (`SpeechSegmentEvent`).
- ASR migration strategy (dual-mode) is in-scope because the roadmap AC explicitly requires ASR to consume segments.

Potential scope pressure:
- “ASR supports both inputs” is a reasonable migration approach, but the plan should explicitly define the stop condition for the epic (e.g., “VAD path is default in compose” vs “feature-flagged but available”).

## Technical Debt / Long-Term Risks
- **Schema debt**: If `SpeechSegmentEvent` launches with inconsistent field naming (`audio_payload` vs existing `audio_bytes`, `sample_rate` vs `sample_rate_hz`), it will create long-lived inconsistency and confusion across services and tooling.
- **Segment semantics debt**: If offsets/indexing are underspecified, future traceability (Epic 1.4) and transcript alignment become hard.
- **Benchmark comparability debt**: Without an explicit methodology to compare “legacy path” vs “VAD path,” you may lose thesis-grade evidence for performance claims.

## Findings

### Critical

1) **`SpeechSegmentEvent` schema definition is incomplete vs architecture requirements**
- **Status**: ADDRESSED
- **Description**: Plan 009 now includes both `segment_id` and explicit `audio_format` in the proposed schema fields.
- **Impact**: Makes traceability and debugging harder; increases risk of ambiguous segment references; makes schema evolution more likely.
- **Recommendation**: Update Plan 009 to require fields that satisfy the architecture semantics (at minimum: `segment_id`, `segment_index`, `start_ms`, `end_ms`, and either an explicit `audio_format` or a pinned invariant stated directly in the schema docstring).

2) **Schema field naming drifts from established shared contract conventions**
- **Status**: ADDRESSED
- **Description**: Plan 009 now uses `audio_bytes` and `sample_rate_hz`, matching the established naming conventions.
- **Impact**: Increases integration friction, confusion across services, and risk of inconsistent adapters.
- **Recommendation**: Align `SpeechSegmentEvent` naming to existing conventions (e.g., `audio_bytes`, `audio_format`, `sample_rate_hz`) unless there is an explicit, documented reason to diverge.

### Medium

3) **Success metrics are not defined (efficiency/latency improvements are implicit)**
- **Status**: ADDRESSED
- **Description**: Plan 009 now defines a measurable success target (≥ 30% reduction in total audio duration processed by ASR on a "sparse speech" test set) and includes it in validation.
- **Impact**: Harder to validate thesis claims and to decide if the feature “worked.”
- **Recommendation**: Add one measurable success criterion (e.g., reduction in total audio duration sent to ASR, reduction in ASR compute time, or latency percentile change).

4) **Migration/rollback strategy needs a tighter stop condition**
- **Status**: ADDRESSED
- **Description**: Plan 009 now explicitly calls out defaulting ASR to VAD mode in Compose while retaining an ENV-based fallback for regression/benchmarks.
- **Impact**: Risk of “done but not adopted” outcomes where VAD exists but is not used by default.
- **Recommendation**: Add explicit stop condition: “compose defaults ASR to consume `speech.audio.speech_segment`, but can be toggled back for regression/benchmarks.”

### Low

5) **Process improvement (PI-003) is partially reflected in the plan text**
- **Status**: PARTIALLY_ADDRESSED
- **Description**: Plan references UAT stub creation, but it is currently placed inside the ASR migration section in a way that reads like an implementation sub-note.
- **Impact**: Minor; can cause small workflow friction.
- **Recommendation**: Add an explicit UAT artifact link to the plan.

### Critical (New)

6) **Acceptance Criteria section contains corrupted/duplicated text**
- **Status**: RESOLVED
- **Description**: Acceptance criteria are now complete, non-duplicated, and aligned to the QA failure-mode checklist (Schema Registry validation, ordering, duplicate tolerance, poison/non-wav resilience, backpressure).
- **Impact**: This directly harms clarity and creates ambiguity for QA/UAT sign-off.
- **Recommendation**: Fix the acceptance criteria text so each bullet is complete, non-duplicated, and unambiguous.

### Medium (New)

7) **Schema file path references do not match repo structure**
- **Status**: RESOLVED
- **Description**: Plan now references `shared/schemas/avro/` for the `SpeechSegmentEvent` schema.
- **Impact**: Increases confusion for the implementer and risks misplaced artifacts.
- **Recommendation**: Update the plan to reference the correct schema location (`shared/schemas/avro/`) or explicitly define the intended target directory if a re-org is planned.

### Medium (New)

8) **Success metric methodology is underspecified**
- **Status**: OPEN
- **Status**: RESOLVED
- **Description**: The plan now includes a comprehensive "Success Metric Measurement Method" section specifying: (a) duration computation from WAV headers and segment offsets, (b) explicit dataset definition ("sparse speech" = ≥40% silence, N≥10 samples, ≥5min total), and (c) a WER guardrail (≤5pp degradation) with qualitative validation for at least 3 samples.
- **Impact**: Eliminates risk of inconclusive results and provides thesis-grade measurement rigor.
- **Recommendation**: ✓ ADDRESSED
## Questions
- Should `SpeechSegmentEvent` embed a nested `payload` record (matching the event envelope style of `AudioInputEvent`) to keep schema structure consistent?
- Does the epic require emitting “segment padding” (pre/post roll) as an explicit plan decision, or should that be purely runtime configuration?
- What is the minimum acceptable transcript-quality regression (if any) when using VAD, and how will it be assessed?
Low
- **Primary risk drivers**: Previously identified schema/semantic ambiguity and measurement clarity issues have been resolved. Remaining risks are standard implementation execution risks (model integration, configuration tuning)
- **Overall**: Medium
- **Primary risk drivers**: Schema mismatch / semantic ambiguity; unclear measurement/stop conditions.

## Recommendations
- ✓ Schema alignment completed (field names, required identifiers, consistent payload structure).
- ✓ Measurable success metric with clear methodology now defined.
- ✓ Migration end-state and rollback path clarified.

Plan 009 is ready for implementation. No further revisions required.

- **Revision 2 (2026-01-19)**: Marked schema naming + required fields + success metric as addressed; flagged new clarity defects and remaining stop-condition ambiguity.
- **Revision 4 (2026-01-19)**: Closed acceptance-criteria corruption and schema-path issues; added a remaining open item to clarify success-metric methodology.
- **Revision 5 (2026-01-19)**: Confirmed Finding 8 (measurement methodology) resolved. All findings closed. Plan approved for implementation
 - **Revision 2 (2026-01-19)**: Marked schema naming + required fields + success metric as addressed; flagged new clarity defects and remaining stop-condition ambiguity.
 - **Revision 4 (2026-01-19)**: Closed acceptance-criteria corruption and schema-path issues; added a remaining open item to clarify success-metric methodology.
