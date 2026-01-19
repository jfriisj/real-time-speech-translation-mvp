# Plan Critique — 005 Ingress Gateway

**Artifact Path**: agent-output/planning/005-ingress-gateway-plan.md  
**Related Analysis**: agent-output/analysis/005-ingress-gateway-analysis.md, agent-output/analysis/007-ingress-gateway-depth-analysis.md  
**Related Architecture**: agent-output/architecture/system-architecture.md  
**Related Security Review**: agent-output/security/005-ingress-gateway-security-pre-implementation.md  
**Date**: 2026-01-19  
**Status**: Revision 4

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-19 | User: “Critique for clarity, completeness, scope, risks, and alignment” | Initial critique focusing on v0.3.0 Epic 1.5 outcomes and plan quality gates |
| 2026-01-19 | User: “Plan is complete. Please critique…” | Re-review after plan revision to address prior C-001/C-002 and reduce over-specification |
| 2026-01-19 | User: "Please revise the plan to address the critique findings" | Re-review after plan generalized protocol specifics (M-001), linked QA artifact (M-003), and clarified correlation_id policy (L-003) |
| 2026-01-19 | User: "The roadmap/epic changed" | Re-review after Epic 1.5 roadmap updated to “Phase 1 (WebSocket)” and plan status updated to Approved |
| 2026-01-19 | User: “Plan is complete. Please critique for clarity, completeness, scope, risks, and alignment.” | Re-review against Analysis 007 stop conditions; confirm remaining gaps (QA artifact, sentinel spec home, load verification expectations, gRPC follow-up bookkeeping) |
## Value Statement Assessment
The value statement is clear and correctly framed as a client-facing enablement epic (“Client Developer streams audio to entry point”). It aligns with the roadmap’s intent to move from CLI-only to “connectable platform.”

**Key Alignment Note**: The plan scopes delivery to **Phase 1 (WebSocket)** and documents gRPC as deferred post-v0.3.0. The roadmap has now been updated to match this scope, so the plan and epic outcomes are aligned.

## Overview
Plan 005 is directionally strong: it establishes an ingress boundary, preserves existing contracts (`AudioInputEvent` on `speech.audio.ingress`), and includes explicit non-functional security constraints.

The revision improves plan hygiene by separating detailed test cases from the plan and by expressing milestones more as requirements than step-by-step implementation.

## Architectural Alignment
**Aligned** with agent-output/architecture/system-architecture.md:
- Uses the canonical ingress contract (`AudioInputEvent` to `speech.audio.ingress`).
- Keeps v0.2.x reproducibility intact by not changing downstream topic taxonomy.
- Treats gateway as a boundary between untrusted clients and internal Kafka.

**Alignment Note**:
- The roadmap now reflects “Phase 1 (WebSocket)” for Epic 1.5, resolving the prior scope mismatch. The architecture doc still references “WebSocket/gRPC” as a general capability, which is acceptable as long as release-scoped acceptance criteria remain WebSocket-only for v0.3.0.

## Scope Assessment
Scope is reasonable for v0.3.0 if the goal is “first usable ingress” and not “full multi-protocol ingress.” The plan keeps streaming-chunking out-of-scope (correctly referencing Epic 3.1).

**Revision note (Revision 2)**: Protocol over-specification has been successfully addressed. The plan now treats protocol details as requirements-level constraints and pushes specific contract shapes to QA/client integration artifacts.

## Technical Debt Risks
- **Protocol lock-in**: Hard-binding to PCM16 16kHz mono as a fixed contract may create compatibility debt with real clients (mobile/web often provide different formats). As written, this is acceptable as an MVP constraint but should be explicitly labeled as such.
- **Operational debt**: The plan introduces several runtime controls (timeouts, connection caps, origin allowlist). Validation ownership is now correctly delegated to the referenced QA artifact.
- **Governance debt**: Analysis 007 recommends explicit stop conditions (QA artifact existence, limit verification, and gRPC follow-up tracking). These are not stated as a hard planning handoff gate in Plan 005 itself, increasing risk of “assumed done” without auditable evidence.

## Findings

### Critical
| ID | Issue Title | Status | Description | Impact | Recommendation |
|----|-------------|--------|-------------|--------|----------------|
| C-001 | Roadmap/plan alignment for Epic 1.5 scope | RESOLVED | Roadmap updated to “Ingress Gateway — Phase 1 (WebSocket)” with gRPC deferred; plan matches this scope. | Removes release sign-off ambiguity and scope disputes. | None. |
| C-002 | QA ownership violation: test cases embedded in plan | RESOLVED | Detailed test cases were removed from the plan and replaced with high-level validation requirements + references to QA/UAT artifacts. | Reduces duplicated sources of truth and keeps plan in the intended WHAT/WHY boundary. | Create/link a dedicated QA artifact for Plan 005 so validation remains auditable. |

