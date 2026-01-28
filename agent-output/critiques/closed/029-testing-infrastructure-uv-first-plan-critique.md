---
ID: 029
Origin: 029
UUID: 8b4c1a2f
Status: Resolved
---

# Critique 029: Test Infrastructure Hardening (uv-first, reproducible QA)

**Artifact**: `agent-output/planning/closed/029-testing-infrastructure-uv-first-plan.md`
**Reviewed On**: 2026-01-28

## Verdict

APPROVED (all blocking findings addressed).

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-28 | User requested plan review | Initial critique created: clarity/completeness/architecture alignment review and actionable revisions. |
| 2026-01-28 | User marked plan complete | Re-review after plan revision: roadmap alignment, test-strategy removal, uv fallback, and evidence artifact path added; remaining blocker is an undecided contract decision for TTS startup helper ownership. |
| 2026-01-28 | Contract decision finalized | Re-review: Milestone 3 contract decision set to Option A with explicit contract statement; critique closed as Resolved. |

## Value Statement Assessment

- **Present**: Yes. The user story is clear and directly tied to QA/CI reliability.
- **Measurable outcome**: Improved. The plan defines validation signals and an evidence artifact location.
- **Master objective alignment**: Improved. Roadmap placement is now justified as a dependency for Plan 028 QA and as part of the Epic 1.9.1 startup-resilience hardening thread.

## Overview

Plan 029 correctly identifies a real blocker (host Python lacks `pip`; `pytest` not declared; full-suite blocked by TTS startup test mismatch) and proposes a constrained, high-leverage outcome: a single canonical uv-first workflow and aligned dependency declarations.

The revised plan resolves the initial critique items (roadmap alignment section, removal of plan-level testing strategy, explicit `uv` environment contract, dedicated evidence artifact path) and finalizes the remaining contract decision for TTS startup helper ownership.

## Architectural Alignment

- **Boundary fit**: Good. This plan is tooling/process-oriented and does not push runtime orchestration logic into shared-lib or services.
- **Risk of coupling**: Moderate, but manageable. Standardizing `PYTHONPATH` across services can entrench non-packaged imports; ensure this is explicitly framed as a test-only contract.

## Scope Assessment

- **Scope is appropriate**: Yes—focused on removing environmental variance and unblocking a known suite failure.
- **Potential scope creep**: If this becomes “CI design” or “full packaging refactor”, it will exceed the plan’s stated scope.

## Technical Debt Risks

- If the solution relies on `PYTHONPATH` ad-hoc wiring long-term, it can become brittle as services evolve. If this is intended as a short-term QA unblocker, record that explicitly.

## Findings

### C-001: Epic/Release Alignment Is Ambiguous
- **Severity**: HIGH
- **Status**: RESOLVED
- **Location**: Plan Header (“Epic Alignment: Epic 1.9.1” and “Target Release: v0.5.0”)
- **Description**: This is a test infrastructure hardening plan. Tying it to Epic 1.9.1 (startup resilience hardening) and v0.5.0 may be correct as a support item, but the plan does not justify why it belongs to that epic/release versus being a cross-cutting “QA/CI reliability” work item.
- **Impact**: Risk of roadmap drift and confusion during release gating (“Why is uv-first test tooling in v0.5.0?”). Also risks later churn if Epic 1.9.1 remains P2/backlog while v0.5.0 is actively targeted.
- **Recommendation**: Add a short “Roadmap Alignment” section that explicitly states whether this is:
  - a dependency of Plan 028 QA signoff for v0.5.0, or
  - a cross-cutting platform capability (then align to a dedicated QA/CI epic or a process-improvement track).

**Update (Re-review)**: The plan now includes a dedicated “Roadmap Alignment” section with explicit justification.

### C-002: Plan Includes QA/Test Strategy Content (Repo Rubric Violation)
- **Severity**: MEDIUM
- **Status**: RESOLVED
- **Location**: “Testing Strategy (high-level)” section
- **Description**: Repo rubric requires plans to focus on WHAT/WHY and avoid QA test strategy content (QA owns that in `agent-output/qa/`). Even though this is high-level, it sets a precedent that plans contain testing guidance.
- **Impact**: Inconsistent documentation ownership and repeated edits across plan/QA docs.
- **Recommendation**: Replace “Testing Strategy” with a “Validation Signals” section only (already present in Milestone 4) and move any “how to run tests” narrative into:
  - a developer runbook (README/docs), and
  - the Plan 028 QA artifact for executed commands/evidence.

