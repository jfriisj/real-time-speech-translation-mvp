# Architecture Findings 024: Schema Registry Readiness & Service Resilience (Plan 011)

**Related Plan (if any)**: agent-output/planning/011-schema-registry-readiness-plan.md
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | Planner/Implementer | Architecture review | Plan is directionally correct but violates shared-contract boundary by proposing shared-lib retries; requires moving resilience policy to service startup + compose health gating. |

## Context

- What is being assessed:
  - Plan 011 proposes fixes to stop `translation-service` (and potentially others) from crashing during schema registration when Schema Registry is not yet accepting connections.
- Affected modules/boundaries:
  - Shared contract artifact / `speech-lib` boundary (must remain narrow; no orchestration policies).
  - Service startup sequence and infra readiness (Schema Registry availability).
  - Docker Compose orchestration (readiness vs container start ordering).

## Findings

### Must Change

1. **Do not add retry/backoff policy to the shared contract artifact**
   - The architecture explicitly forbids retries/backoff policies in the shared artifact (see: shared-lib boundary constraints in prior findings).
   - Plan 011 WP1 currently proposes implementing retry/backoff inside `SchemaRegistryClient` in shared-lib; this violates the “no cross-service SDK” guardrail.
   - Required change:
     - Keep `SchemaRegistryClient` as a thin HTTP adapter (current behavior).
     - Implement controlled retry/backoff at the service boundary (e.g., in `translation-service` startup around schema registration), not in shared-lib.

2. **Add an explicit Schema Registry readiness gate for local compose**
   - `depends_on` is not a readiness mechanism; it only orders container start.
   - Required change:
     - Add a `healthcheck` to the `schema-registry` service and gate service startup on readiness (preferred in local dev).
     - OR implement a service-side wait loop with a bounded timeout (still required even with healthcheck for robustness).

3. **Bounded failure behavior must be explicit**
   - A “wait gracefully” approach must not become an infinite hang.
   - Required change:
     - Define a bounded maximum wait time and exit behavior (fail-fast after N seconds with a clear fatal log), so orchestration can restart or operators can diagnose.

4. **Keep scope to Schema Registry (do not broaden to Kafka readiness in this change)**
   - Plan text introduces “critical infrastructure (Schema Registry, Kafka)”. This risks scope creep into generic infra orchestration.
   - Required change:
     - Constrain the plan’s contract language and work packages to Schema Registry readiness only.
     - If Kafka readiness needs similar handling, track as a follow-up (separate plan) with explicit architecture review.

### Risks

- **Hidden coupling risk**: putting retry policy into shared-lib creates a de facto platform SDK and makes cross-service behavior harder to reason about and test.
- **Masking real outages**: aggressive retries can hide persistent misconfiguration; bounded timeout + clear logs are mandatory.
- **Inconsistent service behavior**: if each service implements its own wait loop differently, startup becomes unpredictable; mitigate via a small, consistent pattern repeated per-service (not via shared-lib).

### Alternatives Considered

- **Compose-only healthcheck gating**
  - Pros: simple, local-dev friendly.
  - Cons: does not protect against mid-run SR instability or non-compose deployments.
  - Verdict: good as a local-dev improvement, but still pair with bounded startup retries in services.

- **Service-only retry/wait loop (no compose healthcheck)**
  - Pros: works in any deployment mode.
  - Cons: slower/ noisier startup UX; still acceptable.

- **Sidecar / entrypoint “wait-for-sr” script**
  - Pros: keeps service code unchanged.
  - Cons: adds operational glue per service; can drift and is harder to test.

## Integration Requirements

- Shared contract artifact (`speech-lib`) MUST remain within allowed scope: schemas/envelope/bindings/serialization/correlation helpers only; no workflow orchestration or retry policy.
- Services MUST log clearly during startup:
  - “Waiting for Schema Registry” vs “Schema Registry ready; registering schemas”.
- Startup waiting MUST be bounded and must exit with a non-zero code on timeout to enable orchestrator restart.

## Consequences

- Slightly longer cold-starts (by design) but materially higher reliability and fewer “silent pipeline” failures.
- Resilience behavior becomes explicit at the service boundary, preserving the architecture’s decoupling rules.

## Handoff

## Handoff to Planner/Implementer

**From**: Architect
**Artifact**: agent-output/architecture/024-schema-registry-readiness-plan-architecture-findings.md
**Status**: APPROVED_WITH_CHANGES
**Key Context**:
- Fix is necessary and fits the system, but retry/backoff policy MUST NOT live in shared-lib.
- Use compose healthchecks and/or service startup bounded wait loops to eliminate SR race conditions.

**Recommended Action**: Update Plan 011 to move retries into service startup (not shared-lib), add a schema-registry readiness gate, and explicitly bound the wait/exit behavior before implementation.
