# Architecture Findings 002: Shared Infrastructure Plan (Epic 1.1) — Post-Outcome Fit Check

**Date**: 2026-01-15
**Related Plan**: agent-output/planning/001-shared-infrastructure-plan.md
**Related Roadmap**: agent-output/roadmap/product-roadmap.md (Epic 1.1 marked Delivered)
**Related Prior Findings**: agent-output/architecture/001-shared-infrastructure-architecture-findings.md

**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Trigger | Summary |
|------|---------|---------|
| 2026-01-15 | Roadmap/Epic outcomes updated | Re-validated Plan 001 against the architecture master; identified remaining governance/documentation deltas and clarified invariants for downstream epics |

## Scope of Review
Architectural fit check of Plan 001 against:
- agent-output/architecture/system-architecture.md (source of truth)
- The updated Epic 1.1 outcomes reflected in the roadmap

Note: Although Plan 001 is marked **DELIVERED**, this review is still valuable as a **gate for re-use** (Epic 1.2+ will directly build on these invariants).

## What Fits Well (No Change Required)
- **System boundaries**: Uses Kafka + Schema Registry as shared infrastructure; keeps services event-coupled only.
- **Contract-first**: Defines envelope fields (`event_id`, `correlation_id`, `timestamp`, `event_type`, `source_service`) aligned with architecture requirements.
- **Topic taxonomy + naming**: Uses `AudioInputEvent` and defines topics + subject naming strategy (TopicNameStrategy), which resolves historical naming drift.
- **Shared library boundary language**: Explicit “allowed vs forbidden” scope for producer/consumer wrappers matches the architecture’s narrow shared-artifact exception.

## Must Change (Required for Architectural Consistency)

1. **Schema Registry compatibility mode must be explicit in the plan**
   - Architecture requires Schema Registry subject compatibility set to `BACKWARD` (or stricter).
   - Required update to the plan: add an explicit step under Infra bring-up / Schema governance:
     - “Set default or per-subject compatibility to `BACKWARD` for MVP subjects.”

2. **Resolve internal inconsistency in the message-size decision**
   - In Plan 001, the “Assumptions & Open Questions” section states audio payloads >1.5MB “must use reference/URI”, but the “Contract Canon” section states larger audio is **rejected** in MVP.
   - Required update to the plan: pick one MVP behavior and state it consistently.
   - Architecture recommendation for v0.1.0: **reject** >1.5 MiB inline audio (defer reference/URI pattern to a later epic).

## Should Change (Strong Recommendations)

1. **Correct the 2MB audio duration approximation**
   - Plan text claims 2MB is “approx 2 mins of raw 16hz mono PCM”; this is materially incorrect and will mislead later design discussions.
   - Recommendation: replace with an accurate statement or remove the duration estimate.

2. **Tighten shared artifact definition in the master contract description**
   - Plan uses the name `speech-lib`. Architecture master allows generated bindings + narrow helpers.
   - Recommendation: ensure the shared artifact is described as “schemas + generated bindings + serialization/envelope helpers only” to avoid SDK creep.

## Architecture Master Updates
The following architecture master updates were applied as part of this review (to keep the system source-of-truth consistent):
- Pinned canonical audio-ingress name to `AudioInputEvent` and documented topic taxonomy.
- Updated the architecture diagram edge labels to include topic names.

## Integration Requirements (Non-Negotiable)
- All MVP events MUST include `correlation_id`.
- Schema Registry compatibility MUST be `BACKWARD` (or stricter) for MVP subjects.
- Shared contract artifact MUST NOT contain business logic (serialization/envelope/correlation helpers only).

## Consequences for Downstream Epics (1.2+)
- Epic 1.2 service implementations MUST use the pinned topic + schema names from the architecture master.
- Any deviation (renames, topic changes) requires an explicit architecture change entry in system-architecture.md.
