# Architecture Findings 001: Shared Infrastructure & Contract Definition (Epic 1.1)

**Related Plan (if any)**: agent-output/planning/001-shared-infrastructure-plan.md
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-15 | Roadmap/Security/Analysis | Architecture review | Fit check of plan vs architecture invariants; identified required changes before implementation |

## Context

- What is being assessed: The plan for Epic 1.1 (Kafka + Schema Registry + shared contract artifact/library).
- Affected modules/boundaries:
  - Shared infrastructure: Kafka, Schema Registry
  - Shared contract artifact: Avro schemas + envelope (+ optional generated bindings)
  - Cross-cutting: correlation tracking and schema governance

## Findings

### Must Change

1. **Resolve canonical event naming inconsistency**
   - Problem: Roadmap AC calls the audio ingress schema `AudioProcessingEvent` while the plan defines `AudioInputEvent`.
   - Requirement: Choose **one canonical name** and apply it consistently in:
     - Shared `.avsc` files
     - Topic taxonomy and examples
     - Plan text
     - Future service implementations
   - Rationale: Naming drift is a primary integration failure mode and creates schema-subject ambiguity.

2. **Pin and document the contract strategy and topic taxonomy explicitly (Option A)**
   - Problem: The architecture requires standardization (Option A), but the plan does not specify the exact topic names / schema subject strategy.
   - Requirement: Add a short “Contract Canon” subsection in the plan with:
     - Canonical topic names (e.g., `speech.audio.ingress`, `speech.asr.text`, `speech.translation.text`)
     - Schema Registry subject naming rule (TopicNameStrategy vs RecordNameStrategy) and rationale
   - Rationale: Without this, services can’t independently implement consumers/producers without re-coordination.

3. **Constrain the shared library to the permitted boundary**
   - Architecture rule: Shared artifact MUST NOT contain business logic and MUST NOT grow into a cross-service SDK.
   - Risk in plan: “Producer/Consumer Wrapper” can become a de-facto platform SDK, creating hidden coupling.
   - Requirement: Tighten scope language:
     - Allowed: schema loading, serialization/deserialization, envelope population helpers, correlation ID helpers, size checks.
     - Forbidden: service-specific topic routing, retries, backoff policies, domain validation, model selection, workflow orchestration.

4. **Resolve the “REQUIRES ANALYSIS” on message size policy before implementation**
   - Problem: Plan leaves max message/header size as an open question, but size limits drive schema decisions (inline audio vs references) and broker config.
   - Requirement: Decide (and record in plan) at least:
     - Max Kafka message size (dev)
     - Max allowed audio payload size for the ingress event
     - Strategy for larger-than-max audio (reference/URI pattern)
   - Rationale: This is a hard architectural constraint; deferring it increases rework and breaks the “hard MVP” scope control.

### Risks

- **Governance risk**: Schema evolution will become chaotic without explicit subject naming + compatibility policy enforcement.
- **Coupling risk**: A shared runtime SDK becomes “distributed monolith” by stealth if wrappers include more than serialization + envelope helpers.
- **Operational risk (MVP)**: If Kafka/SR are accidentally exposed beyond localhost, you create an unauthenticated control plane + data plane.

### Alternatives Considered

- **Adapter layer (Option B)**: Allow each service to keep local schemas/topics and add an adapter.
  - Rejected for MVP: adds a new moving part and increases failure surface.

- **Schema-only shared artifact** (no shared Python lib)
  - Pros: zero runtime coupling.
  - Cons: slows implementation and increases duplication in early MVP.
  - Recommendation: acceptable later; for MVP, allow shared lib but keep it extremely narrow.

## Integration Requirements

- Schema Registry compatibility MUST be set to `BACKWARD` (or stricter) for MVP subjects.
- Event envelope MUST include: `event_id`, `correlation_id`, `timestamp`, `event_type`, `source_service`.
- Kafka + Schema Registry MUST be local-only / private network for MVP dev.

## Consequences

- You will spend a small amount of time up-front choosing canonical naming and topic/subject strategy, but you avoid exponential integration churn across ASR/Translation later.

## Handoff to Planner/Implementer

**From**: Architect
**Artifact**: agent-output/architecture/001-shared-infrastructure-architecture-findings.md
**Status**: APPROVED_WITH_CHANGES
**Key Context**:
- Epic 1.1 is architecturally sound, but only if naming/topic/subject strategy is finalized and the shared library is kept within strict boundaries.

**Recommended Action**:
- Update the plan to incorporate the “Must Change” items, then proceed to implementation.
