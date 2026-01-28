---
ID: 028
Origin: 028
UUID: 4f6b2c1d
Status: Resolved
---

# Critique 028: Kafka Consumer Group Recovery Hardening (Plan 028)

Artifact: agent-output/planning/closed/028-kafka-consumer-group-recovery-hardening-plan.md

Date: 2026-01-28

## Changelog
| Date | Request | Summary | Status |
|------|---------|---------|--------|
| 2026-01-28 | Review for clarity, completeness, architecture alignment | Initial critique created | OPEN |
| 2026-01-28 | Re-review after plan revision | Plan updated to address all findings; critique closed | Resolved |
| 2026-01-28 | Re-review after additional plan edits | Reopened due to rubric regression and scope clarity gaps | OPEN |
| 2026-01-28 | Re-review after plan fix | Plan updated to remove QA/tooling prescription and clarify consumer-only scope | Resolved |
| 2026-01-28 | Final re-review (plan marked complete) | Verified no unresolved open questions; consumer-only scope and QA handoff pointer remain consistent with rubric and architecture | Resolved |

## Value Statement Assessment

Plan 028 has a clear user story and outcome: reduce post-restart Kafka consumer-group recovery tail latency so E2E smoke and bring-up stop failing for predictable “stabilization delay” reasons. This is aligned with the roadmap’s reliability/hardening intent.

## Overview

Directionally strong plan with good boundary discipline (shared-lib kept thin/pure) and explicit telemetry contracts. Two clarity issues re-emerged in the latest revision: (a) plan text has drifted back into QA/tooling prescription (rubric conflict), and (b) the “target services” list risks accidental scope creep by including non-consumers.

## Architectural Alignment

Aligned:
- Preserves the “shared-lib must remain thin / no orchestration” boundary.
- Does not introduce schema changes or cross-service workflow coupling.
- Adds observability contracts (structured telemetry + correlation identifiers) consistent with architecture priorities.

Watch-outs:
- Telemetry contracts are good, but the plan should ensure they remain compatible with existing trace propagation conventions (Kafka headers) and do not accidentally create payload logging.

## Scope Assessment

Scope is appropriately bounded (consumer tuning + telemetry + smoke-mode clarity). The “standardize across services” decision is a reasonable DRY move here because it reduces operational drift. Avoid expanding into broader Kafka security (SASL/TLS/ACLs) inside this plan unless the roadmap explicitly pulls it in.

## Unresolved Open Questions

None. (Previously open question about “conservative defaults” is now resolved with explicit guardrails in Plan 028.)

## Findings

### Critical

**C-001: Missing explicit Deliverables section**
- **Status**: RESOLVED
- **Description**: The plan implies deliverables via milestones, but does not list the concrete deliverables (artifacts and operator-facing changes) as a single section.
- **Impact**: Increases handoff ambiguity: implementers may ship tuning but miss smoke-mode docs, telemetry field standardization, or changelog artifacts.
- **Recommendation**: Add a “Deliverables” section that enumerates: standardized env var interface, shared-lib pure builder + constants, standardized telemetry events/fields, smoke-tool mode separation + docs, and release artifact updates.

### Medium

**M-001: Evidence artifact location/format is underspecified**
- **Status**: RESOLVED
- **Description**: Milestone 1 asks for baseline measurements “as an evidence artifact” but doesn’t define where it lives (path), format (markdown/table/json), or minimum fields.
- **Impact**: Measurement evidence can become ad-hoc and hard to compare across runs/services.
- **Recommendation**: Define a single evidence artifact location under `agent-output/` (e.g., `agent-output/analysis/028-...-baseline.md` or `agent-output/qa/028-...-metrics.json`) and specify minimum fields: timestamp, service, restart conditions, publish time, first-consume time, first-output time, config snapshot (allowlisted).

**M-002: Acceptance criteria are “materially reduced” but not operationalized**
- **Status**: RESOLVED
- **Description**: Milestone 2 acceptance criteria use “materially reduced vs baseline” without defining what qualifies (relative/absolute target, or at least a decision rule).
- **Impact**: Creates debate at QA/UAT time and makes regressions harder to detect.
- **Recommendation**: Define a decision rule without pinning exact tuning values (e.g., “p95 post-restart first-consume delay decreases by X% vs baseline in local compose; steady-state unaffected”). If you want to avoid numeric thresholds, specify an explicit comparison method and required evidence count.

**M-003: Plan contains a Testing Strategy section (potential rubric conflict)**
- **Status**: RESOLVED
- **Description**: The plan reintroduces a detailed “Testing Infrastructure Requirements” section inside the plan body. Even if well-intentioned, it reads as QA/tooling guidance that belongs in a QA handoff/runbook artifact, not in the plan rubric’s WHAT/WHY.
- **Impact**: Duplicates QA ownership in `agent-output/qa/`, creates drift risk, and increases the chance that future plan revisions become a “how-to test” doc rather than a delivery/outcomes plan.
- **Recommendation**: Collapse this section to a brief pointer: (1) state the required validation signals (already present), and (2) point to the canonical QA execution record (`agent-output/qa/028-...-qa.md`) for commands/tooling/env setup.

**M-004: Target service scope is ambiguous (consumer vs producer)**
- **Status**: RESOLVED
- **Description**: Milestone 2 references applying the consumer configuration helper across “Gateway/VAD/ASR/Translation/TTS”. The plan does not clearly state that the scope is **Kafka consumers** only, and Gateway may not be a consumer in this pipeline.
- **Impact**: Risk of wasted work, accidental scope creep, and confusing acceptance criteria (e.g., “reduce first consume” for a service that doesn’t consume).
- **Recommendation**: Make the target set explicit as “services that instantiate Kafka consumers in this pipeline” and list them accordingly. If Gateway is intentionally included, add one sentence explaining what it consumes and why it needs the contract.

### Low

**L-001: Static membership caveats could be elevated into the plan body**
- **Status**: RESOLVED
- **Description**: Plan introduces static membership env vars; it should explicitly call out the multi-replica uniqueness requirement and failure mode in the work plan, not only as a note.
- **Impact**: Avoidable misconfiguration and confusing recovery behavior.
- **Recommendation**: Add a short note in Milestone 2 tasks/acceptance criteria: static membership remains opt-in and requires unique instance IDs per replica.

## Risk Assessment

- **Primary risk**: availability regressions from aggressive tuning (rebalance churn) and observability regressions from excessive logging.
- **Mitigations present**: conservative defaults, validation/bounds, low-volume telemetry, debug gating.
- **Residual risk**: unclear success criteria can cause “it depends” outcomes during QA/UAT.

## Recommendations

All recommendations are now incorporated into Plan 028. No further changes required for clarity/completeness/architectural alignment.
