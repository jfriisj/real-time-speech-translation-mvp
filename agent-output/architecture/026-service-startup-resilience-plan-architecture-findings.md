# Architecture Findings 026: Service Startup Resilience (Plan 025)

**Related Plan (if any)**: agent-output/planning/025-service-startup-resilience-plan.md  
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | Planner/Implementer | Pre-implementation architecture review | Plan direction fits the architecture (service-boundary bounded readiness gates). Must fix plan defects and tighten readiness gate/compose healthcheck strategy to avoid drift and ensure deterministic convergence across services. |

## Context

- What is being assessed:
  - Plan 025 proposes platform-wide startup readiness gating for Schema Registry + Kafka to eliminate crash loops and flaky E2E.
- Architecture baseline constraints (system-architecture.md):
  - Startup resilience is a platform invariant (Epic 1.9).
  - Readiness gates MUST be at the service boundary; shared-lib MUST remain thin (no orchestration/retry policy).
  - Waiting MUST be bounded, diagnosable, and exit non-zero on timeout.

## Findings

### Approved Direction

- The overall approach is architecturally correct:
  - service-level bounded readiness gates for **Schema Registry** and **Kafka broker connectivity**
  - Compose healthchecks as a local-dev optimization, not a hard dependency
  - No shared-lib orchestration helper

### Must Change (Required Plan Revisions)

1. **Fix Plan 025 document integrity issues (blocking)**
   - The plan currently contains garbled/duplicated sections (truncated Scenario B, duplicated acceptance criteria blocks).
   - This is a governance risk: implementers will interpret different acceptance criteria.
   - Required change: repair sections 5–6 so they are coherent, single-sourced, and unambiguous.

2. **Align WP1 (Compose healthchecks) with current repository reality**
   - `schema-registry` already has a healthcheck implemented using shell `/dev/tcp` HTTP probing.
   - The plan text still specifies `curl`-based healthcheck commands, which may not exist in the image and conflicts with the plan’s own “do not add packages” constraint.
   - Required change:
     - State “keep existing Schema Registry healthcheck unless there is a concrete reason to change it.”
     - For Kafka, define a healthcheck approach that is compatible with the chosen image tooling OR explicitly mark Kafka healthcheck as optional and rely on service-side gating.

3. **Make Kafka readiness gating consistent across services (compose + service)**
   - Today, services depend on Kafka `service_started` in compose. That is not readiness.
   - Required change:
     - Either add a Kafka healthcheck and switch `depends_on.kafka.condition` to `service_healthy`, OR
     - Keep compose as-is but make service-side Kafka gating mandatory and explicit (and do not promise `service_healthy` in the plan).

4. **Standardize the startup-gate configuration contract**
   - Architecture requires consistent behavior across services, but Plan 025 only defines two env vars.
   - Required change: explicitly define a minimal, consistent config set across services:
     - `STARTUP_MAX_WAIT_SECONDS`
     - `STARTUP_INITIAL_BACKOFF_SECONDS`
     - `STARTUP_MAX_BACKOFF_SECONDS`
     - `STARTUP_ATTEMPT_TIMEOUT_SECONDS` (per-attempt connect/read timeout)
   - Rationale: avoids drift and ensures bounded behavior is real (not just “overall timeout”).

5. **Define canonical readiness phases and log semantics**
   - Required change: the plan must define the phase order and minimum logs so operators can diagnose quickly.
   - Minimum phases:
     - “Waiting for Schema Registry” → “Schema Registry ready” → “Registering schemas”
     - “Waiting for Kafka” → “Kafka ready” → “Starting consume loop”

### Must Not Change (Guardrails)

- Do not move retry/backoff or readiness orchestration into shared-lib.
- Do not broaden scope into general resilience (DLQ, circuit breakers, exactly-once). Keep this epic focused on deterministic startup convergence.

## Risks

- **Readiness drift**: Compose-only gating tends to diverge from CI/K8s behavior; service-side gating remains mandatory.
- **Implementation drift**: duplicated wait code across services can diverge; mitigate with an explicit plan checklist and shared config names (without creating a shared orchestration library).

## Alternatives Considered

- Compose-only health gating: acceptable local optimization, not sufficient alone.
- Entry-point scripts: acceptable fallback but increases per-service operational glue.
- Shared-lib helper: rejected (violates boundary).

## Integration Requirements

- Readiness gates MUST run before:
  - Schema registration / Avro serializer initialization
  - Kafka consumer subscription / produce loops
- Timeout MUST exit non-zero (no infinite waits).
- Logs MUST avoid secrets and should be rate-limited while waiting.

## Consequences

- Slightly slower cold starts, materially improved deterministic bring-up.
- E2E results become attributable to pipeline behavior rather than startup races.

## Handoff

**Status**: APPROVED_WITH_CHANGES  
**Required Action**: Revise Plan 025 per “Must Change” items above before any implementation begins.
