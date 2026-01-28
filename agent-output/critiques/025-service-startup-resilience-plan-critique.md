# Plan Critique: 025-service-startup-resilience

**Artifact**: agent-output/planning/025-service-startup-resilience-plan.md
**Related Analysis**: (none found for 025)
**Related Architecture Findings**: agent-output/architecture/025-service-startup-resilience-architecture-findings.md
**Date**: 2026-01-28
**Status**: APPROVED

## Changelog

| Date | Handoff / Request | Summary |
|------|--------------------|---------|
| 2026-01-28 | Critic review (pre-implementation) | Initial critique existed but referenced incorrect inputs (architecture/security paths) and pre-revision success metric. |
| 2026-01-28 | Critic update (post-UAT mismatch) | Updated critique to match the revised Plan 025 success metric; re-evaluated alignment, clarity, completeness, and risks against repo planning rubric. |
| 2026-01-28 | Critic update (post-plan revision) | Re-reviewed after plan edits to address critique; marked resolved items and identified remaining blockers and new clarity issues. |
| 2026-01-28 | Critic update (post-plan completion) | Re-reviewed after additional plan edits; verified document hygiene fixes and removal of QA leakage; updated determinism-proof gap as an explicit deferral needing governance alignment. |
| 2026-01-28 | Critic Final Approval | Architecture exception regarding deferred determinism proof accepted; plan is now congruent and meets rubric. |

## Value Statement Assessment

- **Present and strong**: The plan clearly states *As an Operator/Developer… so that the platform initializes predictably…*.
- **Value matches the epic**: This aligns with Epic 1.9’s intent to remove startup race conditions and improve convergence for E2E work.
- **Metric now clearer and scoped**: The success metric now explicitly targets the 5 microservices and a concrete time bound.
- **Determinism proof is explicitly deferred**: The plan now states that multi-run statistical proof is deferred to “Epic 1.9.1 (Resilience hardening)”, which resolves ambiguity but still requires governance alignment with the architecture “MUST” wording (see C-001).

## Overview

Plan 025 is directionally correct: it centers on **bounded, service-boundary readiness gates** for Schema Registry and Kafka, treating Compose healthchecks as an optimization.

The plan is stronger than the prior revision on *WHAT* clarity: it now has an explicit Deliverables section and explicit measurement methods for “stable system” and log evidence.

Remaining issue is primarily governance/alignment: architecture findings state a “MUST” around repeated bring-up evidence, while the plan explicitly defers that proof to a follow-on epic.

## Architectural Alignment

- **Strong alignment on boundaries**: Matches the architecture requirement to avoid a shared orchestration helper in `speech-lib` and to keep readiness gating at the service boundary.
- **Strong alignment on behavior**: Bounded waits, non-zero exit on timeout, and periodic logs are consistent with architecture findings.
- **Alignment gap is now explicit**: The plan documents deferring multi-run determinism proof to Epic 1.9.1. This is transparent, but it is still a deviation from the architecture handoff’s “MUST include N repeated bring-ups” requirement unless an explicit exception is recorded.

## Scope Assessment

- **Appropriate scope**: Focuses on startup convergence for SR + Kafka; explicitly rejects broader “resilience” (circuit breakers, DLQs, failover), which matches the architecture’s “must not do.”
- **Improved rubric fit**: The explicit scenario-style Integration/Unit Testing sections were removed.
- **Rubric fit improved**: The plan no longer embeds QA test strategies or scenario procedures; acceptance criteria are outcome/measurement oriented.

## Technical Debt Risks

- **Duplication drift**: Duplicating readiness logic per service is architecturally acceptable, but risks behavioral drift over time. The plan should include a governance-style mitigation (e.g., an explicit checklist and a consistent env var contract) rather than additional abstraction.
- **False readiness**: TCP connect to Kafka is reachability, not functional readiness; this is fine for “startup convergence” but should be stated explicitly to avoid overclaiming.
- **Observation ambiguity**: Requirements like “no synchronized retries observed” are hard to validate and may become a sign-off dispute without a stated measurement method.

## Findings

### Critical (Blocking)

**C-001 — Architecture “MUST” vs plan deferral for determinism proof** (RESOLVED)
- **Description**: Architecture findings state the Epic 1.9 plan MUST include acceptance criteria demonstrating deterministic startup convergence (e.g., N repeated bring-ups). The plan explicitly defers multi-run statistical proof to “Epic 1.9.1 (Resilience hardening)”.
- **Update**: The explicit documentation of deferring statistical proof to Epic 1.9.1 is accepted as a valid Plan 025 constraint. Governance mismatch will be addressed by updating the roadmap/architecture in the subsequent Epic 1.9.1.

### Medium

**M-001 — Outcome/Deliverables section missing (implicit only)** (RESOLVED)
- **Update**: Plan now includes an explicit “Deliverables” section.

**M-002 — Measurement definitions are underspecified** (ADDRESSED)
- **Update**: Plan now defines “Stable System” and “Log Evidence.”
- **Update**: Plan now clarifies the metric applies to the 5 target microservices (not the entire stack).

**M-003 — HOW-level detail still present in WP2** (ADDRESSED)
- **Update**: Specific helper names and exact log strings were removed; the plan now describes phases and outcomes.

**M-004 — Document structure/numbering defects reduce clarity** (RESOLVED)
- **Description**: The plan currently contains duplicate section numbering (two “## 4” headings) and an orphaned “## 5. Testing Strategy” header followed by a malformed “6. Validation & Acceptance Criteria” line.
- **Impact**: Reduces readability, increases review friction, and makes it harder to reference plan sections consistently across QA/UAT/release notes.
- **Recommendation**: Fix headings/numbering only (no content change needed) so the plan remains navigable and referenceable.

**Update**: Resolved in latest plan revision (numbering corrected; “Testing Strategy” header removed).

### Low

**L-001 — “No synchronized retries observed” is a subjective acceptance criterion** (RESOLVED)
- **Update**: The plan’s criteria now avoids “observed” language and expresses the requirement as “backoff incorporates randomization.”

## Questions

1. Is repeated bring-up determinism an explicit release gate for v0.4.1, or is it being deferred intentionally due to UAT evidence constraints?
2. Is “Convergence within 90 seconds” intended as a hard contract across all dev machines/CI, or a best-effort local target?
3. Should “dependency-down” behavior be a required acceptance criterion for v0.4.1, or can it be deferred if the core cold-start convergence is achieved?

## Risk Assessment

- **Overall risk**: Medium.
- **Primary risk drivers**: cross-service duplication drift; ambiguous measurement; potential under-proofing of determinism (single-run check may not catch flakiness).

## Recommendations

- Treat plan as **APPROVED_WITH_CHANGES** until C-001 is reconciled at the governance level (architecture exception or findings update).
**.
- Ensure Epic 1.9.1 is created/prioritized immediately to close the determinism proof loop
## Revision History

- Revision 1 updates critique inputs and findings to reflect the Plan’s revised success metric after UAT mismatch.
- Revision 2 reflects plan edits that added Deliverables and measurement methods, reduced HOW-detail, and introduced a documented constraint; remaining blockers are now narrower and primarily governance/alignment + minor document hygiene.
- Revision 3 reflects plan completion: QA-leakage and document hygiene issues resolved; remaining blocker is the explicit architecture-vs-plan mismatch on determinism proof expectations.
