# Retrospective 005: Ingress Gateway

**Plan Reference**: `agent-output/planning/005-ingress-gateway-plan.md`
**Date**: 2026-01-19
**Retrospective Facilitator**: retrospective

## Summary
**Value Statement**: As a Client Developer (Web/Mobile), I want to stream audio via WebSocket to a single entry point, so that I can connect external devices (microphones, browsers) to the pipeline without direct Kafka access or local CLI scripts.
**Value Delivered**: YES
**Implementation Duration**: 1 day (Intraday cycle on 2026-01-19)
**Overall Assessment**: High-velocity delivery of a critical architectural boundary (Ingress) with strong security controls. The explicit "Security Gate" pattern in the Plan proved highly effective, ensuring DoS controls were implemented and verified. However, roadmap/plan scope misalignment (WebSocket vs gRPC) caused initial friction, and the release documentation step was skipped/incomplete despite deployment success.
**Focus**: Process improvements for Roadmap alignment and Artifact lifecycle management.

## Timeline Analysis
| Phase | Planned Duration | Actual Duration | Variance | Notes |
|-------|-----------------|-----------------|----------|-------|
| Planning | 0.5d | 0.5d | 0 | Fast, but required revision for Roadmap alignment |
| Analysis | 0.25d | 0.5d | +0.25d | Two analysis cycles (005 and 007) required to clarify stop conditions |
| Critique | 0.25d | 0.25d | 0 | Effective at catching scope mismatch |
| Implementation | 0.5d | 0.5d | 0 | Smooth; Python/FastAPI implementation was straightforward |
| QA | 0.25d | 0.25d | 0 | Passed; included Security/DoS verification |
| UAT | 0.1d | 0.1d | 0 | Passed; validated value statement |
| **Total** | ~2d | ~2d | 0 | Very efficient flow |

## What Went Well (Process Focus)
### Quality Gates
- **Security-First Planning**: The "Security Requirements (Implementation Gate)" section in Plan 005 was a standout success. By listing specific controls (Idle Timeout, Max Chunk Size, Origin Allowlist) *before* implementation, the Implementer built them in naturally, and QA had a clear checklist to verify (Scenario 2). This prevented the typical "bolt-on security" pattern.

### Agent Collaboration Patterns
- **Critique as Scope Guard**: The Critic correctly identified that the Roadmap promised "WebSocket + gRPC" while the Plan delivered only "WebSocket". Instead of letting this drift pass, the Critic blocked (Verdict: Revision Required), forcing a Roadmap update to reflect the "Phase 1" reality. This kept the roadmap honest.
- **UAT vs QA Distinction**: QA focused on technical correctness (buffer limits, protocol handling), while UAT focused on "Client Developer" value (end-to-end ingestion). This separation ensured both stability and utility were verified.

## What Didn't Go Well (Process Focus)
### Workflow Bottlenecks
- **Roadmap-Plan Scope Mismatch**: The Planner wrote a plan for "Phase 1" while the Roadmap still described the full Epic. This required a backward loop (Plan -> Critique -> Roadmap Update -> Plan Revision) that could have been avoided if the Analyst had reconciled the Roadmap scope *before* Planning began.

### Artifact Hygiene
- **Forward Reference to Missing Artifacts**: The Plan referenced `agent-output/qa/005-ingress-gateway-qa.md` before it existed. The Critique flagged this as "missing artifact / ownership violation". This confuses the workflow—Implementers don't know if they should create the file or read it.
- **Bifurcated Analysis**: We had `005-ingress-gateway-analysis` and `007-ingress-gateway-depth-analysis` for the same feature. This non-sequential numbering (skipping 006) complicates traceability. Analysis iterations should likely stay bonded to the Plan ID (e.g., update 005 or use 005-depth).
- **Missing Release Artifact**: Although the user declared "Release complete", the standard `agent-output/releases/v0.3.0.md` artifact was not found in the workspace. This means the release audit trail is incomplete.

## Agent Output Analysis
### Changelog Patterns
**Total Handoffs**: ~6 (Analyst -> Planner -> Critic -> Implementer -> QA -> UAT)
**Handoff Chain**: Standard linear flow, with one loop-back at Critique for scope alignment.

### Issues and Blockers
**Issue Pattern Analysis**:
- **Scope Ambiguity**: The primary blocker was "Does v0.3.0 include gRPC?". This was resolved by splitting the Epic into Phases.
- **Protocol Specificity**: Initial plan over-specified the protocol (JSON formats), which Critique correctly flagged as "Implementation Detail". The fix was to move contract shapes to QA/Integration docs.

## Unified Memory Contract
- **Retrieval**: Agents successfully used memory to find the "Sentinel Message" pattern and existing Kafka topic names.
- **Storage**: QA and UAT verified the `AudioInputEvent` contract was preserved, maintaining the "Walking Skeleton" integrity.

## Recommendations for Improvement

### 1. Pre-Plan Roadmap Check
**Problem**: Planner writes a plan that contradicts the Roadmap's Acceptance Criteria, causing Critique rejection.
**Solution**: The **Analyst** (or Planner in pre-work) must explicitly validate that the *current* Roadmap entry matches the *intended* Plan scope. If not, the Roadmap must be updated *first* (via a "Roadmap alignment" task) before the Plan is drafted.

### 2. Stubbing QA Artifacts
**Problem**: Plans reference QA docs that don't exist, leading to "Missing Artifact" findings.
**Solution**: When a Plan is Approved, the next step (Implementation or QA prep) should immediately **scaffold** the `qa/NNN-*.md` file as a stub. Alternatively, the Plan should list the *requirements* for the QA Doc, rather than linking to it as a static asset.

### 3. Release Verification Step
**Problem**: Release marked complete but artifact missing.
**Solution**: The Release Agent instructions must require *verifying* the existence/commit of the `releases/vX.Y.Z.md` file before declaring "Deployment Complete".

## Technical Debt Incurred
- **Deferred gRPC**: The "Phase 1" decision leaves gRPC support as a debt item. It requires a dedicated Backlog Item/Epic to ensure it isn't lost.
- **Protocol Customization**: The custom JSON handshake/sentinel protocol (vs standard verbs) is a mild form of contract debt that requires bespoke client logic.

## Follow-Up Actions
- [ ] **Roadmap Agent**: Ensure Epic 1.5 is marked "Phase 1 Delivered" and a new Epic/Story is created for "Phase 2 (gRPC)".
- [ ] **Release Agent**: Retroactively create/restore `agent-output/releases/v0.3.0.md` to complete the audit trail.
- [ ] **Docs Agent**: Document the WebSocket Sentinel/Handshake interaction in `docs/INTERFACES.md` so client developers don't have to read `protocol.py`.

## Metrics
**Lines of Code Changed**: ~450 (Service implementation + Tests)
**Files Modified**: ~15
**Tests Added**: 8 Unit, 2 Integration, 1 Load
**Escalations**: 0 (Scope mismatch handled via Critique)
