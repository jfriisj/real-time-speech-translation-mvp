# Security Assessment: Plan 025 (Service Startup Resilience)

**Plan Reference (if any)**: agent-output/planning/025-service-startup-resilience-plan.md  
**Architecture Reference**: agent-output/architecture/system-architecture.md  
**Assessment Type**: Pre-Implementation Security Review (Plan/Architecture)  
**Status/Verdict**: APPROVED_WITH_CONTROLS

## Changelog

| Date | Change | Impact |
|------|--------|--------|
| 2026-01-28 | Initial assessment | Defines security controls required before implementation proceeds |

## Scope

- Files/components covered:
  - Plan 025 (service startup resilience pattern + compose healthchecks)
  - Docker Compose readiness mechanisms for Kafka and Schema Registry
  - Cross-service startup wait behavior for: `gateway-service`, `vad-service`, `asr-service`, `translation-service`, `tts-service`
  - Architecture constraints: “no shared-lib orchestration”, bounded waits, diagnosable logs
- Out of scope:
  - Full code review of each service implementation
  - Production TLS/SASL/IAM hardening for Kafka/SR/MinIO (not in MVP scope)
  - Runtime data-plane security between services (network segmentation, mTLS)

## Scope Notes (Data, Secrets, Retention)

- **PII**: This epic does not introduce new PII processing, but it impacts what gets logged during startup; ensure logs do not leak user content or sensitive configuration.
- **Credentials/Secrets present in environment today**:
  - MinIO credentials (`MINIO_*`) are present in compose for multiple services.
  - Hugging Face token (`HF_TOKEN`) may be provided.
  - Future Kafka/SR auth credentials (SASL/basic auth) may be embedded in URLs if not handled carefully.
- **Data retention**:
  - Startup logs are retained by default in container logs; treat them as potentially sensitive and avoid logging secrets/URLs with credentials.

## Executive Summary

- **Overall risk rating**: LOW–MEDIUM
- **Key risks**:
  - Secrets leakage via overly verbose logging (URLs containing credentials, env dumps, stack traces)
  - Supply-chain/attack-surface increase if healthchecks force adding tools (e.g., `curl`, `nc`) into images
  - Availability risk if readiness loops hang (missing per-attempt timeouts) or create “thundering herd” dependency traffic
- **Security posture**: This epic is net-positive for security and reliability because it reduces crash loops and improves deterministic startup, but it must be implemented with safe logging and bounded networking.

## Threat Model Summary

- **Trust boundaries**:
  - Service → Schema Registry (HTTP)
  - Service → Kafka broker (TCP)
  - Orchestrator (Compose/K8s) → Service lifecycle
- **Key threats (STRIDE)**:
  - **I**nformation disclosure: leaking credentials in logs (e.g., `SCHEMA_REGISTRY_URL` with basic auth; future Kafka SASL credentials)
  - **D**enial of service: startup loops without timeouts can hang; aggressive retries across many services can overload SR/Kafka on cold start
  - **T**ampering (config): if environment/config is attacker-controlled, readiness checks could be redirected to unintended endpoints (SSRF-like behavior)

## Findings

### Critical
None identified for local-only MVP, provided the controls below are implemented.

### High

| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| H-001 | Potential secrets exposure in startup logs | Information Disclosure | Plan 025 (WP2 logging requirements) | Startup readiness often logs dependency URLs. If URLs ever include credentials (basic auth for SR, SASL user/pass embedded in bootstrap strings, tokens), this becomes immediate credential leakage into `docker logs`. | Log only sanitized host/port (no userinfo/query). Never log env var dumps. Ensure exception handlers do not print request headers/bodies or full URLs with credentials. |
| H-002 | Healthcheck tooling drift may expand attack surface | Supply chain / Misconfiguration | Plan 025 (WP1) | Plan proposes `curl`/`nc`. Adding these tools to images via package managers increases attack surface and supply-chain churn. Compose already uses a bash `/dev/tcp` healthcheck for Schema Registry, which avoids new dependencies. | Prefer healthchecks that use tools already in the base image (or minimal shell checks). Avoid modifying production images to add `curl` solely for healthchecks. |

