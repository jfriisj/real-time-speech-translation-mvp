# Plan 005: Ingress Gateway

**Plan ID**: 005
**Target Release**: v0.3.0 (Connectivity, Optimization & Speech)
**Epic**: 1.5 Ingress Gateway — Phase 1 (WebSocket)
**Status**: Approved
**Date**: 2026-01-19
**Dependencies**: Plan 001 (Shared Infra), Release v0.2.0 (Core Services)
**Related Analysis**: [Analysis 005](agent-output/analysis/005-ingress-gateway-analysis.md)
**Security Review**: [Security 005](agent-output/security/005-ingress-gateway-security-pre-implementation.md) — APPROVED_WITH_CONTROLS
**Related Critique**: [Critique 005](agent-output/critiques/005-ingress-gateway-plan-critique.md)
**QA Artifact**: [QA 005](agent-output/qa/005-ingress-gateway-qa.md)

## 1. Value Statement and Business Objective
**As a** Client Developer (Web/Mobile),
**I want** to stream audio via WebSocket to a single entry point,
**So that** I can connect external devices (microphones, browsers) to the pipeline without direct Kafka access or local CLI scripts.

**Scope Note**: This plan delivers Phase 1 (WebSocket ingress only). gRPC support (originally part of Epic 1.5) is deferred to a follow-up sprint post-v0.3.0 per [Analysis 005](agent-output/analysis/005-ingress-gateway-analysis.md).

**Measure of Success**:
- A new container `gateway-service` is running.
- A WebSocket client can connect, stream audio PCM, and receive an ack.
- The Gateway successfully produces an `AudioInputEvent` to Kafka `speech.audio.ingress`.
- The downstream ASR service processes this event (verified by logs/traceability).

## 2. Context & Roadmap Alignment
This plan addresses **Epic 1.5** specifically. It is the first step of **Release v0.3.0**, fundamentally changing the "User Experience" from a CLI-based demo to a network-accessible platform.

**Related Architecture**:
- [Architecture Master](agent-output/architecture/system-architecture.md): Defines the Gateway -> Kafka flow and preserves `AudioInputEvent` for backward compatibility.
- [Architecture Findings 006](agent-output/architecture/006-tts-voice-cloning-architecture-findings.md): Validates logical flow for v0.3.0.

**Roadmap Note**:
- This is part of the "Connectivity" theme of v0.3.0.
- Subsequent plans (006 VAD, 007 TTS) depend on the Gateway effectively capturing audio.

## 3. Assumptions & Constraints
- **assumption**: For MVP, the Gateway handles "End of Stream" detection via explicit client signals (connection close or structured end-of-stream message) OR buffer size limit. Sophisticated VAD happens *downstream* in the VAD service (Plan 006). **Protocol details documented in QA/client integration artifacts**.
- **constraint (Protocol)**: Must support WebSocket (primary for web clients). gRPC support is DEFERRED to post-v0.3.0 follow-up sprint per [Analysis 005](agent-output/analysis/005-ingress-gateway-analysis.md).
- **constraint (Payload)**: Gateway MUST buffer streaming audio into a valid `AudioInputEvent` (WAV format, ≤ 1.5 MiB) to satisfy the current synchronous contract before publishing. True streaming events are Post-MVP (Epic 3.1).
- **constraint (Concurrency)**: Maximum 10 concurrent WebSocket connections per container instance. Hard limit enforced at accept() to protect memory.
- **constraint (Buffer Management)**: Per-connection in-memory buffer with bounded size. Oversized streams are rejected with error response. **Buffer size constraint: must fit within Kafka message size limit (≤1.5 MiB event payload)**.
- **constraint (Session Timeouts)**: Idle timeout of 10 seconds (no data received) and maximum session duration of 60 seconds per connection. **Rationale**: Prevents slowloris-style DoS attacks and resource exhaustion from stalled clients.
- **constraint (Chunk Limits)**: Maximum chunk size of 64 KB per WebSocket message and maximum message rate enforcement. **Rationale**: Prevents oversized individual frames and rapid-fire flooding.
- **constraint (Origin Validation)**: WebSocket Origin header MUST be validated against an allowlist (configurable via env var; empty for local dev). **Rationale**: Prevents Cross-Site WebSocket Hijacking (CSWSH) if auth is later added or if deployed in mixed-trust environments.
- **constraint (Correlation ID)**: Gateway generates `correlation_id` server-side (UUID4) and MUST return it to client in the connection handshake/acknowledgment message for debugging/traceability. **Policy**: Gateway always generates its own `correlation_id`; any client-provided ID is ignored to ensure consistent UUID format and prevent spoofing/collisions.
- **constraint (Network Exposure)**: Service MUST be deployed on trusted internal network only for MVP. Public internet exposure is explicitly UNSUPPORTED without an external auth/rate-limit layer (reverse proxy with API key/JWT). **Rationale**: No authentication in MVP; exposure without perimeter control enables abuse.
- **constraint (Data Persistence)**: Gateway MUST NOT persist audio to disk by default. Audio payloads exist only in-memory during buffering and are discarded after publishing to Kafka. **Rationale**: Prevents accidental sensitive-data retention and privacy exposure.
- **constraint (Security)**: No authentication/authz required (per Architecture "No API Gateway/Auth" for MVP) BUT only if network-isolated.
- **constraint (Audio Format - MVP)**: Gateway accepts PCM16 audio (16kHz mono) as the baseline MVP contract. Support for additional formats/encodings is out-of-scope for v0.3.0.
- **dependency**: Requires `speech-lib` for Avro serialization and Python standard library `wave` module for WAV wrapping.

