---
ID: 028
Origin: 028
UUID: 9c2e6d41
Status: Active
---

# Architecture Findings 028: Kafka Consumer Group Recovery Hardening (Plan 028)

## Changelog
| Date | Change | Rationale |
|------|--------|-----------|
| 2026-01-28 | Initial architecture review of Plan 028 | Validate architectural alignment and require boundary/telemetry fixes before implementation. |
| 2026-01-28 | Re-review after plan revision | Confirm Plan 028 addresses MUST items; upgrade verdict to APPROVED. |
| 2026-01-28 | Re-review after Analysis 030 parity finding | Confirm measurement/evidence requirements include image/workspace parity to avoid stale-image false conclusions. |

## Verdict
**APPROVED**

Plan 028 is directionally aligned with the platform’s **Epic 1.9 startup resilience boundary** and the “shared-lib must remain thin” constraint, and it targets a real, measured reliability risk (post-restart consumer-group recovery tail latency).

Plan 028 now satisfies the architectural requirements below (recorded for traceability).

## Architectural Alignment (What’s Good)
- **Correct problem framing**: Treats the restart tail as a Kafka consumer-group coordination/recovery issue, not “slow inference”.
- **Boundary-respecting intent**: Keeps resilience behavior at the service boundary and limits shared-lib to a thin helper.
- **Cross-service standardization**: Reasonable DRY use-case (config + telemetry field naming) to prevent drift across VAD/ASR/Translation/TTS.
- **Diagnosability-first**: Adds assignment-acquired and input-received timestamps, matching the platform’s observability priority.

## Required Changes (MUST) — Status

### MUST-1: Keep shared-lib helper pure and non-orchestrating
Status: **SATISFIED** (Plan 028 now constrains shared-lib to constants + a pure builder; services parse env vars.)

**Requirement**:
- Shared-lib MAY provide **constants + a pure config builder** (e.g., merge defaults with explicit overrides).
- Shared-lib MUST NOT:
  - read environment variables directly (prefer service-owned settings parsing),
  - perform I/O,
  - sleep/retry/backoff, or
  - create/manage Kafka client instances.

**Rationale**: Preserves the architecture decision that shared artifacts remain thin and do not own runtime orchestration. Services still “own” operational policy and deployment concerns.

### MUST-2: Always-on telemetry must be low-volume (no per-message INFO logs)
Status: **SATISFIED** (Plan 028 defines Normal vs Debug telemetry and removes always-on per-message logging.)

**Requirement (Normal vs Debug)**:
- **Normal (always-on, low volume)** MUST include:
  - `consumer_config_effective` log once at startup (sanitized)
  - `consumer_assignment_acquired` on assignment changes/rebalances
  - `consumer_first_input_received` after startup AND after each new assignment (topic/partition/offset/message_ts + `correlation_id` when available)
- **Debug (opt-in)** MAY include:
  - per-message consume logs, but gated behind an env flag and/or sampled.

**Rationale**: Observability is architecture, but uncontrolled log volume is an availability and cost risk.

### MUST-3: Standardize env var naming and field schema across services
Status: **SATISFIED** (Plan 028 defines canonical `KAFKA_CONSUMER_*` env vars and canonical structured event names/fields.)

**Requirement**:
- Define a single set of env vars for consumer tuning (same names across services), with safe defaults and documented tradeoffs.
- Define a single set of structured log fields for the three required telemetry events above, and reuse across services.

**Rationale**: Prevents drift and makes cross-service correlation possible without per-service parsing logic.

### MUST-4: Smoke-test “make it pass” must not mask regressions
Milestone 4’s acceptance criterion (“default local smoke runs no longer fail…”) can inadvertently hide real regressions.

**Requirement**:
- Smoke tooling MUST have explicit modes (or explicit parameters) that separate:
  - **steady-state latency** validation vs
  - **cold-start / post-restart recovery** validation.
- Default local behavior SHOULD target steady-state only (to reduce developer friction), but the cold-start scenario MUST remain a first-class check.

Status: **SATISFIED** (Plan 028 now requires explicit steady-state vs cold-start modes and preserves cold-start as a first-class check.)

