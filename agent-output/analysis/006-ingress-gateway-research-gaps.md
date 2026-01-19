# Analysis 006: Ingress Gateway Research Gaps

**Date**: 2026-01-19
**Plan Referenced**: [Plan 005](agent-output/planning/005-ingress-gateway-plan.md)
**Context**: The plan is marked as Approved, but it still lists a handful of assumptions and controls whose fulfillment has not yet been verified by experiment or documentation. This analysis captures the remaining research gaps so the team can close them before implementation begins.

## 1. Methodology
- Reviewed Plan 005, existing analysis (Analysis 005), and critique (Critique 005) to identify assumptions that are currently unmet or undocumented.
- Compared requirements against the updated roadmap (Epic 1.5 Phase 1 WebSocket) to confirm what is and is not in scope.
- Highlighted QA/artifact gaps by scanning the workspace for referenced documents (e.g., `agent-output/qa/005-ingress-gateway-qa.md`).

## 2. Research Gaps & Unverified Assumptions
| Gap | Evidence | Verification Approach |
|-----|----------|------------------------|
| **End-of-stream contract** | Plan assumes clients signal end-of-stream via a connection close or "structured end-of-stream message" (Plan §3). No client-facing API spec or sentinel payload is documented yet. | Draft a concise protocol appendix (WebSocket handshake + sentinel format) and validate with sample clients (browser/websocket, CLI). Capture the signals in the QA artifact so implementations and tests can refer to a single source of truth. |
| **Memory/Concurrency safety** | Plan caps per-connection buffer at ≤1.5 MiB and limits concurrency to 10 connections (Plan §3). These thresholds are derived from Kafka message limits, but there is no empirical validation of how these values behave under load. | Prototype the buffering logic and run an async load test (e.g., 10–15 concurrent clients streaming 1.4 MiB). Measure resident set, buffer allocations, and Kafka publish success/failure. Adjust `MAX_CHUNK_SIZE`/connection caps if memory usage or latency spikes. Document findings in QA artifact. |
| **Security control verification (QA artifact)** | Plan references `agent-output/qa/005-ingress-gateway-qa.md` and promises that Section 3.1 controls will be validated, but the file does not exist. Without it, the QA gate is unverified (Critique 005 M-003). | Create `agent-output/qa/005-ingress-gateway-qa.md` before QA sign-off. Populate it with tests for idle timeout, max session, chunk limit, origin validation, and logs-not-containing-audio. Point to relevant plan sections and trace outputs (logs, metrics). This artifact closes the missing-verification gap. |
| **gRPC follow-up** | Plan defers gRPC support (Plan §1 scope note); the roadmap now explicitly marks gRPC as deferred. However, there is no follow-up epic or backlog ticket documented. | Capture a short follow-up plan or backlog item (Epic 1.5b or note in backlog/roadmap) specifying the gRPC contract so the deferred work resumes with a clear scope. Without it, the future milestone may slip or be misunderstood. |

## 3. Findings Summary
- The plan is functionally ready for WebSocket delivery, but the listed research gaps above must be closed so the implementation, QA, and future gRPC work have documented orchestration points.
- There is no blocking architectural risk; these are mostly validation/documentation gaps.

## 4. Recommendations
1. **Define the WebSocket client handshake** (endpoint path, ack payload, sentinel message) in the QA artifact and/or API doc; share sample payloads with client integrators.
2. **Run a load verification exercise** to confirm buffer/concurrency limits behave as expected and document the results in QA 005 so security/performance claims are evidence-based.
3. **Create the missing QA artifact** and use it as the verification gate referenced in Plan 005, ensuring Section 3.1 controls and Section 5 validations are all traceable.
4. **Document the deferred gRPC follow-up** (roadmap/backlog) so future work picks up with clear acceptance criteria.

## 5. Open Questions
- What exact sentinel message structure should clients send to signal completion (JSON shape, field names, allowed order)?
- Is there appetite to expose a second WebSocket command (e.g., `{"command":"done"}`) in addition to connection close to make EOF detection deterministic?
- Where should the follow-up gRPC work be captured (roadmap epic, backlog item, or issue tracker) so the deferred scope is auditable?