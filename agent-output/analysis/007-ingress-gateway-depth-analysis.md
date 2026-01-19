# Analysis 007: Ingress Gateway Deep Dive

**Date**: 2026-01-19
**Prior Analysis**: [Analysis 006: Research Gaps](agent-output/analysis/006-ingress-gateway-research-gaps.md)
**Plan Referenced**: [Plan 005](agent-output/planning/005-ingress-gateway-plan.md)

## 1. Objective
The previous analysis surfaced four research gaps. This follow-up goes deeper: it defines concrete experiments/tests, clarifies contradictory signals across artifacts (plan vs architecture vs roadmap), and specifies the stop condition for planning handoff.

## 2. Contradictions & New Questions
1. **Architecture vs. Release Scope**: `system-architecture.md` still states the Gateway supports WebSocket/gRPC, but roadmap and plan restrict v0.3.0 to WebSocket. Should architecture maintain this capability note, or should separate release-scoped notes be added? For planning we assume architecture describes long-term capability, but final release sign-off should reference the roadmap's Phase 1 scope.
2. **Sentinel message shape**: Plan references a "structured end-of-stream message" without specifying fields. QA literature needs consistent spec to implement tests and clients. What fields are mandatory vs optional, and how is the message validated?
3. **QA artifact absence**: The plan references `agent-output/qa/005-ingress-gateway-qa.md`, but the file doesn't exist. Without it there is no deterministic verification of Section 3.1 controls or Section 5 validations.
4. **Deferred gRPC timeline**: There is still no backlog item or plan for gRPC, despite plan saying "deferred"; downstream teams may assume it ships with v0.3.0 unless a follow-up epic/backlog entry is defined.

## 3. Deep Investigations
### 3.1 Sentinel Message / EOF Detection
- **Hypothesis**: Clients will either close WebSocket or send JSON `{"event":"done"}`. The plan already mentions JSON sentinel but lacks schema.
- **Investigation**: Draft a minimal spec covering required fields: `event`, optional `sequence`, optional `correlation_id` (server overrides). Define handshake ack message structure (e.g., `{"correlation_id":"...","status":"ready"}`) and specify any preconditions (must be valid UTF-8, no binary). Record this spec within the QA artifact (once created) so client SDKs can rely on it.
- **Verification Steps**: Build two prototypes (browser-based WebSocket and CLI streaming) that send the sentinel and confirm Gateway completes audio buffering and publishes event. Capture logs to ensure `correlation_id` returned matches plan.

### 3.2 Buffer/Concurrency Limits
- **Gap**: Plan sets `MAX_BUFFER = 1.5 MiB` and `MAX_CONCURRENT = 10`. Without actual load tests, these numbers are theoretical.
- **Approach**: Implement a lightweight load harness (Python/asyncio) to simulate 12 concurrent clients streaming synthetic PCM frames at 16kHz for 10 seconds. Monitor container memory, Kafka publish success, and latency. If memory usage nears limit or chunk drop occurs, adjust configuration: e.g., reduce `MAX_CHUNK_SIZE` or distribute load across multiple gateway instances. Document final thresholds in QA artifact and plan's constraints section (update `constraint (Chunk Limits)` accordingly).

### 3.3 QA Artifact Creation
- **Requirement**: The plan references QA artifact to verify Section 3.1 and Section 5. Without it, gating is impossible.
- **Work**: Create `agent-output/qa/005-ingress-gateway-qa.md`. Structure it with sections: (1) Functional validation (WebSocket handshake, correlation_id propagation), (2) Security controls (timeouts, chunk limits, origin allowlist, log hygiene), (3) Load/performance checks, (4) Acceptance criteria mapping to plan sections. Link each test to the plan for traceability.
- **Stop Condition Contribution**: QA sign-off will be this artifact plus evidence (logs, metrics). Planning can proceed once QA artifact exists and the team agrees on pass/fail criteria.

### 3.4 gRPC Follow-up Planning
- **Observation**: Both plan and roadmap mention gRPC deferral, but there is no backlog entry. Without follow-up, there is risk of forgetting or duplicating work.
- **Next Step**: Create a short backlog note/placeholder (e.g., in `agent-output/planning/` or roadmap backlog) titled "Epic 1.5b — Ingress Gateway gRPC" capturing the acceptance criteria (gRPC endpoint, streaming contract, authentication). Link it from QA artifact or plan to ensure visibility.

## 4. Findings Summary
- No new architectural blockers were found; the plan remains focused on WebSocket delivery.
- Actionable research tasks remain: sentinel contract, load verification, QA artifact creation, and gRPC backlog documentation.
- Deeper investigation clarifies the stop condition: planning can proceed once QA artifact exists, load tests validate constraints, and gRPC deferral is explicitly logged for future follow-up.

## 5. Recommendations
1. Complete the sentinel/handshake spec in QA artifact and document any expected client behavior (connection order, ack, error responses).
2. Execute load tests to prove buffer/concurrency defaults, then update plan constraints with measured values (if adjustments needed). Save results to QA artifact.
3. Publish `agent-output/qa/005-ingress-gateway-qa.md` with traceable tests for every security control and validation requirement.
4. Create a recorded follow-up item (possibly `agent-output/planning/006-ingress-gateway-grpc-plan.md` placeholder or roadmap backlog note) so the deferred gRPC work has a home.

## 6. Stop Condition
Planning can hand off to implementation when:
- QA artifact exists and references Plan 005 sections + Security 005 controls.
- Buffer/concurrency limits are verified (log evidence or documented adjustments) and reflected in the plan/QA artifact.
- The gRPC follow-up backlog item is documented so scope deferral is auditable.
