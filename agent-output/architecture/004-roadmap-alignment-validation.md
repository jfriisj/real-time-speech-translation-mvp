# Architecture Validation 004: Roadmap Alignment

**Date**: 2026-01-15
**Validated By**: Architecture Agent
**Context**: Post-Epic 1.1 Delivery, Pre-Epic 1.2 Kickoff

## Input Artifacts
- **Roadmap**: `agent-output/roadmap/product-roadmap.md` (v0.1.0 Epics 1.1-1.3)
- **Architecture Master**: `agent-output/architecture/system-architecture.md`
- **Recent Findings**: `003-audio-payload-policy-architecture-findings.md`

## Validation Summary
**Verdict**: **FULLY ALIGNED**

The architectural approach defined in `system-architecture.md` (including recent updates to event naming, payload sizing, and schema governance) correctly supports the outcomes defined in the Product Roadmap for Epics 1.2 and 1.3.

## Detailed Checks

### 1. Naming & Taxonomy fit
- **Roadmap Requirement**: Epic 1.1 (Delivered) and 1.2 (Planned) use `AudioInputEvent`.
- **Architecture**: Defines `AudioInputEvent` as the canonical ingress schema and maps it to `speech.audio.ingress`.
- **Status**: ✅ Aligned. (Retrospective 001 naming drift was resolved).

### 2. Payload & Throughput Constraints
- **Roadmap Constraint**: Hard MVP (v0.1.0) prioritizes "Walking Skeleton" over feature breadth.
- **Architecture**: Enforces a 1.5 MiB hard cap on inline audio and rejects larger payloads for v0.1.0. This avoids the complexity of reference-handling (External Storage pattern) which is out of scope for the current roadmap epics.
- **Status**: ✅ Aligned. The constraint prevents scope creep in Epic 1.2.

### 3. Integration Surface (Shared Contract)
- **Roadmap Requirement**: "Shared Python library/module created containing generated classes/models".
- **Architecture**: explicit "Shared Contract Artifact" decision allows this exception to the "no shared code" rule, but strictly bounds it to schemas/envelope/serialization.
- **Status**: ✅ Aligned. The architecture permits the exact deliverable the roadmap assumes.

### 4. Correlation & Observability
- **Roadmap AC**: "Output events contain correct `correlation_id` from input." (Epic 1.2/1.3).
- **Architecture**: Mandates `correlation_id` in the `BaseEvent` envelope and requires preservation across consumers/producers.
- **Status**: ✅ Aligned.

## Risks & Forward-Looking Gaps

### Audio Sizing (Epic 1.2)
- **Risk**: Users might expect to transcribe long files immediately.
- **Mitigation**: The Architecture Findings 003 explicitly reject >1.5MB files for v0.1.0. The Roadmap Owner must manage this user expectation (e.g., "Clip duration limited to ~90s for MVP").

### Schema Governance (Epic 1.2/1.3)
- **Risk**: Parallel development of ASR and Translation might fork schemas.
- **Mitigation**: The `TopicNameStrategy` decision (Architecture 003) forces a rigid subject naming convention, reducing the chance of accidental incompatibility during independent service development.

## Conclusion
The system architecture provides a stable, constrained foundation for executing Epics 1.2 and 1.3. No further architectural changes are required to proceed with planning Epic 1.2.
