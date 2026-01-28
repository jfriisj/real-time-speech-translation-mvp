# Critique: Plan 003 — Text-to-Text Translation (Translation Service)

**Artifact**: agent-output/planning/003-translation-service-plan.md
**Related Analysis**: agent-output/analysis/003-translation-service-analysis.md
**Related Analysis (Diagnostics)**: agent-output/analysis/016-translation-test-infra-analysis.md
**Related Architecture Findings**: agent-output/architecture/003-translation-service-architecture-findings.md
**Related Roadmap**: agent-output/roadmap/product-roadmap.md (Release v0.2.0, Epic 1.3)
**Date**: 2026-01-28
**Status**: Revision 4 — APPROVED

> Process note: Review performed using `.github/chatmodes/planner.chatmode.md` as the rubric, plus the roadmap, analysis, and architecture findings.

## Changelog
| Date | Trigger | Summary |
|------|---------|---------|
| 2026-01-15 | Plan 003 completed | Reviewed for clarity/completeness/scope/risks/alignment; identified minor gaps around acceptance criteria, config surface, and failure-handling specifics. |
| 2026-01-15 | Plan 003 updated via Analysis 003 | Re-reviewed after plan updates; resolved prior gaps (explicit `TARGET_LANGUAGE`, commit-on-drop semantics, missing input language default) and approved. |
| 2026-01-28 | Epic 1.3 reopened + Plan updated | Re-reviewed because Epic 1.3 is now “In Progress” for diagnostics/stabilization and Plan 003 gained test-infrastructure content; identified scope/clarity issues and plan/roadmap drift. |
| 2026-01-28 | Plan revised after critique | Re-reviewed after the plan was updated to be outcome-focused for diagnostics and to remove “HOW/QA mechanics” from Milestone 6; approved with minor follow-ups. |

## Value Statement Assessment
- **Present**: YES.
- **Aligned to Roadmap**: YES.
	- The plan retains the Epic 1.3 user value statement and now adds an explicit stabilization/diagnostics initiative.
- **Measures of Success**: MOSTLY.
	- Core functional measures remain testable.
	- Diagnostic success is now stated (integration suite runnable in target environment).
	- Minor gap: the plan states “identify the root cause” in the initiative, but does not list a concrete evidence artifact or explicit “root cause classified” outcome.

## Overview
Plan 003 remains architecturally aligned on the core contract and topics. The latest revision successfully reframes the reopened epic work as **Diagnostics & Stabilization** and changes test enablement from a prescriptive “how to run tests” section into a set of outcome requirements.

The main remaining improvements are clarifications (what artifact proves diagnostics ran, and how “root cause identified” is recorded), rather than scope or architecture blockers.

## Architectural Alignment
- **Contract schemas**: Aligned (post-architecture review, the plan uses `TextTranslatedEvent.payload.text`, `source_language`, `target_language`).
- **Topics**: Aligned (canonical topic taxonomy matches architecture master).
- **Delivery semantics**: Aligned (at-least-once acknowledged; duplicates tolerated).
- **Failure signaling**: Aligned (plan now defines “log + drop” as log error and commit offset).
- **Shared contract artifact**: Aligned (uses `speech-lib` for Avro/Kafka; does not propose cross-service imports beyond shared contract).

Alignment watch-out:
- The roadmap status note explicitly says the implementation moved beyond the mock and uses a real Hugging Face model. The plan still emphasizes a deterministic mock as MVP priority, which is now historically true but operationally misleading for the reopened epic.

## Scope Assessment
- **In scope (good)**:
  - Consumer → translate → producer loop.
  - Containerized service + Compose integration.
  - Unit tests for translator and handler; smoke/integration validation.

Scope concern (prior):
- The earlier revision included Dockerfile/Compose specifics and named fixtures. This has been addressed by rewriting Milestone 6 as requirements and constraints rather than implementation steps.

## Technical Debt / Delivery Risks
- **Language-pair ambiguity** (Resolved): Plan defines `TARGET_LANGUAGE` (default `"es"`) and documents how output `payload.target_language` is populated.
- **Operational semantics under failure** (Resolved): Plan defines drop behavior as committing the offset to avoid poison-pill loops.
- **Versioning mismatch risk** (Low): The plan targets v0.2.0 and suggests setting service version to 0.2.0. If other services follow different versioning, this can introduce release-note confusion. (Not an architecture blocker, but worth clarifying.)

Residual risks worth tracking:
- **Test container drift**: A separate test container capability can drift from the production container over time. The plan mitigates this by explicitly requiring reuse/alignment “where possible,” but it’s still a watch item.
- **Dependency weight**: Translation uses ML dependencies; cold-start and caching behavior can dominate perceived stability. The plan acknowledges this risk.

## Findings

### Critical
None.

### Medium

1. **Target language configuration is underspecified**
	- **Status**: RESOLVED
	- **Description**: Plan requires setting `payload.target_language` but doesn’t define the expected configuration interface (env var, default, allowed values) or how it impacts the mock translator.
	- **Impact**: Ambiguity in demo behavior; harder QA reproducibility.
	- **Recommendation**: Define a single MVP config input (e.g., one env var with default) and document expected behavior when missing/invalid.

2. **Failure-handling semantics are too high-level for Kafka reality**
	- **Status**: RESOLVED

3. **Diagnostics evidence artifact is not specified**
	- **Status**: OPEN
	- **Description**: The plan now correctly requires that the integration suite can run in the target environment, but it does not say what artifact proves it (e.g., QA report update, stored logs snapshot, or benchmark entry).
	- **Impact**: “Diagnostics ran” can become subjective, leading to rework or debate during handoff.
	- **Recommendation**: Add a single sentence defining the evidence location/format (e.g., update the QA report and attach a logs snapshot).

### Low

3. **Plan doesn’t explicitly restate the required output fields from schema**
	- **Status**: RESOLVED
	- **Description**: The plan now references required output fields in Milestone 3, but the “Measure of Success” and QA section could more explicitly enumerate required output metadata (`source_language`, `target_language`) to prevent regression.
	- **Impact**: Small; mostly prevents implementer/QA misinterpretation.
	- **Recommendation**: Optional: add explicit checks for `payload.source_language` and `payload.target_language` in the integration test scenario to match the schema requirements.

4. **Template process gap**
	- **Status**: RESOLVED
	- **Description**: This critique previously stated `.github/chatmodes/planner.chatmode.md` was missing; it exists now and is used as the rubric. Template availability for other doc types is still a general process concern, but not a blocker for this plan.
	- **Impact**: Slows future architecture reviews and increases formatting drift.
	- **Recommendation**: Add/standardize a template location in a process-improvement doc (not required to implement the translation service).

## Questions
1. Where should the diagnostic evidence be recorded (QA report update, `agent-output/build-logs/` snapshot, or benchmark doc)?
2. Is the plan’s “mock-first” historical note still useful, or should it be updated to reflect the current runtime reality (real model in place) while keeping mock as a fallback option?

## Verdict
**APPROVED**. The plan is now clear, aligned, and appropriately scoped for the reopened diagnostics/stabilization objective. The remaining gap is a minor completeness item: define what artifact constitutes “diagnostics ran” for auditability.