**Update (Re-review)**: The plan-level “Testing Strategy” section has been removed; validation is kept as signals + evidence capture.

### C-003: Acceptance Criteria Need a Cross-Host/CI Fallback Path
- **Severity**: HIGH
- **Status**: ADDRESSED
- **Location**: Milestone 1 acceptance criteria; Dependencies (“uv available”)
- **Description**: The plan assumes `uv` is available everywhere. That is verified on the current host, but not guaranteed across QA environments or CI.
- **Impact**: The plan can “pass locally” but fail in CI/other machines, reintroducing the original non-reproducibility problem.
- **Recommendation**: Add an explicit fallback contract such as:
  - “If `uv` is unavailable, provide a supported alternative (e.g., `python -m venv` + `pip` inside venv) OR explicitly require `uv` in CI images.”
  - Consider pinning a minimum `uv` version if required.

**Update (Re-review)**: The plan now defines a preferred requirement (“`uv` is required”) and an explicit fallback option. A minimum `uv` version is still optional; add it only if specific features are required.

### C-004: Startup Helper Ownership Contract Is Still Undecided (Blocking)
- **Severity**: HIGH
- **Status**: RESOLVED
- **Location**: Milestone 3 (“Contract Decision (to be completed during implementation)”)
- **Description**: The plan now includes a “Contract Decision” subsection, but it leaves the key decision blank (A vs B). Per the repo planning rubric (“no hidden decisions” / contract decision gates), relevant contract decisions must be explicit before the plan can be approved.
- **Impact**: High risk of re-drift and recurring suite breakage; implementers may pick different interpretations and embed accidental API surface changes.
- **Recommendation**: Choose Option A or B in the plan now, and write the contract statement in one sentence (what tests target, what API surface is stable).

**Update (Re-review)**: The plan now finalizes Option A and states the contract (tests target `speech_lib.startup`; service modules may re-export but do not own private helper APIs).

### M-002: Deliverables Lack Clear “Done” Evidence Artifacts
- **Severity**: MEDIUM
- **Status**: RESOLVED
- **Location**: Deliverables and Milestone 4
- **Description**: Plan references recording commands/outcomes in the Plan 028 QA doc, but Plan 029’s own evidence artifact location isn’t defined.
- **Impact**: Hard to audit Plan 029 completion later; creates coupling to Plan 028 QA doc.
- **Recommendation**: Define a Plan 029 QA artifact path (e.g., `agent-output/qa/029-testing-infrastructure-uv-first-qa.md`) as the canonical evidence location, and cross-link it from Plan 028 QA only as needed.

**Update (Re-review)**: The plan now defines `agent-output/qa/029-testing-infrastructure-uv-first-qa.md` as the dedicated evidence artifact.

### L-001: README Is Currently Empty (Doc Placement Ambiguity)
- **Severity**: LOW
- **Status**: ADDRESSED
- **Location**: Milestone 1, Task 2 (“README or dedicated doc”)
- **Description**: The plan suggests documenting commands in README, but README content is currently minimal, and the repo uses `agent-output/qa/` for executable evidence.
- **Impact**: Developers may not discover the canonical workflow; increased onboarding friction.
- **Recommendation**: Prefer a dedicated developer runbook file under `docs/` or a concise README section, and avoid duplicating “executed evidence” outside `agent-output/qa/`.

**Update (Re-review)**: The plan now prefers a `docs/` runbook plus a short README pointer, which is consistent with repo doc ownership.

## Unresolved Open Questions

None detected in the plan text (no `OPEN QUESTION` markers).

## Risk Assessment

- **Primary risk**: Toolchain standardization becomes environment-specific (works only where `uv` exists) or expands into packaging refactors.
- **Secondary risk**: TTS startup helper ownership remains undecided, causing recurring suite breakage.

## Recommendations

- Finalize the Milestone 3 “Contract Decision” by choosing Option A or B and stating the stable test target/API surface.
