# Architecture Findings 012: Epic 1.7 TTS — Architecture Governance Gaps (Plan + Evidence Artifacts)

**Related Plan (if any)**: agent-output/planning/010-text-to-speech-plan.md (referenced; missing)
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | Architect | Documentation coherence check | Flags missing plan/evidence artifacts referenced by roadmap alignment + UAT, and records required governance corrections. |

## Context

Multiple artifacts reference Plan 010 and related validation outputs:
- agent-output/architecture/006-roadmap-alignment-validation-tts.md references agent-output/planning/010-text-to-speech-plan.md
- agent-output/uat/010-text-to-speech-uat.md references:
  - agent-output/planning/010-text-to-speech-plan.md
  - agent-output/validation/performance_report.md
  - agent-output/validation/retention-proof.md

In the current repo state:
- The referenced plan file is not present.
- The referenced validation directory/files are not present.

This is an architectural governance concern because it breaks traceability for contract changes and cross-agent sign-offs.

## Findings

### Must Change

- **Restore or re-point the canonical Plan 010 reference**
  - Either restore agent-output/planning/010-text-to-speech-plan.md, or update all references to the actual plan location.
  - Without this, the architecture cannot reliably assert which acceptance criteria were intended (and the system-architecture changelog references become unverifiable).

- **Fix or remove references to missing validation artifacts**
  - If performance/retention evidence exists elsewhere, link to it.
  - If it does not exist, documents must state “missing” explicitly (and UAT/Release gate should remain blocked).

- **Master architecture changelog must not reference missing findings**
  - agent-output/architecture/system-architecture.md currently cites “Findings 013/014” which do not exist.

### Risks

- **Governance drift**: teams can’t tell what was decided vs what was assumed.
- **Schema churn risk**: without a canonical plan, schema edits may violate compatibility invariants.

### Alternatives Considered

- **Ignore missing artifacts**
  - Rejected. This would undermine thesis-grade reproducibility and auditability.

## Integration Requirements

- Roadmap alignment docs, UAT docs, and the master architecture doc must reference real artifacts in-repo.

## Consequences

- Short-term overhead to restore coherence.
- Long-term reduction in integration mistakes and “phantom requirements”.

## Handoff

## Handoff to Roadmap/Planner/QA

**From**: Architect
**Artifact**: agent-output/architecture/012-tts-architecture-governance-gaps-architecture-findings.md
**Status**: APPROVED_WITH_CHANGES
**Key Context**:
- Plan/evidence artifact references are currently broken; this blocks trustworthy release gating.

**Recommended Action**: Restore the missing plan/evidence files or update references to existing ones before declaring Epic 1.7 complete.