# Plan Critique 010: Text-to-Speech (TTS) Service (IndexTTS-2)

**Artifact**: agent-output/planning/010-text-to-speech-plan.md  
**Related Architecture**: agent-output/architecture/system-architecture.md  
**Related Findings**: agent-output/architecture/011-tts-indextts-2-architecture-findings.md, agent-output/architecture/006-tts-voice-cloning-architecture-findings.md  
**Date**: 2026-01-25  
**Status**: APPROVED (Revision 7)

> Note: This review uses the repository rubric in `.github/chatmodes/planner.chatmode.md` (WHAT/WHY only, contract decision gates, QA separation).

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-25 | User requested critique | Initial critique of Plan 010 for clarity, completeness, scope, risks, and alignment |
| 2026-01-25 | User requested re-critique | Reviewed revised Plan 010 (Revision 1) and updated findings status |
| 2026-01-25 | User requested re-critique | Reviewed revised Plan 010 (Revision 2) against planner rubric and architecture decision gates |
| 2026-01-25 | User requested re-critique | Reviewed revised Plan 010 (Revision 3) and updated findings status and decision gate coverage |
| 2026-01-25 | User requested re-critique | Reviewed revised Plan 010 (Revision 4) incorporating analysis findings (schema compatibility, consumer URI failure semantics, dataset provenance) |
| 2026-01-25 | User requested re-critique | Reviewed revised Plan 010 (Revision 5). All blockers resolved (Retention, Observability, Risks, Rollout). |
| 2026-01-25 | User requested re-critique | Reviewed revised Plan 010 (Revision 6). Added testing-infrastructure notes; flagged rubric boundary and doc hygiene issues. |

## Value Statement Assessment
The value statement is clear and aligned with the roadmap:
- **Who**: User
- **What**: Hear translated text spoken naturally
- **Why**: Hands-free consumption

The plan also attempts to be measurable (RTF, latency), which is directionally correct for thesis-grade validation.

## Overview
Plan 010 (Revision 6) remains a complete, implementation-ready specification for the TTS Service.
It successfully addresses all previous blockers:
- **Roadmap Alignment**: Targets v0.5.0 explicitly.
- **Shared Contract Boundary**: `speech-lib` is purely schema/constants; no logic.
- **Architectural Contracts**: Explicit pinned strategies for Dual-Mode Transport, Speaker Context (Inline), Pass-through, Schema Compatibility, and Failure Semantics.
- **Decision Gates**:
    - **Retention**: Pinned to 24-hour ephemeral MinIO lifecycle.
    - **Observability**: Mandatory log fields defined (`correlation_id`, `input_char_count`, `latency`, `mode`).
- **Release Management**: Includes clear Risks & Mitigations and Rollout/Rollback strategies.

Rev 6 also adds explicit testing-infrastructure notes; this is useful context, but it slightly re-introduces the plan/QA boundary risk called out in the rubric.

The plan strikes the right balance between defining rigid constraint boundaries (WHAT/WHY) and leaving implementation details (HOW) to the engineer, while satisfying the "Thesis MVP+" requirements for traceability and measurement.

## Architectural Alignment
✅ All architecture findings (011 & 006) are correctly reflected in the plan.
✅ Dual-mode transport strategy is properly constrained.
✅ MinIO failure modes are handled (Log+Drop/Fallback).
✅ Schema evolution is safe (Optional fields).

## Scope Assessment
Scope is borderline-large for a single epic because it combines:
- New service (TTS)
- New event schema (`AudioSynthesisEvent`)
- Potential new infrastructure dependency (MinIO)
- Cross-cutting speaker context propagation design

This may still be acceptable as Epic 1.7 if scoped carefully, but the plan needs a clear “stop condition” and explicit deferrals (e.g., cloning optional, fallback voice guaranteed).

## Technical Debt / Long-Term Risks
- **Shared artifact creep**: pushing MinIO client logic into `speech-lib` risks long-lived coupling and makes non-TTS services transitively dependent on storage/network behavior.
- **Schema ambiguity**: without explicit “exactly one of (`audio_bytes`, `audio_uri`)” semantics, consumers will implement inconsistent interpretations.
- **Sensitive-data handling**: speaker reference context and synthesized audio increase the risk of accidental logging/trace leakage. Retention is pinned, but “data minimization in logs” remains an execution risk.

## Findings

### Critical

1) **Roadmap ↔ Plan version mismatch (release target is ambiguous)**
- **Status**: RESOLVED
- **Description**: Addressed in Rev 1. Target release v0.5.0.

2) **Plan includes implementation-level HOW and QA-level test cases**
- **Status**: RESOLVED
- **Description**: Addressed in Rev 2/5. Implementation steps reduced to constraints.

