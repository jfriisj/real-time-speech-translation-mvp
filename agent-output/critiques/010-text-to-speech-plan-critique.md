# Plan Critique 010: Text-to-Speech (TTS) Service (Kokoro ONNX)

**Artifact**: agent-output/planning/010-text-to-speech-plan.md
**Related Analysis**: agent-output/analysis/011-onnx-tts-model-selection-analysis.md, agent-output/analysis/008-tts-voice-context-unknowns-analysis.md
**Related Architecture (master)**: agent-output/architecture/system-architecture.md
**Related Findings**: agent-output/architecture/013-tts-kokoro-onnx-architecture-findings.md
**Date**: 2026-01-25
**Status**: APPROVED_WITH_CHANGES (Revision 9)

This critique follows the rubric in `.github/chatmodes/planner.chatmode.md` (plans describe **WHAT/WHY**, include explicit contract gates, avoid QA/test-case content, avoid implementation “HOW”).

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-25 | User requested critique | Updated critique for Plan 010 Revision 9 (Kokoro ONNX pivot), including roadmap alignment, contract gate coverage, and scope/risks. |

## Value Statement Assessment
The value statement is aligned with Epic 1.7 wording (“hands-free consumption”) and is user-centric.

Clarity note: the statement contains minor formatting drift (capitalized “So that …” and punctuation), but the intent is unambiguous.

## Overview
Plan 010 (Rev 9) is largely complete and aligned with the Kokoro ONNX pivot:
- The **core outcomes** are clear (speak translated text; close the speech-to-speech loop).
- The **architectural contracts** are explicitly stated (speaker context pass-through, dual-mode output transport, schema evolution, retention/TTL, observability fields).
- The plan includes measurable success metrics (RTF and latency) consistent with thesis validation goals.

However, there are several alignment and clarity gaps that reduce the plan’s usefulness as a stable “source of truth” for Epic 1.7 outcomes.

## Architectural Alignment
**Strong alignment (✅)**
- Matches Findings 013 directionally: event-driven boundary, dual-mode payload strategy, schema optionality, and pluggable synthesizer requirement.

**Gaps (⚠️)**
- The plan header still cites an older findings reference (Findings 011) rather than the active Kokoro findings (Findings 013). This creates audit confusion.
- Findings 013 requires explicit CPU vs GPU packaging/deployment profiles; the plan gestures at provider selection but does not fully “pin” the delivery profile.

## Scope Assessment
The scope is coherent for Epic 1.7 *if* it stays tightly constrained to “produce `AudioSynthesisEvent` from `TextTranslatedEvent`” with a stable backend.

Risk of scope creep remains because the plan blends:
- outcome contracts (good),
- execution tracking (`[x]` checklists), and
- QA/testing strategy details.

This mixture makes it harder to tell what is required for the epic vs what is implementation work-in-progress.

## Technical Debt / Long-Term Risks
- **Contract drift**: If provider selection, speed/duration control, and audio payload limits aren’t explicitly pinned as outcomes, implementations may vary and make benchmarking / demo reproducibility weaker.
- **Privacy leakage risk**: speaker reference bytes are treated as sensitive, but the plan does not explicitly prohibit logging them or including them in error payloads.
- **Operational ambiguity**: CPU/GPU expectations are part of the epic’s “stable runtime” value; ambiguity here will become a recurring deployment/debug tax.

## Findings

### Critical

1) **Architecture reference drift in plan header**
- **Status**: OPEN
- **Description**: Plan 010 (Rev 9) header still references Findings 011, but the controlling decision artifact for the Kokoro ONNX pivot is Findings 013.
- **Impact**: Confuses readers about which constraints are authoritative; weakens traceability for thesis/release documentation.
- **Recommendation**: Update the plan header references to point to Findings 013 as the active findings for this epic.

