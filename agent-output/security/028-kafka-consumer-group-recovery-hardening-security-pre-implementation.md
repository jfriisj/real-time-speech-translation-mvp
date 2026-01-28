# Security Assessment: Plan 028 (Kafka Consumer Group Recovery Hardening)

**Plan Reference**: agent-output/planning/closed/028-kafka-consumer-group-recovery-hardening-plan.md  
**Architecture Reference**: agent-output/architecture/system-architecture.md  
**Assessment Type**: Pre-Implementation Security + Compliance Review (Plan/Architecture)  
**Status/Verdict**: APPROVED_WITH_CONTROLS

## Metadata
| Field | Value |
|------|-------|
| Assessment Date | 2026-01-28 |
| Assessor | Security Agent |
| Mode Determination | Inferred (user asked to review Plan 028 for security/compliance) |
| Scope | Plan 028 consumer tuning env vars + cross-service telemetry/logging contracts |
| Out of Scope | Full code audit of all services; production Kafka/SR auth (SASL/TLS/ACLs); SIEM/central logging deployment |

## Changelog
| Date | Change | Impact |
|------|--------|--------|
| 2026-01-28 | Initial assessment | Defines security/compliance controls required before implementation proceeds |

## Executive Summary

Plan 028 is **net-positive** for security and reliability: it reduces restart-induced unavailability and improves diagnosability. The main security risks are **information disclosure via logs/config echoing** and **availability regressions** from over-aggressive Kafka consumer tuning.

**Overall Risk Rating**: LOW–MEDIUM  
**Verdict**: APPROVED_WITH_CONTROLS

## Threat Model Summary (STRIDE)

**Trust boundaries impacted**:
- Service → Kafka broker (TCP)
- Operator/CI → Service configuration (environment variables)
- Service → Log sink (container logs; future centralized logging)

**Key threats**:
- **Information Disclosure**: accidentally logging secrets embedded in connection strings or environment; leaking sensitive identifiers via per-message logs.
- **Denial of Service**: consumer tuning causes frequent rebalances, stalls, or thundering herds on restarts.
- **Tampering/Misconfiguration**: invalid `group.instance.id` usage or unsafe assignment strategy config causing stuck consumption.

## Findings

### Critical
None identified at plan level, provided controls below are implemented.

### High

| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| H-001 | Secrets/config leakage via “effective config” logging | Information Disclosure (OWASP A09/A05) | Plan 028 Milestone 3 (`kafka_consumer_config_effective`) | Logging effective consumer config is valuable, but Kafka/SR connection settings can include credentials (e.g., SASL, basic auth, tokens, query params) in future deployments. Printing config dicts can leak secrets to logs. | Log only an allowlist of *non-sensitive* keys/values. Sanitize any endpoints (strip userinfo/query). Never log env dumps. Never log headers or payloads. |
| H-002 | Debug per-message logging can leak sensitive data and overload logs | Information Disclosure + Availability | Plan 028 telemetry contract | Even “debug mode” per-message logs can leak user-related identifiers and can become an inadvertent always-on setting in dev/CI. | Ensure debug mode logs **never include payload contents** and support sampling. Provide a clear kill-switch and make default OFF. |

### Medium

| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| M-001 | Over-aggressive consumer tuning can reduce availability | Availability / Insecure Design (OWASP A04) | Plan 028 Milestone 2 | Tight timeouts can amplify false rebalances during GC pauses, CPU contention, or IO stalls (common during cold start), potentially reducing reliability. | Ship conservative defaults; document tradeoffs; enforce minimum/maximum bounds; validate with restart + steady-state soak tests. |
| M-002 | Static membership introduces identity/config pitfalls | Availability / Misconfiguration | Plan 028 env vars (`KAFKA_CONSUMER_GROUP_INSTANCE_ID`) | Static membership can reduce disruptive rebalances but requires unique instance IDs per replica. Misconfiguration can lead to “flapping” members or stuck partitions. | Keep static membership **opt-in**; require uniqueness guarantee in multi-replica deployments; document compatibility constraints. |
| M-003 | Correlation identifiers in logs are pseudo-identifiers (retention/compliance risk) | Compliance / Privacy | Plan 028 `kafka_consumer_first_input_received` | `correlation_id` is not inherently PII, but it can become a stable pseudonymous identifier. Logging it at scale creates retention obligations and increases breach impact. | Define retention limits for logs in dev/CI, avoid embedding PII in `correlation_id`, and prefer short-lived IDs. Consider hashing if correlation ID might contain user-derived data. |