### MUST-5: Measurement evidence MUST include image/workspace parity proof
Status: **SATISFIED** (Plan 028 Milestone 1 now requires parity verification before collecting baseline/post-change evidence.)

**Requirement**:
- Any baseline or post-change tail-latency measurements MUST be taken against containers/images that match the workspace code under test.
- Evidence artifacts MUST include enough information to confirm parity (e.g., rebuilt/recreated containers plus effective config telemetry from the running service).

**Rationale**: Stale Docker images can produce timing artifacts that look like regressions or mask improvements, making the plan’s evidence non-actionable.

## Recommended Improvements (SHOULD)

### SHOULD-1: Prefer “minimally invasive” Kafka tuning first
Tune the smallest set of parameters that address the measured tail (likely session/membership behavior). Avoid speculative changes across unrelated knobs.

### SHOULD-2: Evaluate static membership carefully
Static membership (`group.instance.id`) may reduce disruptive rebalances, but it introduces deployment identity requirements:
- single replica local-compose is straightforward
- multi-replica requires unique, stable instance IDs

Plan should treat this as optional with clear constraints.

### SHOULD-3: Document at-least-once implications explicitly
Changing consumer liveness parameters can change duplicate/replay behavior around restarts. Ensure the plan explicitly reaffirms:
- MVP semantics remain **at-least-once**
- outputs may be duplicated

## Explicit Non-Goals (Confirmed)
- No schema changes.
- No “change group.id on restart” workaround (would create offset/state chaos).
- No exactly-once semantics.

## Architecture Consistency Check (Decisions Referenced)
- Consistent with [Startup resilience policy boundary](agent-output/architecture/system-architecture.md#decision-startup-resilience-policy-boundary-schema-registry-readiness) (service-owned bounded behavior; shared-lib thin).
- Consistent with [Service startup resilience invariant](agent-output/architecture/system-architecture.md#decision-service-startup-resilience-is-a-platform-invariant-epic-19).

## Plan Update Checklist (What to change in Plan 028)
- Completed in Plan 028 revision dated 2026-01-28.

## Architecture Acceptance Checklist (QA/UAT Gate)
Use this checklist as the “architecture compliance” gate before QA/UAT is treated as meaningful.

### A. Boundary (Shared-lib vs Service)
- [ ] Shared-lib provides only **pure** consumer tuning helpers (constants/builder/validator); no env reads, no I/O, no Kafka client construction, no sleeps/retries/backoff.
- [ ] Each service owns env parsing + validation and passes explicit overrides into the shared-lib helper.

### B. Telemetry (Normal vs Debug)
- [ ] Always-on logs are low-volume (no per-message INFO logs in default mode).
- [ ] Each consuming service emits:
  - [ ] `kafka_consumer_config_effective` once at startup (allowlisted values only)
  - [ ] `kafka_consumer_assignment_acquired` on assignment changes
  - [ ] `kafka_consumer_first_input_received` once after startup and after assignment changes
- [ ] Any per-message diagnostics are behind an explicit opt-in flag and/or sampling.

### C. Configuration Contract
- [ ] All services use the canonical `KAFKA_CONSUMER_*` env vars (same names across services).
- [ ] Validation guardrails enforced (bounds + type checks), including:
  - [ ] `session.timeout.ms > heartbeat.interval.ms`
  - [ ] `max.poll.interval.ms > session.timeout.ms`
  - [ ] assignment strategy allowlist
- [ ] Static membership remains opt-in; if enabled, `group.instance.id` is required and uniqueness constraints are documented.

### D. Evidence Integrity (Measurement Parity)
- [ ] Baseline/post-change measurements include proof the running containers match the workspace code (rebuild/recreate + effective config telemetry).
- [ ] Evidence captures timestamps/deltas sufficient to attribute tail latency to assignment vs processing.

### E. Smoke Governance
- [ ] Smoke tooling keeps **steady-state** vs **cold-start/restart recovery** checks as distinct modes.
- [ ] Default developer flow targets steady-state, but cold-start remains a first-class check.