### Medium
| ID | Issue Title | Status | Description | Impact | Recommendation |
|----|-------------|--------|-------------|--------|----------------|
| M-001 | Over-specification of implementation details | RESOLVED | Plan has generalized protocol specifics ("connection close or structured end-of-stream message" vs fixed JSON, removed `io.BytesIO` mention, generalized buffer size constraint). | Reduces rework risk; maintains focus on WHAT/WHY over HOW. | Protocol contract details should live in QA/client integration docs referenced by the plan. |
| M-002 | Security gate phrasing mixes WHAT/WHY with implementation workflow | RESOLVED | The gate is now outcome-focused (“MUST enforce…”) and pushes procedural verification to Security 005 / QA/UAT artifacts. | Improves maintainability and avoids procedural brittleness in the plan itself. | Ensure QA/UAT artifacts enumerate the procedural checks. |
| M-003 | Validation artifact referenced but missing | OPEN | Plan references `agent-output/qa/005-ingress-gateway-qa.md`, but the artifact does not currently exist in the workspace. | Risk of “paper compliance” where verification is implied but not auditable. | Create `agent-output/qa/005-ingress-gateway-qa.md` and map it to Plan Section 3.1 controls and Section 5 validations. |
| M-004 | Analysis 007 outcomes not closed in plan/QA | OPEN | Analysis 007 defines stop conditions and calls for a minimal sentinel/handshake contract and limit verification. Plan 005 currently defers protocol specifics to QA, but QA 005 is missing, and the plan does not state the Analysis 007 stop condition as an explicit handoff gate. | Ambiguity for client integrators; higher risk of incomplete verification and “it works on my machine” implementation drift. | Either (a) add an explicit “Stop Condition / Handoff Gate” subsection in the plan referencing Analysis 007, or (b) ensure QA 005 exists and explicitly records the sentinel contract + load/limit verification evidence. |

### Low
| ID | Issue Title | Status | Description | Impact | Recommendation |
|----|-------------|--------|-------------|--------|----------------|
| L-001 | Missing explicit “out of scope” for persistence/retention | RESOLVED | Plan now explicitly forbids persisting audio to disk by default. | Reduces privacy/retention ambiguity. | Ensure QA/UAT verifies “no disk writes” in container runtime behavior. |
| L-002 | Plan status semantics | RESOLVED | Plan status updated to “Approved” after roadmap alignment was completed. | Reduces confusion for downstream agents. | None.
| L-003 | Correlation ID policy clarified | RESOLVED | Plan now explicitly states: "Gateway always generates its own correlation_id; any client-provided ID is ignored to ensure consistent UUID format and prevent spoofing/collisions." | Removes ambiguity for client integrators and implementers. | None; policy is clear and documented. |

## Questions
1. Does `agent-output/qa/005-ingress-gateway-qa.md` exist and enumerate procedural validation mapped to Security 005 controls and Plan Section 5 validations?
2. Where is the authoritative, testable **sentinel/EOF contract** recorded for client developers (QA 005 vs a client integration doc), and what is the minimal required message shape?
3. Is there an explicit, auditable follow-up item for the deferred gRPC scope (Epic 1.5b/backlog artifact), as recommended by Analysis 007?

## Risk Assessment
- **Delivery risk**: Low (roadmap and plan are aligned on Phase 1 WebSocket delivery).
- **Operational risk**: Low → Medium until the referenced QA artifact exists and is used as evidence of control verification.
- **Governance risk**: Low (process boundaries are clean; QA is the correct home for procedural checks).
	- **Note**: Governance risk becomes Medium if QA 005 remains missing, because it removes the only planned “verification anchor” for security and protocol behavior.

## Recommendations
**Non-Blocking (Process Hygiene)**:
- Ensure `agent-output/qa/005-ingress-gateway-qa.md` is created and explicitly maps: (a) Plan Section 3.1 security controls, (b) Plan Section 5 validations, and (c) any UAT expectations.
- If architecture documentation is used as release-scoped truth, consider adjusting its wording to avoid implying gRPC ships in v0.3.0.
- Ensure the sentinel/EOF contract has exactly one canonical home (preferably QA 005 for verifiability), and is referenced from the plan to avoid multiple drifting specs.

## Revision History
- Initial version created 2026-01-19.
- Revision 1 updated 2026-01-19 after plan scope/status/test-boundary revisions.
- Revision 2 updated 2026-01-19 after plan generalized protocol specifics (M-001 RESOLVED), linked QA artifact (M-003), and clarified correlation_id policy (L-003 RESOLVED).
- Revision 3 updated 2026-01-19 after roadmap Epic 1.5 updated to “Phase 1 (WebSocket)”, resolving C-001.
- Revision 4 updated 2026-01-19 to incorporate Analysis 007 stop-condition expectations; confirmed QA 005 still missing and added M-004.

## Process Note
Reviewer instruction referenced a `.github/chatmodes/planner.chatmode.md` file, but no such file exists in this workspace (`.github/` contains `agents/` and `skills/`). Review proceeded based on the artifact inputs listed above.
