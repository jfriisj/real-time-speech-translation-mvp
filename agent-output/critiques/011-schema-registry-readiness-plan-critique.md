# Critique: Plan 011 Schema Registry Readiness & Service Resilience (Revision 1)

**Artifact**: agent-output/planning/011-schema-registry-readiness-plan.md
**Related Analysis**: agent-output/analysis/011-schema-registry-readiness-analysis.md
**Related Architecture Findings**: agent-output/architecture/024-schema-registry-readiness-plan-architecture-findings.md
**Date**: 2026-01-28
**Status**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff / Request | Summary |
|------|--------------------------|---------|
| 2026-01-28 | Critic review (Rev 1) | Plan aligns with Findings 024 after revision, but has remaining scope/clarity inconsistencies (shared-lib/versioning leftovers, overly prescriptive healthcheck details, missing rollback notes). |

## Value Statement Assessment

- **Present**: The plan has a clear “As a / I want / So that” value statement.
- **Aligned to the real blocker**: Matches the analysis: the pipeline fails because `translation-service` crashes before producing `TextTranslatedEvent`, starving TTS and causing E2E timeouts.
- **Outcome-focused**: Primary outcomes (reliable bring-up; E2E unblocked) are correct.

## Overview

Plan 011 addresses a real integration failure mode: Schema Registry readiness races in Docker Compose startup. The revised approach is directionally consistent with the architecture boundary rule (resilience policy belongs at the service/orchestration layer, not in the shared contract artifact). 

However, the plan still contains some internal inconsistencies and a few “too detailed HOW” items that reduce clarity and reviewability.

## Architectural Alignment

- **Aligned with Findings 024 (core requirement)**: The plan now states that retry/backoff policies must live at the service boundary, not in `speech-lib`.
- **Good separation of concerns**:
  - Compose readiness improvements (healthcheck + dependency gating) are treated as infrastructure.
  - Service robustness outside Compose is handled via a bounded startup wait.

Remaining alignment concerns:
- **Scope drift risk**: The plan still hints at “critical infrastructure” generally, and WP3 suggests copying a wait loop into other services. That’s acceptable as an optional follow-up, but the plan should be explicit about whether the deliverable is “translation-service only” vs “all services” to avoid accidental expansion.

## Scope Assessment

- **Appropriately small** if scoped to: schema-registry healthcheck + translation-service bounded wait + compose dependency updates.
- **Roadmap/release mapping is unclear**: Target release is stated as v0.4.1, but the roadmap primarily references v0.4.0, v0.5.0, v0.6.0. A patch release is reasonable, but this should be reconciled (or explicitly labeled as “local-dev stability patch” not a roadmap release).

## Technical Debt & Delivery Risks

- **Healthcheck command fragility**: The plan specifies `curl` inside the schema-registry container. If the image lacks `curl`, the healthcheck will never succeed and can deadlock dependent services. This needs to be called out with an allowed fallback (or defined as “use whatever HTTP probe tool is present”).
- **Compose semantics variability**: `depends_on: condition: service_healthy` behavior can vary by Compose implementation/version; relying exclusively on it is risky. The plan correctly pairs it with service-side bounded wait, but should explicitly state that the service-side wait is the reliability backstop.
- **Residual “shared-lib change” language**: The plan still contains risk and version-management items that imply shared-lib will change, which contradicts the architecture requirement and the revised work packages.

## Findings

### Critical

| Issue | Status |
|------|--------|
| Shared-lib/versioning leftovers contradict plan direction | **OPEN** |

**Description**: Section 6 (“Shared lib update breaks other services”) and Section 7 (“Bump shared-lib version”) no longer match the revised approach (shared-lib should remain unchanged).

**Impact**: Creates implementation ambiguity and may cause unnecessary shared-lib churn, which the architecture explicitly tries to prevent.

**Recommendation**: Remove/replace shared-lib version bump and “shared-lib breakage” risk with service-/compose-scoped risks.

### Medium

| Issue | Status |
|------|--------|
| Over-prescriptive healthcheck parameters and commands in plan | **OPEN** |

**Description**: WP1 includes specific command/interval/retry values. This crosses into “HOW” detail and also bakes in assumptions (e.g., `curl` availability).

**Impact**: Review noise and avoidable brittleness; reviewers can’t easily tell what is required vs suggested defaults.

**Recommendation**: State the requirement (“healthcheck must validate SR can serve `/subjects`”) and treat concrete values as defaults or implementation notes.

| Issue | Status |
|------|--------|
| Missing rollout / rollback notes | **OPEN** |

**Description**: The plan lacks a high-level rollback strategy (per repo plan template guidance).

**Impact**: Harder to approve operationally; unclear how to revert if healthcheck gating causes deadlocks.

**Recommendation**: Add brief rollback notes (e.g., disable healthcheck gating; revert to service-only bounded wait).

### Low

| Issue | Status |
|------|--------|
| Deliverables and WP4 acceptance could be more observable | **OPEN** |

**Description**: WP4 mixes steps and outcomes. “Smoke test passes” is good; add an explicit observable symptom that resolves the original failure (e.g., translation-service no longer exits; `Published TextTranslatedEvent` appears during the run).

**Impact**: Minor; mostly affects review precision.

**Recommendation**: Tighten acceptance to 2–3 observable signals, without adding QA test spec detail.

## Questions

1. Is the plan’s scope intended to fix only `translation-service` (the proven blocker), or to apply the same pattern to all services in the compose stack?
2. Is v0.4.1 an official roadmap patch release, or should this be tracked as a “dev-experience stability fix” under an existing release?

## Risk Assessment

- **Overall risk**: Low-to-medium.
- **Main risk drivers**: healthcheck tool availability (`curl`), compose gating variability, and scope creep to “all infra readiness” or “all services” without explicit commitment.

## Recommendations

- **Proceed after plan edits**: This plan is close to approval quality, but the Critical inconsistency (shared-lib/version bump leftovers) should be corrected before implementation.
- **Keep service-side bounded wait as the primary guarantee**; treat compose gating as a dev ergonomics improvement.
