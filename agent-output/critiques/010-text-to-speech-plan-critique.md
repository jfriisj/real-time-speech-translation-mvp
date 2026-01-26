# Plan Critique 010: Text-to-Speech (TTS) Service (Kokoro ONNX)

**Artifact**: agent-output/planning/010-text-to-speech-plan.md
**Related Analysis**: agent-output/analysis/010-text-to-speech-analysis.md
**Related Architecture (master)**: agent-output/architecture/system-architecture.md
**Related Findings**: agent-output/architecture/011-tts-indextts-2-architecture-findings.md, agent-output/architecture/013-tts-kokoro-onnx-architecture-findings.md
**Date**: 2026-01-26
**Status**: APPROVED_WITH_CHANGES (Plan Revision 10)

This critique follows the rubric in `.github/chatmodes/planner.chatmode.md` (plans describe **WHAT/WHY**, include explicit contract gates, avoid QA/test-case content, avoid implementation “HOW”).

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-25 | User requested critique | Created critique for Plan 010 Revision 9 (Kokoro ONNX pivot), focusing on roadmap alignment, contract gates, scope, and risks. |
| 2026-01-26 | User requested updated critique | Updated critique for Plan 010 Revision 10 to reflect Analysis 010’s “integration + real inference” blockers and current architectural alignment. |

## Value Statement Assessment
The value statement matches the roadmap user story for Epic 1.7 (“hear translated text spoken naturally … hands-free”). It is clear and user-centric.

Clarity nit: the sentence casing/formatting is slightly inconsistent (“So that …”), but not ambiguous.

## Overview
Plan 010 (Rev 10) is directionally strong and materially improved versus Rev 9 because it now explicitly calls out the two blockers identified in Analysis 010:
- “Real Kokoro inference” (replacing the current mocked/noise output) is represented as a remaining work item.
- Integration validation for the large-payload `audio_uri` path is represented as a remaining work item.

The plan’s contract decision gates are mostly present (speaker context propagation, transport/failure semantics, schema compatibility, retention, observability), and the success metric measurement method is included.

Remaining issues are primarily about (1) artifact alignment/traceability, (2) scope hygiene (plan vs QA vs implementation tracker), and (3) a small set of missing “pinned decisions” required by the roadmap/architecture (notably CPU/GPU deployment profile and the roadmap’s “speed control” AC).

## Architectural Alignment
**Strong alignment (✅)**
- Matches Findings 011 on D2 dual-mode transport, `correlation_id` keying, and WAV invariants.
- Matches Findings 013 on layered boundary (orchestration vs synthesizer vs storage), pluggable synthesizer contract, and schema optionality (`model_name`, `audio_uri`, speaker fields).

**Gaps / drift (⚠️)**
- The plan header cites Findings 011 as the architecture reference while the Kokoro ONNX pivot’s controlling findings are in Findings 013. Keeping 011 is fine as historical context, but the “active” constraint set should be explicit to avoid audit confusion.
- Findings 013 requires an explicit decision on CPU-only vs GPU-enabled packaging/deployment profiles. Rev 10 mentions providers via env var but does not pin the deliverable profile(s).

## Scope Assessment
The scope is coherent for v0.5.0 if it remains constrained to:
- Consume `TextTranslatedEvent` → produce `AudioSynthesisEvent`.
- Provide dual-mode audio delivery (inline bytes vs MinIO URI) and preserve correlation.

The plan still mixes three categories that are better kept separate:
- Stable contract/outcome commitments (good and necessary).
- Execution tracking (checkbox completion).
- QA strategy/tooling/cov targets.

This reduces clarity for non-implementers (PM/QA/UAT/release) and increases drift risk over time.

## Technical Debt Risks
- **Contract drift risk**: “provider selection” and “speed control” are partly implied but not pinned; late additions can force schema changes or config churn.
- **Privacy leakage risk**: speaker/audio bytes are sensitive; the plan states retention expectations but does not explicitly prohibit logging raw bytes.
- **Operational ambiguity**: the epic’s roadmap value includes “stable CPU/GPU runtime”. Without a pinned deployment profile, this can become a recurring integration tax.

## Findings

### Critical

