---
ID: 028
Origin: 028
UUID: 4f6b2c1d
Status: Active
---

# Plan 028: Kafka Consumer Group Recovery Hardening (Reduce post-restart tail latency)

## Plan Header
- **Target Release: v0.5.0**
- **Epic Alignment**: Epic 1.9.1 (Service Startup Resilience Hardening)
- **Supports**: Epic 1.7 (TTS) and end-to-end smoke reliability
- **Inputs**: [agent-output/analysis/closed/028-tts-e2e-timeouts-rebalance-latency-analysis.md](agent-output/analysis/closed/028-tts-e2e-timeouts-rebalance-latency-analysis.md), [agent-output/analysis/027-technical-unknowns-analysis.md](agent-output/analysis/027-technical-unknowns-analysis.md), [agent-output/roadmap/product-roadmap.md](agent-output/roadmap/product-roadmap.md)

## Changelog
| Date | Change | Rationale |
|------|--------|-----------|
| 2026-01-28 | Initial plan | Convert Analysis 028 findings into an implementable hardening work package. |
| 2026-01-28 | Standardize across services | Apply the same recovery tuning + telemetry everywhere, using shared-lib only for a thin config helper to reduce duplication without violating architecture boundaries. |
| 2026-01-28 | Architecture revisions | Apply Findings 028: keep shared-lib helper pure (no env/I\O/orchestration), define canonical env/log contracts, and keep always-on telemetry low-volume. |
| 2026-01-28 | Security/compliance revisions | Apply security controls: safe config logging allowlist, no payload logging, bounded/validated tuning knobs, debug gating/sampling, and basic log-retention/privacy posture. |

## Value Statement and Business Objective
As an operator/contributor, I want services to recover Kafka consumption quickly after restarts, so that end-to-end smoke tests and development bring-up are reliable and do not fail due to predictable consumer group stabilization delays.

## Objective
1. Reduce the post-restart “first message processed” tail latency attributable to Kafka consumer group recovery.
2. Make the remaining tail latency diagnosable with low-volume, always-on telemetry (no debug log requirement).
3. Ensure changes preserve the architecture boundary: shared contract artifact remains thin; resilience/tuning lives at the service boundary.
4. Standardize behavior across services to avoid drift and reduce duplicate implementation effort.

## Scope
**In scope**:
- Kafka consumer configuration hardening for faster restart recovery across all pipeline services that consume from Kafka.
- Service logging/telemetry additions that clarify consumer-group assignment and “input received” timestamps.
- Documentation updates to set correct expectations for cold-start vs steady-state behavior.

**Standardization target services** (initial rollout):
- Gateway
- VAD
- ASR
- Translation
- TTS

**Out of scope**:
- Changing event schemas.
- Introducing new orchestration tooling requirements (e.g., mandatory sidecars or new healthcheck binaries).
- Implementing “exactly once” semantics or deduplication.
- Re-architecting topic topology.

## Key Findings (from Analysis 028)
- Immediate publish after restarting `speech-tts-service` can produce ~41–43s end-to-end delay while `synthesis_latency_ms` remains ~2s, indicating a pre-synthesis delay.
- Waiting ~55s after restart before publishing collapses end-to-end latency back to ~2s.
- This is strongly consistent with Kafka consumer group membership/session timeout behavior with a fixed `group.id`.

## Assumptions
- The dominant post-restart delay is due to Kafka consumer group coordinator behavior (membership expiration / rebalance), not model download or inference.
- The platform accepts tuning consumer group parameters to improve restart recovery, provided it does not materially increase false rebalances in normal operation.

## Open Questions
1. **OPEN QUESTION [RESOLVED]**: Apply consumer group recovery tuning across gateway/VAD/ASR/translation/TTS for consistency.
2. **OPEN QUESTION [PARTIALLY RESOLVED]**: Tune conservatively by default; make aggressiveness configurable via env vars with documented tradeoffs.

## Architecture Constraint (Shared-lib usage)
To avoid duplicated code while honoring the platform boundary:
- Shared-lib MAY provide **constants + a pure config builder** for Kafka consumer configuration (e.g., merge pinned defaults with caller-provided overrides).
- Shared-lib MUST NOT:
  - read environment variables directly,
  - perform I/O,
  - create/manage Kafka client instances, or
  - embed workflow behavior such as retry loops, backoff policies, sleeps, or dependency orchestration.
- Services remain responsible for:
  - parsing environment variables into service-owned settings,
  - applying the config to their Kafka clients, and
  - any service-specific readiness/wait behavior.

## Standardization Contracts