2) **Epic acceptance criteria are not fully mapped into plan deliverables**
- **Status**: OPEN
- **Description**: The roadmap’s Epic 1.7 acceptance criteria include “Basic duration/speed control implemented.” Plan 010 mentions measurement and payload strategy but does not clearly define what “duration/speed control” means at the contract level (e.g., fixed default speed only, optional field, or explicitly out-of-scope).
- **Impact**: Implementation teams can meet the plan while still failing the epic outcome; also risks adding late, ad-hoc changes to schemas/APIs.
- **Recommendation**: Add an explicit “Epic AC mapping” section (one-to-one bullets) and clarify what minimal duration/speed control is considered “done” for v0.5.0.

3) **CPU/GPU stability outcome is under-specified (provider + packaging decision gate)**
- **Status**: OPEN
- **Description**: Findings 013 requires explicit provider selection and discourages “try both at runtime” ambiguity. The plan mentions an env-var provider toggle, but does not pin whether v0.5.0 ships (a) CPU-only image, (b) GPU image, or (c) two distinct deployment profiles.
- **Impact**: You can’t validate the “stable CPU/GPU runtime” business value without a pinned deployment profile; increases risk of runtime failures during demo/benchmarking.
- **Recommendation**: Explicitly state the supported deployment profile(s) for v0.5.0 and how that satisfies the epic’s stability claim.

### Medium

4) **Plan includes QA/test strategy content (rubric violation)**
- **Status**: OPEN
- **Description**: The plan contains a dedicated Testing Strategy section with tooling, coverage targets, and integration testing guidance. Repo rubric says QA details should live in `agent-output/qa/` and plans should stay at WHAT/WHY + contract gates.
- **Impact**: Duplicates QA ownership, increases drift risk, and weakens the plan as a stable contract artifact.
- **Recommendation**: Keep only minimal “testing infrastructure constraints” (e.g., mocks required, external I/O isolation) and move the rest to the QA doc.

5) **Execution tracking (`[x]` checklists) reduces clarity of intended scope**
- **Status**: OPEN
- **Description**: Plan steps are marked `[x]` “complete,” while epic acceptance criteria remain unchecked. This makes it unclear whether the epic is functionally complete or only scaffolded.
- **Impact**: Stakeholders can misread progress; future revisions become harder to review because the plan blends planning and status reporting.
- **Recommendation**: Split “Plan” (stable scope/contract) from “Implementation tracker” (progress checklist) or move the `[x]` tracking to an implementation/QA artifact.

6) **Privacy/retention contract is directionally good but missing an explicit logging redaction rule**
- **Status**: OPEN
- **Description**: The plan states speaker reference clips must not be persisted beyond session scope, but does not explicitly state “must not be logged” for speaker reference bytes or synthesized audio bytes.
- **Impact**: Accidental leakage into logs is a common failure mode; harder to claim privacy-conscious handling.
- **Recommendation**: Add an explicit “no bytes in logs” constraint for `speaker_reference_bytes` and `audio_bytes`.

### Low

7) **Minor doc clarity/typos and naming drift**
- **Status**: OPEN
- **Description**: Minor issues like “Intellegible” spelling and inconsistent timestamp naming (plan references `timestamp_ms` while the platform uses `timestamp` with timestamp-millis).
- **Impact**: Low, but it adds friction during implementation and review.
- **Recommendation**: Cleanup pass for typos and field naming consistency.

## Questions
1) For v0.5.0, is “speed control” a fixed default (no API/contract) or a configurable parameter? If configurable, where is it specified (event field, env var, or internal config)?
2) Do we intend to ship one container image (CPU) and treat GPU as a future enhancement, or do we need two explicit deployment profiles to satisfy the epic’s stability statement?
3) Are there explicit guardrails for maximum output duration (beyond input text length), to prevent payload/latency blowups?

## Risk Assessment
- **Overall**: Medium
- **Primary risk drivers**: provider/profile ambiguity, incomplete mapping to epic AC (speed control), and plan/rubric drift (QA content + execution tracking).

## Recommendation
**APPROVE_WITH_CHANGES** for documentation quality and epic alignment.

Implementation can continue, but if the plan is intended to be an auditable artifact for v0.5.0 delivery, the Critical items should be addressed so the plan cleanly maps to the updated epic outcomes and Findings 013.