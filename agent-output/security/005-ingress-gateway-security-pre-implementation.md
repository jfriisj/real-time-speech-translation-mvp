# Security Assessment: Ingress Gateway (WebSocket Audio Ingress)

**Plan Reference (if any)**: agent-output/planning/005-ingress-gateway-plan.md
**Assessment Type**: Pre-Implementation Security Review (Plan/Architecture)
**Status/Verdict**: APPROVED_WITH_CONTROLS

## Changelog

| Date | Change | Impact |
|------|--------|--------|
| 2026-01-19 | Initial assessment | Establishes security controls required before implementation |

## Scope

- Files/endpoints/components covered:
  - Plan: `services/gateway` (to be created), WebSocket endpoint `GET /ws/audio`
  - Docker Compose runtime settings for `gateway-service`
  - Kafka publishing of `AudioInputEvent` to `speech.audio.ingress`
  - Architecture requirements in agent-output/architecture/system-architecture.md (v0.3.0 flows)
- Out of scope:
  - Authentication/authorization for public internet exposure (explicitly out-of-scope for MVP)
  - gRPC ingress (deferred)
  - VAD/TTS services (separate reviews)

## Scope Notes (Data, Secrets, Retention)
- **PII**: Raw voice audio is personally identifying. Gateway handles audio payload in memory; avoid persistence unless explicitly introduced.
- **Credentials/Secrets**:
  - Kafka bootstrap + Schema Registry URLs are not secrets, but may reveal internal topology.
  - If SASL/TLS credentials are later required, they MUST come from environment/secret store and MUST NOT be logged.
- **Data retention**:
  - Gateway must not store audio to disk by default.
  - Logs must not include raw audio or large payload dumps.

## Executive Summary

- Overall risk rating: **MEDIUM**
- Key risks:
  - Denial of Service (connection flooding, oversized payloads, slowloris-style WebSocket)
  - Unauthorized access if the Gateway is exposed beyond a trusted network
  - Sensitive-data exposure via logs/metrics (voice audio, reference samples)
- Required controls:
  - Hard limits (connections, payload size, timeouts) + backpressure
  - Network exposure constraints (bind to internal network; protect with reverse proxy if exposed)
  - Safe logging practices + structured logging
  - Container hardening (non-root, read-only filesystem where practical)

## Threat Model Summary

- Trust boundaries:
  - External client > Gateway (untrusted input)
  - Gateway > Kafka/SR (internal trusted infra; must be authenticated/authorized if not on isolated network)
- Key threats (STRIDE):
  - **S**poofing: unauthenticated clients impersonate users; correlation IDs could be abused if client-controlled
  - **T**ampering: malicious clients send malformed frames to crash server or poison downstream decode
  - **R**epudiation: limited auditability without auth; need request IDs and minimal audit logs
  - **I**nformation disclosure: audio payload in logs, internal URLs, stack traces
  - **D**enial of service: connection floods, oversized buffers, slow sends, CPU exhaustion
  - **E**levation of privilege: if gateway container runs as root or has excessive Docker capabilities

## Findings

### Critical
| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| C-001 | No public exposure without perimeter control | Broken Access Control / Misconfiguration | agent-output/planning/005-ingress-gateway-plan.md | Plan explicitly omits auth. If the service is reachable from the public internet, any user can stream audio into Kafka, enabling abuse and cost/availability impacts. | Deploy only on trusted networks for MVP. If exposure is required, add a reverse proxy with auth (API key/JWT) and rate limiting, or implement minimal auth in-gateway. |

### High
| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| H-001 | DoS via connection/payload flooding | Availability | agent-output/planning/005-ingress-gateway-plan.md | WebSockets are easy to flood. Even with 10 connections, attackers can open/close rapidly or send very small chunks slowly to tie up resources. | Add: per-connection idle timeout, max session duration, max chunk size, and per-IP rate limiting (if behind proxy). Enforce `MAX_CONNECTIONS` plus request timeouts. |
| H-002 | Potential sensitive data leakage in logs | Information Disclosure | services/gateway (planned) | Default FastAPI/uvicorn logging and exception handling can leak stack traces, internal env vars, or request bodies if configured poorly. | Ensure production logging level defaults to INFO; never log payload bytes; sanitize exceptions; disable debug. Add explicit log filters for headers/env vars. |
| H-003 | Kafka injection / topic abuse if credentials are added later | Injection / Misconfiguration | docker-compose.yml (planned) | If SASL/TLS is introduced later, mismanaging credentials (in env, logs) becomes a major risk. | Document: credentials only via secrets; never in images; redact logs; prefer mTLS/SASL with least-privilege producer ACL to only `speech.audio.ingress`. |

