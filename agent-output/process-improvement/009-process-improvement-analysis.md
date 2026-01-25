# Process Improvement Analysis 009: Scientific Planning & Evidence-Based UAT

**Source**: [Retrospective 009 (VAD Service)](agent-output/retrospectives/009-voice-activity-detection-retrospective.md)
**Date**: 2026-01-25
**Status**: DRAFT

## Executive Summary
Retrospective 009 identified that "Scientific Planning" (defining specific measurement methods upfront) and "Evidence-Based UAT" (consuming machine-readable QA outputs) were key drivers of the VAD release's success. It also noted recurring issues with Release Document corruption due to partial edits. This analysis proposes standardizing these patterns across Planner, Critic, QA, UAT, and DevOps agents.

**Recommendation**: **APPROVE**. The changes are additive, low-risk, and directly address observed quality/workflow issues.

## Changelog Pattern Analysis
- **Planner**: 5 revisions were required to get Plan 009 right, but implementation was smooth (1 attempt). This supports the "Shift Left" validation strategy.
- **QA/UAT Handoff**: The manual creation of `vad_metric_summary.json` by QA allowed UAT to be objective. This pattern should be codified.
- **Release**: Text duplication in `v0.4.0.md` required manual intervention.

## Recommendation Analysis

### 1. Mandatory "Measurement Method" Section
- **Source**: Retrospective 009 (Improvement #1)
- **Current State**: Planner asks for "Measurable success criteria when possible".
- **Proposed Change**: For performance/efficiency plans, MANDATE a "Success Metric Measurement Method" section defining datasets, formulas, and guardrails.
- **Affected Agents**: `02-planner`, `05-critic`
- **Risk**: Low. Increases planning rigor but reduces downstream ambiguity.

### 2. Evidence-Based UAT (JSON Artifacts)
- **Source**: Retrospective 009 (Improvement #2)
- **Current State**: QA updates markdown reports; UAT reads markdown/logs.
- **Proposed Change**: QA should output key metrics to JSON files (e.g., `metrics.json`) alongside the report. UAT should explicitly reference these.
- **Affected Agents**: `08-qa`, `09-uat`
- **Risk**: Low. Standardizes handoff format.

### 3. Release Document Safety (Rewrite Policy)
- **Source**: Retrospective 009 (Improvement #3)
- **Current State**: "When updating release docs, read the ENTIRE file first to avoid duplicating headers/sections."
- **Proposed Change**: Change instruction to prefer `create_file` (overwrite) over `replace_string_in_file` for whole-doc updates to ensure consistency.
- **Affected Agents**: `11-devops`
- **Risk**: Low. `create_file` is safer for whole-file regeneration than complex regex replacements.

## Conflict Analysis

| Recommendation | Conflicting Instruction | File | Nature of Conflict | Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **Release Doc Rewrite** | "read the ENTIRE file first to avoid duplicating... Do not use create_file if the file exists [implied preference for edit]" | `11-devops.agent.md` | Logic/Preference | Update instruction to explicitly favor `create_file` for *Release Docs* when regenerating the full status, as partial edits are error-prone. |

## Risk Assessment

| Recommendation | Risk Level | Rationale | Mitigation |
| :--- | :--- | :--- | :--- |
| Mandatory Measurement Method | LOW | Adds work to planning phase. | Critic ensures it's only required for *performance/efficiency* plans, not simple features. |
| Evidence-Based UAT | LOW | Requires QA to write JSON. | Standardize the JSON structure (simple key-value pairs). |
| Release Doc Rewrite | LOW | Overwriting loses history if not careful. | Agent must read *before* rewriting to preserve history (e.g. user confirmation timestamps). |

## Implementation Recommendations

### Priority 1: Scientific Planning (High Impact)
Update Planner and Critic to enforce the "Measurement Method" section. This prevents vague "make it faster" plans.

### Priority 2: Release Doc Stability (Workflow Fix)
Update DevOps instructions to prevent the recurring "duplication" bug in release docs.

### Priority 3: Evidence-Based UAT (Best Practice)
Update QA and UAT to formalize the JSON handoff pattern.

## Suggested Agent Instruction Updates

### [02-planner.agent.md](.github/agents/02-planner.agent.md)
**Add to "Response Style"**:
> - **Performance Plans**: MUST include "Success Metric Measurement Method" section (dataset definition, calculation formula, guardrails).

### [05-critic.agent.md](.github/agents/05-critic.agent.md)
**Add to "Review Method"**:
> - **Performance Plans**: Is "Success Metric Measurement Method" defined? (Dataset, formula, guardrails).

### [08-qa.agent.md](.github/agents/08-qa.agent.md)
**Add to "Process - Phase 2"**:
> - **Metrics**: For quantitative criteria, output a machine-readable JSON artifact (e.g., `agent-output/qa/NNN-metrics.json`) to facilitate UAT.

### [09-uat.agent.md](.github/agents/09-uat.agent.md)
**Add to "Workflow"**:
> - **Evidence**: Consume machine-readable QA artifacts (JSON) as primary evidence where available.

### [11-devops.agent.md](.github/agents/11-devops.agent.md)
**Update "Constraints"**:
> - **Release Doc Updates**: Prefer reading the full file and re-creating it (`create_file`) over partial text replacements, to prevent duplication errors.

## User Decision Required
- **Approve Updates**: Update agent instructions as proposed? (Yes/No)