### Medium

| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| M-001 | Missing per-attempt network timeouts can cause hangs | Availability | Plan 025 (WP2 `wait_for_url`) | A bounded overall timeout is good, but each attempt must also have a short timeout (connect+read). Without per-attempt timeouts, a single hung TCP connection can exceed the overall budget or block clean shutdown. | Require per-attempt timeouts: HTTP requests with `timeout=(connect, read)`; TCP connect with short timeout (e.g., 1–2s). |
| M-002 | Retry storms (“thundering herd”) on cold start | Availability | Plan 025 (WP2) | When five services start simultaneously, naïve exponential backoff without jitter can synchronize and spike SR/Kafka. | Add jitter (small randomization) and cap backoff (`STARTUP_MAX_BACKOFF_SECONDS`). Rate-limit “still waiting” logs. |
| M-003 | SSRF-like risk if dependency URLs become configurable by untrusted actors | SSRF / Insecure Design | Plan 025 (WP2) | Readiness checks make outbound calls. If `SCHEMA_REGISTRY_URL` or similar were ever influenced by untrusted input, it could target internal metadata endpoints or external systems. In MVP compose this is operator-controlled, but it’s worth constraining for future deployments. | Constrain schemes to `http/https`; reject URLs with credentials in userinfo; optionally allowlist hostnames (e.g., `schema-registry`, `kafka`) for production configs. |

### Low / Informational

| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| L-001 | Compose dependency conditions are not fully “ready” today | Reliability / Misconfiguration | docker-compose.yml vs Plan 025 | Current compose uses `schema-registry: condition: service_healthy` (good), but Kafka is `condition: service_started` for services. This is not a security issue, but it can cause avoidable restarts/log churn and complicate incident triage. | Prefer `service_healthy` for Kafka too (if a robust healthcheck exists). Keep service-side waits regardless. |

## Positive Findings

- Architecture already enforces the key security boundary: no retry/backoff orchestration in `speech-lib`.
- Compose binds Kafka/SR/MinIO to `127.0.0.1` for local dev, reducing exposure.
- Gateway container hardening exists (non-root, `cap_drop`, `read_only`, resource limits), which is a good baseline.

## Required Controls (Gate to Implementation)

Before implementation begins (or before it is considered complete), incorporate these controls into Plan 025 acceptance criteria and implementation checklists:

1. **Safe logging**
   - Never log secrets (MinIO keys, HF tokens, any SASL creds).
   - Sanitize dependency URLs in logs (strip credentials/query). Prefer logging only `host:port`.
2. **Bounded waits with per-attempt timeouts**
   - Overall max wait via `STARTUP_MAX_WAIT_SECONDS`.
   - Per-attempt network timeouts for HTTP/TCP.
3. **Backoff + jitter**
   - Cap max backoff; add jitter to avoid synchronized retries.
   - Rate-limit “waiting…” logs.
4. **Avoid adding new tools solely for healthchecks**
   - Keep compose healthchecks compatible with existing container tooling.
5. **Configuration hardening (future-safe)**
   - Restrict dependency URL schemes; reject URLs containing embedded credentials.

## Testing Recommendations

- Add a negative-path integration test (or manual runbook) verifying:
  - If Schema Registry is down, each service exits non-zero after the configured timeout.
  - Logs do not contain any of: `MINIO_SECRET_KEY`, `HF_TOKEN`, or full URLs containing credentials.
- Add a cold-start stress test:
  - Run `docker compose down -v && docker compose up` 10 times; verify no crash loops and no retry storms.

## Handoff

**From**: Security  
**Artifact**: agent-output/security/025-service-startup-resilience-security-pre-implementation.md  
**Status**: APPROVED_WITH_CONTROLS  
**Key Context**:
- The main security risk is accidental credential leakage via logging while implementing readiness.
- Avoid increasing attack surface by installing extra tools for healthchecks.
- Enforce per-attempt timeouts + jittered backoff to prevent hangs and retry storms.