### Medium
| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| M-001 | Input validation for PCM/WAV synthesis assumptions | Insecure Design | agent-output/planning/005-ingress-gateway-plan.md | Plan assumes PCM16 16kHz mono; malicious clients can send invalid data, causing downstream decode failures or high CPU during WAV wrapping. | Validate chunk type/size; enforce declared audio params in handshake; reject non-binary frames except sentinel JSON; cap total duration and chunk rate. |
| M-002 | Origin checking / CSWSH risk for browser clients | Broken Access Control | services/gateway (planned) | Browsers can be tricked into opening WebSockets (Cross-Site WebSocket Hijacking) if no Origin checks and if later cookies/auth are added. | For MVP: implement Origin allowlist (configurable) even without auth. If auth added later, make Origin checks mandatory. |
| M-003 | Correlation ID predictability/abuse | Integrity | agent-output/planning/005-ingress-gateway-plan.md | Server-generated UUIDs are fine, but ensure clients cannot force arbitrary correlation IDs that collide with existing sessions (if accepted later). | Keep correlation_id server-generated; echo to client; if client-supplied IDs are later allowed, validate format and uniqueness. |

### Low / Informational
| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| L-001 | Container hardening not specified | Security Misconfiguration | docker-compose.yml (planned) | Defaults often run as root and with broad capabilities. | Add: `user: "1000:1000"` (or non-root), `read_only: true` where possible, `cap_drop: ["ALL"]`, resource limits (`mem_limit`, `cpus`). |
| L-002 | TLS termination not defined | Crypto / Misconfiguration | Deployment | WebSockets over plain HTTP are fine for local dev but not safe over untrusted networks. | Terminate TLS at reverse proxy (Traefik/Nginx) for any non-local deployment; ensure HSTS if exposed via HTTPS. |

## Positive Findings

- Plan enforces strict payload caps (1.4 MiB buffer, 1.5 MiB event cap) and a global connection limit.
- Correlation IDs are generated server-side, reducing client-controlled trace manipulation.
- No disk persistence is required; in-memory buffering limits retention by default.

## Testing Recommendations

- Add integration test that attempts:
  - Oversized payload (>1.4 MiB) -> verify rejection and connection close
  - Idle connection (no data) -> verify idle timeout closes socket
  - Many short-lived connections -> verify connection limiter behavior
- Add a basic fuzz test (or property-based test) for WebSocket message handling: binary vs JSON sentinel ordering.
- Add load test (manual is acceptable for MVP): 10 concurrent clients for 60s.

## Required Controls (Gate to Implementation)

Before implementation begins, update the plan (or implementation checklist) to include:
- Idle timeout (e.g., 10s with no data) and max session duration (e.g., 60s) per connection.
- Max chunk size (e.g., 64KB) and max message rate per connection.
- Origin allowlist configuration (even if empty for local dev).
- Docker/container hardening baseline (`user`, `cap_drop`, resource limits).
- Explicit logging policy: no audio bytes, no secrets, no debug traces in prod.

## Handoff

## Handoff to Implementer

**From**: Security
**Artifact**: agent-output/security/005-ingress-gateway-security-pre-implementation.md
**Status**: APPROVED_WITH_CONTROLS
**Key Context**:
- Primary risks are DoS and inadvertent sensitive-data exposure.
- MVP can remain unauthenticated only if deployed inside a trusted network boundary.

**Recommended Action**: Update Plan 005 with the required controls section (timeouts, rate limits, Origin checks, container hardening) and treat public exposure as explicitly unsupported until an auth/rate-limit layer exists.
