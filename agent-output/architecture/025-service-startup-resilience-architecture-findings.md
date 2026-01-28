# Architecture Findings 025: Service Startup Resilience (Epic 1.9)

**Related Plan (future)**: agent-output/planning/025-service-startup-resilience-plan.md
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | Roadmap/Planner | Pre-planning architecture assessment | Approves “resilience first” resequencing; defines platform-level startup resilience invariant and boundaries (no shared-lib orchestration), plus minimal required readiness gates for SR/Kafka. |

## Context

Epic 1.9 exists to eliminate platform bring-up race conditions that block reliable development and end-to-end tests.

- Primary symptoms (observed / expected):
  - Services crash-loop (or exit) when **Schema Registry** is not yet reachable during schema registration.
  - E2E tests become flaky because the platform does not converge deterministically after `docker compose up`.
- Why this matters now:
  - Epics 1.8 (artifact persistence rollout) and 1.7 (TTS) add more moving parts and longer pipelines; without stable startup, failures become hard to attribute.

## Dependency Implications (Epic Ordering)

- Epic 1.1 (Kafka + Schema Registry + contract) is a prerequisite for all microservices.
- Epic 1.9 is a **platform invariant** that should be delivered before expanding the pipeline further.
- Architectural dependency order for stable E2E:
  - **Epic 1.9 (Resilience)** → **Epic 1.8 (Persistence Rollout)** → **Epic 1.7 (TTS)**

## Findings

### Must Have (Architecture Requirements)

1. **Service-boundary readiness gates (bounded) for Schema Registry**
   - Each service that registers/uses Avro schemas MUST implement a bounded wait for Schema Registry readiness *at startup*.
   - Wait MUST be bounded (timeout) and MUST exit non-zero on timeout.
   - Logs MUST clearly indicate: waiting → ready → registering schemas.

2. **Service-boundary readiness gates (bounded) for Kafka connectivity**
   - Each service that consumes/produces Kafka events MUST verify broker connectivity *before entering its main processing loop*.
   - This is not “exactly-once” or durability logic; it is a startup convergence mechanism.

3. **Local-dev orchestration should help, but cannot be the only mechanism**
   - Docker Compose healthchecks (e.g., Schema Registry “/subjects” reachable) MAY reduce local flakiness.
   - Services MUST still be robust when healthchecks are absent (Kubernetes, CI, manual runs).

4. **Consistency across services is required (but not via shared-lib orchestration)**
   - All services MUST follow the same conceptual pattern (same phases, same timeout semantics), to keep operations predictable.

### Must Not Do (Boundary Protection)

1. **Do not implement retry/backoff policy inside the shared contract artifact (`speech-lib`)**
   - The shared artifact must remain schemas/envelope/bindings/serialization/correlation helpers only.
   - Embedding orchestration/retry policies turns it into a platform SDK and violates existing architectural guardrails.

2. **Do not expand scope into “general resilience”**
   - Epic 1.9 is specifically about deterministic startup convergence.
   - Circuit breakers, DLQs, exactly-once semantics, multi-broker failover are out of scope.

### Failure Mode & Observability Requirements

- Startup waits MUST:
  - Use truncated exponential backoff (or fixed interval) with jitter permitted.
  - Emit periodic INFO logs while waiting (rate-limited).
  - Emit a single ERROR/FATAL on timeout with actionable diagnostics (URLs, elapsed time, next steps), then exit non-zero.
- Services MUST NOT hang indefinitely.

### Configuration Contract (Cross-Service)

To keep behavior consistent without introducing a shared orchestration library, standardize environment variables:

- `STARTUP_MAX_WAIT_SECONDS` (default: 60; acceptable range: 30–180)
- `STARTUP_INITIAL_BACKOFF_SECONDS` (default: 1)
- `STARTUP_MAX_BACKOFF_SECONDS` (default: 5–10)

(Exact naming can vary, but MUST be consistent across services once chosen.)

## Alternatives Considered

- **Compose-only readiness (`depends_on: condition: service_healthy`)**
  - Pros: simple, great for local dev.
  - Cons: not portable; does not cover non-compose or mid-run dependency resets.
  - Decision: allowed as an optimization, not as the only safeguard.

- **Shared “wait-for-deps” helper in shared-lib**
  - Pros: deduplicates code.
  - Cons: violates shared-lib boundary (becomes orchestration SDK).
  - Decision: rejected.

- **Entry-point scripts per container**
  - Pros: keeps app code unchanged.
  - Cons: drifts per-service; harder to test; less portable.
  - Decision: acceptable only if service-code changes are infeasible, but still must preserve bounded behavior and clear logs.

## Integration Requirements

- Readiness gates must occur before:
  - Schema registration calls
  - Kafka consumer subscription loops
- Exit semantics:
  - Timeout MUST exit non-zero so an orchestrator can restart.
- Documentation:
  - Each service must document its startup readiness behavior in its implementation doc and in the Epic 1.9 plan (when created).

## Consequences

- Slightly slower cold-start, materially improved determinism.
- E2E tests become attributable (failures are real pipeline issues, not startup races).
- Preserves architecture invariant: shared contract artifact is not an SDK.

## Handoff

- Epic 1.9 plan MUST:
  - Define the canonical readiness gate phases and the exact env var names.
  - Include acceptance criteria demonstrating deterministic startup convergence (e.g., N repeated compose bring-ups with no crash loops).
  - Apply the pattern across Gateway/VAD/ASR/Translation/TTS (as applicable), not only Translation.