### Low / Informational

| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| L-001 | Env var interface hardening | Misconfiguration | Plan 028 Standardization Contracts | New `KAFKA_CONSUMER_*` env vars need validation to prevent invalid values causing unexpected behavior. | Validate numeric ranges and allowed strategies at service startup; fail fast with clear error. |

## Positive Findings

- Plan explicitly constrains shared-lib to a **pure** helper (no orchestration), reducing supply-chain and privilege creep.
- Telemetry is designed to be **low-volume** (startup + assignment + first input) which is a good baseline for both security and cost.
- Explicit separation of steady-state vs cold-start smoke modes reduces the temptation to “hide” failure modes.

## Required Controls (Gate to Implementation)

1. **Safe structured logging allowlist**
   - For `kafka_consumer_config_effective`, log only non-sensitive keys (e.g., timeouts, assignment strategy, group id). Do **not** log `bootstrap.servers` or any auth-related config.
   - Sanitize endpoints (strip credentials/query) if any endpoint-like values are logged.

2. **No payload logging (ever)**
   - Even in debug mode, do not log event payloads (text/audio URIs/bytes). Debug logs may include offsets/timestamps only.

3. **Config validation and bounds**
   - Validate `*_MS` ranges (min/max) and assignment strategy values; fail fast with a clear startup error.
   - Keep static membership opt-in and document replica-uniqueness requirements.

4. **Default-off debug / sampled diagnostics**
   - Per-message consume logs must be gated behind explicit env flags and/or sampling.
   - CI should run with debug logging disabled unless a test explicitly needs it.

5. **Log retention + privacy posture (baseline)**
   - Document expected retention for local/dev/CI logs.
   - Ensure `correlation_id` is not user-derived PII and is short-lived.

## Testing Recommendations (Security/Compliance)

- Add a unit/integration check that `kafka_consumer_config_effective` output never contains:
  - `KAFKA_BOOTSTRAP_SERVERS`,
  - any `PASSWORD`, `TOKEN`, `SECRET`,
  - URLs containing userinfo (`user:pass@`) or query tokens.
- Add a “debug mode” test ensuring payloads are not logged.
- Add a restart/soak test verifying tuning does not cause repeated rebalances under mild resource pressure.

## Compliance Mapping (Lightweight)

| Requirement | Standard | Status | Notes |
|-------------|----------|--------|------|
| Data minimization in logs | GDPR Art. 5(1)(c) | ✅ with controls | Log only offsets/timestamps/correlation_id; never payloads; avoid stable identifiers where possible. |
| Storage limitation / retention | GDPR Art. 5(1)(e) | ⚠️ requires follow-up | Plan should reference log retention expectations for dev/CI; production retention policy is out of MVP scope but should be tracked. |
| Security of processing (confidentiality) | GDPR Art. 32 | ✅ with controls | Main risk is secrets in logs; mitigated via allowlist + sanitization + no env dumps. |
| Logging and monitoring hygiene | OWASP ASVS 4.0 (V7) | ✅ with controls | Structured events are good; ensure sanitization and avoid sensitive content. |

## Handoff

**From**: Security  
**Artifact**: agent-output/security/028-kafka-consumer-group-recovery-hardening-security-pre-implementation.md  
**Verdict**: APPROVED_WITH_CONTROLS  
**Key focus**: prevent secrets/payload leakage in logs; validate/limit tuning knobs to avoid availability regressions.