3) **Shared contract artifact boundary likely violated (MinIO I/O inside `speech-lib`)**
- **Status**: RESOLVED
- **Description**: Addressed in Rev 1. MinIO logic removed from lib.

4) **Speaker context propagation is referenced but not specified as a contract**
- **Status**: RESOLVED
- **Description**: Addressed in Rev 2. Explicit contract added.

### Medium

5) **`AudioSynthesisEvent` schema requirements are incomplete/underspecified**
- **Status**: RESOLVED
- **Description**: Addressed in Rev 4. Pinned "exactly-one-of" payload and optionality.

6) **Metrics are directionally good but lack a dataset definition and guardrails for “naturalness”**
- **Status**: RESOLVED
- **Description**: Addressed in Rev 4/5. Dataset provenance and quality checks defined.
- **Impact**: Results may be non-reproducible or unconvincing for thesis claims.
- **Recommendation**: Define a deterministic phrase set (source, language, lengths) and a basic audio-quality acceptance method (even qualitative + minimum sample count).

7) **Object store failure semantics for `audio_uri` are not pinned (Architecture Findings 011.F)**
- **Status**: RESOLVED
- **Description**: The plan now pins producer-side behavior on upload failure (log + fallback; no crash-loop) and consumer-side behavior on retrieval failure (log with `correlation_id`, treat as playback failure/skip, no infinite retries).
- **Impact**: High risk of crash-loops, inconsistent downstream behavior, and difficult debugging.
- **Recommendation**: Add a contract-level failure policy for URI retrieval failures consistent with Findings 011 (“fallback voice; do not crash-loop”) and minimal observability signals.

8) **Schema evolution / backward compatibility expectations are not pinned (Decision Gate 4.1)**
- **Status**: RESOLVED
- **Description**: The plan explicitly pins backward compatibility expectations (optional fields via union-with-null and Schema Registry backward/backward-transitive compatibility).
- **Impact**: High risk of breaking existing consumers, subject incompatibilities, and confusing “it works locally but not in CI/demo” failures.
- **Recommendation**: Add a contract-level statement of schema evolution constraints (e.g., optional fields only; no breaking changes; compatibility mode expectation) and identify affected producers/consumers.

### Low

9) **Markdown formatting issue: plan is wrapped in an extra code fence**
- **Status**: RESOLVED
- **Description**: The revised plan is no longer wrapped in an extra outer code fence.
- **Impact**: Minor readability/tooling friction.
- **Recommendation**: Remove the outer code fences.

10) **Object-store retention/TTL for synthesized audio is not specified (Decision Gate 4.3)**
- **Status**: RESOLVED
- **Description**: Addressed in Rev 5. Retention is pinned to a 24-hour MinIO bucket lifecycle rule (expiration).
- **Impact**: Previously risked storage growth and privacy ambiguity; now bounded.
- **Recommendation**: None.

11) **Observability contract is incomplete (Decision Gate 4.4)**
- **Status**: RESOLVED
- **Description**: Addressed in Rev 5. Mandatory log fields and metrics defined.

12) **Testing strategy content reintroduced into the plan (rubric boundary risk)**
- **Status**: OPEN (Non-blocking)
- **Description**: Rev 6 adds a dedicated **Testing Strategy** section (unit + integration) including tooling and scenario lists. Repo rubric discourages embedding QA strategy/test-case content in plans; plans should focus on WHAT/WHY and contract gates, with QA details living in `agent-output/qa/`.
- **Impact**: Encourages plan drift into “how-to test” and creates duplication/ownership friction with QA artifacts.
- **Recommendation**: Keep only **Testing Infrastructure Requirements** in the plan (frameworks/plugins, minimal config/fixtures constraints, and isolation requirements). Move scenario lists and integration-test workflows to the QA document.

13) **Plan document hygiene: corrupted/duplicated section near the end**
- **Status**: OPEN (Non-blocking)
- **Description**: Rev 6 contains a malformed section break around Step 3 (an inline "Risks & Mitigations" block) and an extra stray header fragment ("##  - **Requirement**") that reads like accidental paste/merge.
- **Impact**: Reduces clarity for implementers, risks misinterpretation of the work packages, and makes the plan harder to treat as a stable “source of truth.”
- **Recommendation**: Clean up the section boundaries and ensure Steps/Risks/Rollout are distinct, correctly headed, and non-duplicative.

## Risk Assessment
- **Overall**: Low-Medium
- **Remaining Risks**:
    - Latency of synthesis with MinIO uploads (Mitigated by "Dual-Mode with Fallback").
    - Schema compatibility in practice (Mitigated by "Optional fields" contract).

## Recommendation
**APPROVE (with notes)**. Before handoff, clean up the minor doc-hygiene issues and consider moving the scenario-level testing content into the QA artifact to stay within the repo’s plan rubric.