### Canonical environment variables (consumer tuning)
To prevent configuration drift, the following environment variables are the **canonical interface** for consumer-group recovery tuning across Gateway/VAD/ASR/Translation/TTS.

- Existing (already used): `CONSUMER_GROUP_ID`
- Add (new, standardized):
  - `KAFKA_CONSUMER_SESSION_TIMEOUT_MS`
  - `KAFKA_CONSUMER_HEARTBEAT_INTERVAL_MS`
  - `KAFKA_CONSUMER_MAX_POLL_INTERVAL_MS`
  - `KAFKA_CONSUMER_PARTITION_ASSIGNMENT_STRATEGY`
  - `KAFKA_CONSUMER_ENABLE_STATIC_MEMBERSHIP` (boolean)
  - `KAFKA_CONSUMER_GROUP_INSTANCE_ID` (optional; if set, must be unique per replica)

Notes:
- Defaults must be safe/conservative.
- “Aggressiveness” tuning must be documented as explicit tradeoffs.

### Canonical structured telemetry events (low-volume)
All target services MUST emit the following low-volume events with consistent field names to enable cross-service correlation.

**Always-on (normal mode)**:
- `kafka_consumer_config_effective` (once at startup)
- `kafka_consumer_assignment_acquired` (on assignment changes)
- `kafka_consumer_first_input_received` (after startup and after assignment changes)

**Debug/opt-in**:
- Per-message consume telemetry MAY be enabled behind an explicit env flag and/or sampling.

Minimum common fields (all events):
- `service_name`
- `timestamp`
- `consumer_group_id`

Event-specific minimum fields:
- `kafka_consumer_assignment_acquired`: `topic`, `partitions`
- `kafka_consumer_first_input_received`: `correlation_id` (when available), `topic`, `partition`, `offset`, `kafka_message_timestamp`

## Security and Compliance Constraints

### Logging safety (mandatory)
- Telemetry MUST be **structured and allowlisted**.
- Telemetry MUST NOT include:
  - event payloads (audio bytes, text content, URIs),
  - Kafka headers beyond what is strictly needed for triage,
  - full dependency endpoints that may embed credentials (future SASL/basic-auth), or
  - environment variable dumps.
- `kafka_consumer_config_effective` MUST log only non-sensitive consumer tuning values (timeouts, assignment strategy, group id, static membership enabled/disabled). It MUST NOT log `bootstrap.servers` or any auth/security config.

### Debug gating and sampling
- Any per-message diagnostics MUST be behind explicit opt-in configuration and/or sampling.
- Default runtime and CI MUST run with debug/per-message logs disabled.

### Configuration validation and bounds
- Services MUST validate `KAFKA_CONSUMER_*` values (type + min/max bounds) at startup and fail fast with clear errors on invalid config.
- Static membership MUST remain opt-in and documented as requiring unique instance IDs per replica in multi-replica deployments.

### Privacy and retention posture (baseline)
- `correlation_id` MUST remain non-PII and short-lived. It MUST NOT embed user identifiers.
- Document the expected retention posture for local/dev/CI logs (production retention is out of MVP scope but should be tracked).

## Work Plan

### Milestone 1: Confirm current consumer configuration and baseline behavior
**Objective**: Make current Kafka consumer-group behavior observable and establish a baseline for comparison.

**Tasks**:
1. Inventory each service’s Kafka consumer settings currently in effect (at minimum: `group.id`, `session.timeout.ms`, `heartbeat.interval.ms`, `max.poll.interval.ms`, assignment strategy if configured).
2. Capture a baseline “restart → immediate publish → first output” latency measurement for TTS using existing smoke/probe tooling.
3. Capture a baseline “restart → first consume” time for at least one additional service (e.g., translation or ASR) to confirm the pattern is not TTS-specific.
4. Document baseline measurements (including environment assumptions) as an evidence artifact.

**Acceptance Criteria**:
- Baseline parameters and timing evidence are recorded in a reproducible location.
- A single source of truth exists for “what the consumer thinks it’s configured to do” (service startup log line or equivalent).

**Dependencies**: None.

### Milestone 2: Implement consumer-group recovery tuning at the service boundary
**Objective**: Reduce the predictable ~42s post-restart delay by adjusting consumer-group configuration.

**Tasks**:
1. Decide on a tuning approach and document the rationale. Candidate categories include:
  - Shortening consumer session/member liveness timeouts to reduce dead-member wait.
  - Using assignment strategies that reduce disruptive rebalances.
  - Optional static membership patterns where appropriate.
2. Implement a shared-lib **pure helper** that merges pinned consumer defaults with caller-provided overrides.
   - Services remain responsible for parsing env vars and passing overrides into the helper.