## 3.1. Security Requirements (Implementation Gate)

**Source**: [Security Review 005](agent-output/security/005-ingress-gateway-security-pre-implementation.md)

The following controls are REQUIRED before implementation and MUST be verified before release:

1. **DoS Protection**:
   - MUST enforce idle timeout (10s) and max session duration (60s).
   - MUST enforce max chunk size (64 KB) and reject oversized frames immediately.
   - MUST implement per-connection message rate tracking (graceful degradation or disconnect for abusive patterns).

2. **Container Hardening**:
   - MUST run as non-root user (e.g., `user: "1000:1000"` in Docker Compose).
   - MUST drop all unnecessary capabilities (`cap_drop: ["ALL"]`).
   - MUST set resource limits (`mem_limit`, `cpus`) to prevent runaway resource consumption.
   - SHOULD use read-only root filesystem where practical.

3. **Sensitive Data Protection**:
   - MUST NOT log audio payload bytes in any log level.
   - MUST NOT log environment variables or internal topology details at INFO/WARN levels.
   - MUST sanitize exceptions to avoid stack trace leakage in production.
   - Default log level MUST be INFO; DEBUG mode explicitly disabled in production.

4. **Network Boundary Enforcement**:
   - Deployment docs MUST explicitly state "trusted network only" for MVP.
   - If TLS termination is required, it MUST be handled by reverse proxy (not in-service).
   - Origin allowlist MUST be configurable (even if empty for local dev) to support future mixed-trust deployments.

**Verification**: QA/UAT artifacts must validate these controls before release sign-off. See [Security 005](agent-output/security/005-ingress-gateway-security-pre-implementation.md) for detailed threat model and procedural gates.

## 4. Implementation Plan

### Milestone 1: Workspace & Docker Setup
**Objective**: Establish the `services/gateway` container structure.
1.  **Directory**: Create `services/gateway/` workspace with runtime dependencies (HTTP/WebSocket server, Kafka producer, speech-lib for serialization).
2.  **Docker Compose**: Add `gateway-service` container.
    - **Requirements**:
      - Expose WebSocket endpoint on internal network.
      - Connect to Kafka and Schema Registry (env-based configuration).
      - Enforce concurrency/timeout/chunk limits via environment variables.
      - Container security hardening: non-root user, minimal capabilities, resource limits (see Security Review 005).

### Milestone 2: WebSocket Ingress
**Objective**: Accept audio streams over WebSocket and produce `AudioInputEvent` to Kafka.

**Requirements**:
1.  **Connection Management**:
    - Generate server-side `correlation_id` and return it to client in handshake acknowledgment.
    - Enforce global connection limit; reject excess connections.
    - Apply idle timeout and max session duration per Security Requirements.
2.  **Stream Buffering**:
    - Accept binary audio chunks (PCM format as defined in Audio Format constraint).
    - Accumulate into in-memory buffer (no disk persistence).
    - Detect stream termination via: client disconnect, explicit end-of-stream signal, or buffer size limit.
3.  **Event Production**:
    - Convert buffered PCM to WAV format.
    - Serialize as `AudioInputEvent` using `speech-lib` with `correlation_id`.
    - Publish to `speech.audio.ingress` topic.
4.  **Error Handling**:
    - Reject oversized payloads and close connection gracefully.
    - Log errors without exposing sensitive data (see Security Requirements).

### Milestone 3: Integration Verification
**Objective**: Verify the Gateway drives the pipeline end-to-end.

**Requirements**:
- Create a basic test client that simulates streaming audio to the Gateway WebSocket endpoint.
- Verify that Gateway successfully produces events consumed by downstream ASR service.
- Validate correlation_id propagation through the pipeline.

### Milestone 4: Version Management & Release Artifacts
**Objective**: Update project versioning.
1.  **Version Bump**: Update `services/gateway/__init__.py` (or similar) to `0.3.0-dev`.
2.  **Changelog**: Add entry to `CHANGELOG.md` (or release notes) denoting Gateway addition.
3.  **Roadmap Alignment**: Check off Epic 1.5 in `roadmap/product-roadmap.md`.

## 5. Validation Requirements

**Functional Validation**:
- Gateway must successfully accept WebSocket connections and produce valid `AudioInputEvent` messages to Kafka.
- Correlation IDs must propagate correctly from client → Gateway → downstream services.
- End-to-end latency traceability must function (integration with existing traceability tooling from v0.2.1).

**Non-Functional Validation**:
- Security controls from Section 3.1 must be verified (DoS protection, container hardening, data protection, network boundaries).
- Concurrency limits, timeouts, and chunk size caps must be enforced.
- Load characteristics under multiple concurrent connections must be acceptable.

**Note**: Detailed test cases, strategies, and QA procedures are documented in [QA 005](agent-output/qa/005-ingress-gateway-qa.md) per agent workflow boundaries.

## 6. Risks
- **Memory Pressure**: Buffering whole audio chunks in memory for many concurrent clients could OOM the container.
    - *mitigation*: Set strict payload limits (constrained by Kafka message size) and concurrent connection limits per Security Requirements.
- **Latency**: Buffering implementation adds latency (= utterance duration) vs true streaming.
    - *acceptance*: This is a known constraint of the current "Batch Event" architecture. True streaming is Epic 3.1.