1) **Architecture reference ambiguity (Findings 011 vs Findings 013)**
- **Status**: OPEN
- **Description**: Plan header still points to Findings 011 as the architecture reference, while Findings 013 is the Kokoro ONNX pivot’s controlling architecture artifact.
- **Impact**: Weakens traceability for v0.5.0 release evidence and creates ambiguity about which constraints are authoritative.
- **Recommendation**: Make Findings 013 the primary architecture reference and keep Findings 011 as “historical context” (if desired).

2) **Roadmap Epic AC gap: “Basic duration/speed control” not pinned**
- **Status**: OPEN
- **Description**: The roadmap’s Epic 1.7 acceptance criteria include “Basic duration/speed control implemented.” Plan Rev 10 does not define what “speed control” means for v0.5.0 as an outcome (fixed default, configuration, or contract field).
- **Impact**: The plan can be “done” while the epic remains “not done”, creating late-cycle churn and/or schema changes.
- **Recommendation**: Add a short “Roadmap AC mapping” section and explicitly define the minimal acceptable “speed control” behavior for v0.5.0.

3) **CPU/GPU deployment profile decision not explicit**
- **Status**: OPEN
- **Description**: Findings 013 requires explicitly pinning whether v0.5.0 ships CPU-only, GPU-enabled, or distinct deployment profiles. Rev 10 mentions provider configuration but not the packaging/runtime profile.
- **Impact**: Hard to validate the epic’s “stability on CPU and GPU” value; higher risk of runtime failures during demos/benchmarks.
- **Recommendation**: Explicitly state the supported deployment profile(s) for v0.5.0 (and which are out of scope if only one is supported).

### Medium

4) **Plan contains QA strategy details (rubric drift)**
- **Status**: OPEN
- **Description**: The plan includes tooling/coverage targets and testing strategy content. Repo rubric expects QA ownership to live in `agent-output/qa/` while the plan stays on outcomes/contracts.
- **Impact**: Duplicate sources of truth; higher chance QA and plan drift out of sync.
- **Recommendation**: Reduce Testing Strategy to only non-negotiable constraints (e.g., “external I/O must be mockable”) and move the rest to the QA doc.

5) **Implementation tracker checkboxes reduce the plan’s clarity as a stable contract**
- **Status**: PARTIALLY_ADDRESSED
- **Description**: Rev 10 improves this by explicitly labeling “scaffold” vs “real inference”, but the plan still mixes “what we must deliver” and “what is done today.”
- **Impact**: Stakeholders can misread scaffolded work as functional completeness.
- **Recommendation**: Either separate “Plan” vs “Implementation tracker”, or clearly label checklists as non-authoritative status reporting.

6) **Observability contract missing byte-redaction rule**
- **Status**: OPEN
- **Description**: The plan mandates correlation/model/latency fields but does not explicitly forbid logging `speaker_reference_bytes` or `audio_bytes`.
- **Impact**: Accidental leakage into logs is a common failure mode; increases privacy and storage risk.
- **Recommendation**: Add a single explicit constraint: no raw audio bytes in logs.

### Low

7) **Minor wording/typo and config naming consistency**
- **Status**: OPEN
- **Description**: “Intellegible” spelling; provider env var naming in the plan (`ONNX_PROVIDER`) should be consistent and unambiguous.
- **Impact**: Low severity but creates friction and confusion.
- **Recommendation**: Cleanup pass for typos and naming consistency.

## Questions
1) For v0.5.0, is “speed control” intended as a fixed default (no contract surface), an env var, or an event field?
2) Do we intend to validate CPU-only in v0.5.0 and defer GPU, or do we need two explicit deployment profiles to satisfy the roadmap’s stability claim?
3) Is there an explicit maximum expected output duration (beyond input text length cap) to keep payload/latency predictable?

## Risk Assessment
- **Overall**: Medium
- **Primary risk drivers**: missing pinned decisions (speed control, CPU/GPU profile), plan/QA separation drift, and privacy/observability redaction ambiguity.

## Recommendations
Maintain **APPROVED_WITH_CHANGES**. Rev 10 is close, but the Critical items should be addressed for the plan to be a clean, auditable v0.5.0 artifact aligned with the roadmap and Findings 013.