3. Apply the shared-lib helper across all target services’ consumers (Gateway/VAD/ASR/Translation/TTS) to standardize behavior.
4. Validate there is no drift: services should log the effective values at startup (Milestone 3).

**Acceptance Criteria**:
- After restarting the TTS service and publishing within a few seconds, time-to-first-output is materially reduced vs baseline.
- After restarting any one additional target service, time-to-first-consume is materially reduced vs baseline.
- Service behavior remains stable under steady-state operation (no visible crash loops or runaway rebalances).
- All target services use the same shared-lib helper (documented) to avoid configuration drift.
- All new consumer tuning knobs are validated with safe bounds and fail fast on invalid configuration.

**Constraints**:
- Do not move retry/backoff policy into shared-lib.
- Keep any new configuration controlled via environment variables with safe defaults.

### Milestone 3: Add minimal, always-on diagnosability telemetry
**Objective**: Make future incidents quickly attributable (rebalance vs compute vs storage vs deserialization).

**Tasks**:
1. Add a startup log event (standardized name/fields) that prints the effective consumer-group tuning parameters using an explicit allowlist (sanitized; no secrets).
2. Add a structured log event for consumer assignment acquisition (timestamp + partitions) that is emitted only on assignment changes.
3. Add a structured log event for “first input received” that is emitted:
  - once after startup, and
  - once after each assignment change.
4. Ensure the same event names and fields are present across all target services to support cross-service correlation.
5. Gate any per-message consume logs behind an explicit debug/sampling toggle.

**Security Constraints (for this milestone)**:
- No telemetry event logs payload contents.
- The “effective config” event logs only non-sensitive tuning values (never endpoints or auth-related config).

**Acceptance Criteria**:
- A single failing E2E run can be diagnosed by correlating:
  - service startup time
  - assignment acquired time
  - input received time
  - output published time
  without enabling debug logs.

### Milestone 4: Align smoke-test expectations with known tail behavior
**Objective**: Prevent false negatives in E2E smoke when the only issue is expected post-restart recovery delay.

**Tasks**:
1. Update the smoke tooling/configuration defaults so that:
  - It is explicit whether a run is measuring “cold-start recovery” vs “steady-state latency”.
  - Timeouts match the targeted recovery behavior (post Milestone 2) for each mode.
2. Update developer documentation/runbook notes describing how to interpret timeouts and which logs to check.

**Acceptance Criteria**:
- Default local smoke runs target **steady-state** validation and no longer fail due to predictable restart recovery delay.
- There is a documented and first-class way to run a **cold-start/restart recovery** scenario intentionally (separate mode/flag), so regressions are not masked.

### Milestone 5: Version management and release artifacts
**Objective**: Keep release-train artifacts consistent with the roadmap target.

**Tasks**:
1. Add a CHANGELOG entry for this hardening work under v0.5.0.
2. Update any versioned artifacts required by the repo’s release process to match v0.5.0.

**Acceptance Criteria**:
- CHANGELOG and version artifacts are consistent and reflect the work delivered by this plan.

## Testing Strategy (high-level)
- Unit-level coverage for any new configuration parsing and logging helpers.
- Integration-level validation that restart recovery meets the plan’s acceptance criteria.
- End-to-end validation via existing smoke harnesses to ensure the TTS output is still produced and consumed as expected.

## Validation & Rollback (high-level)
- **Validation**: Compare pre/post measurements for restart recovery latency; confirm no new crash loops.
- **Rollback**: Revert consumer tuning to prior defaults if instability is observed; keep telemetry additions (they are low-risk).

## Risks and Mitigations
- **Risk**: Over-aggressive timeouts increase false rebalances during transient pauses.
  - **Mitigation**: Tune conservatively, measure in local loops, and document the tradeoff.
- **Risk**: Sensitive data leaks via logs (endpoints, secrets, or payload content).
  - **Mitigation**: Enforce allowlisted structured logging; never log payloads; never dump env; do not log endpoints/auth config.
- **Risk**: `correlation_id` becomes a stable pseudonymous identifier with long log retention.
  - **Mitigation**: Ensure `correlation_id` contains no user-derived identifiers; document retention expectations for local/dev/CI logs.
- **Risk**: Configuration drift across services causes inconsistent behavior.
  - **Mitigation**: Prefer a consistent, documented pattern across services once proven on TTS.
- **Risk**: Excessive logging volume.
  - **Mitigation**: Keep always-on telemetry to startup + assignment changes + “first input received”; gate per-message logs behind explicit debug/sampling.
