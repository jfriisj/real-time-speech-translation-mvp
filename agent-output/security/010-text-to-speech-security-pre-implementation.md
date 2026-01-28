# Security Assessment: Plan 010 (TTS + Claim Check Pilot)

**Plan Reference (if any)**: agent-output/planning/010-text-to-speech-plan.md
**Assessment Type**: Pre-Implementation (Architecture-focused)
**Status/Verdict**: APPROVED_WITH_CONTROLS

## Changelog

| Date | Change | Impact |
|------|--------|--------|
| 2026-01-27 | Initial assessment | Defines required controls before implementation proceeds |

## Scope

- Files/components covered:
  - agent-output/planning/010-text-to-speech-plan.md (Rev 34)
  - agent-output/architecture/system-architecture.md
  - docker-compose.yml (MinIO/SR/Kafka exposure defaults)
  - Claim Check pilot boundary: TTS emits internal object key; Gateway presigns/proxies
- Out of scope:
  - Full code security review of `services/tts` implementation
  - Gateway endpoint design details (only the contract boundary is reviewed)
  - Production IAM, TLS, and secrets manager implementation (not present in MVP scope)

## Executive Summary

- **Overall risk rating**: MEDIUM
- **Key risks**:
  - **Secrets/credentials**: MinIO root credentials are static and default in local compose; unsafe if reused beyond localhost.
  - **Supply chain drift**: `minio/minio:latest` and `minio/mc:latest` are unpinned; Kokoro model downloads are not pinned to a specific HF revision.
  - **Sensitive data handling**: Audio and text are inherently sensitive; retention/visibility controls need to be explicit and enforced.
  - **URI misuse risk (future)**: If `audio_uri` ever becomes an arbitrary URL, it becomes an SSRF vector at the edge.
- **Required controls** (must address before implementation is considered complete):
  - Pin container images and model revisions; tighten secret handling; restrict presigned URL exposure and TTL; ensure sensitive content is not logged.

## Threat Model Summary

- **Trust boundaries**:
  - External client ↔ Gateway (edge boundary)
  - Internal services ↔ Kafka/SR (internal network boundary)
  - Internal services ↔ MinIO (object store boundary)

- **Key threats (STRIDE)**:
  - **Spoofing**: No authentication between services in MVP; if network is compromised, an attacker can produce/consume events.
  - **Tampering**: Object store objects could be overwritten if keys collide or creds leak; no payload integrity (hash) is defined.
  - **Repudiation**: Lack of audit-grade immutable logs; correlation IDs help but not tamper-proof.
  - **Information disclosure**: Presigned URLs and user text/audio leakage via logs, Kafka payloads, or exposed ports.
  - **Denial of service**: Large input texts/audio can exhaust CPU and storage; model downloads can stall startup.
  - **Elevation of privilege**: MinIO root credentials (if reused) grant broad access.

## Findings

### Critical
| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| C-001 | Default object store credentials usable beyond localhost | Secrets / Misconfiguration | docker-compose.yml | MinIO is configured with `minioadmin/minioadmin`. Compose binds MinIO to `127.0.0.1`, which is safer for local dev, but these credentials are high risk if copied to non-local environments. | Require unique credentials per environment; never use defaults outside local. Use a secrets mechanism (env injection at minimum) and rotate. |

### High
| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| H-001 | Unpinned container images (`latest`) | Supply chain | docker-compose.yml | `minio/minio:latest` and `minio/mc:latest` increase risk of unexpected changes and compromised upstream tags. | Pin image digests or explicit versions; document update cadence. |
| H-002 | Unpinned model artifacts from Hugging Face | Supply chain / Integrity | Plan 010; TTS model download behavior | Plan requires `onnx-community/Kokoro-82M-v1.0-ONNX` but does not require pinning to a specific revision/commit or verifying integrity. | Pin `repo_id` + `revision` (commit hash/tag) and cache in build/runtime with controlled updates. |
| H-003 | Presigned URL exposure controls not specified at the edge | Info disclosure | Plan 010 (Gateway/Edge contract) | Plan correctly assigns presigning to Gateway, but does not require URL TTL bounds for client delivery nor explicit “never store/persist presigned URLs”. | Require short TTL for client presigns (minutes, not hours), and prohibit logging, persistence, or sharing across tenants. |

### Medium
| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| M-001 | Sensitive data in logs/events (text/audio context) | Privacy / Logging | Plan 010 (observability), schemas | Even a 120-char `text_snippet` can contain PII. Correlation IDs are fine, but any user content in logs should be minimized. | Make text snippet emission configurable; default to no user text in logs. Redact/limit further if needed. |
| M-002 | Missing payload integrity metadata for Claim Check objects | Integrity | Plan 010 + AudioSynthesisEvent | `audio_uri` references an object, but there is no checksum/size metadata to detect tampering/corruption. | Add optional `audio_sha256` and `audio_size_bytes` fields (additive schema evolution) and verify on fetch (Gateway/client). |
| M-003 | Key collision / overwrite risk | Integrity / Availability | Plan 010 key format | `tts/{correlation_id}.wav` can overwrite on retry/replay if correlation IDs are reused or duplicated across runs. | Include uniqueness (e.g., event_id suffix) or use versioned keys; enforce bucket versioning if available. |
| M-004 | Potential future SSRF if `audio_uri` becomes a URL | SSRF | Plan 010 future modes | The plan now restricts `TTS_AUDIO_URI_MODE` to `internal` for v0.5.0 (good). If later expanded to presigned/external URLs, the edge may become an SSRF vector if it fetches arbitrary URLs. | Keep `audio_uri` as internal key; if URLs are ever allowed, enforce strict allowlist + scheme restrictions at the Gateway. |

### Low / Informational
| ID | Title | Category | Location | Description | Remediation |
|----|-------|----------|----------|-------------|-------------|
| L-001 | No auth/TLS in MVP internal network | Security posture | system-architecture.md, docker-compose.yml | MVP uses plaintext Kafka/SR/MinIO with localhost port binds. Acceptable for local dev but not for production-like deployments. | Document “local-only” posture; require TLS/auth for any non-local deployment. |

## Positive Findings

- Plan enforces **Claim Check XOR semantics** (inline bytes vs URI) and explicitly prohibits logging presigned URLs.
- Plan assigns presigning to the **edge boundary**, reducing credential leakage risk from internal services.
- Retention is **time-bounded** via object-store lifecycle (24h), which is a strong baseline for sensitive audio artifacts.

## Required Controls (Gate for implementation completion)

1. **Secrets**: replace default MinIO creds in any environment beyond localhost; document secrets injection and rotation.
2. **Supply chain pinning**:
   - Pin MinIO images to versions/digests.
   - Pin Kokoro ONNX model to an HF `revision` (commit/tag) and document update process.
3. **Edge URL policy**:
   - Require short TTL presigned URLs for clients (minutes).
   - Prohibit logging/persisting presigned URLs; avoid returning long-lived public URLs.
4. **Sensitive logging policy**:
   - Do not log user text/audio; if `text_snippet` is emitted, make it opt-in and/or strongly truncated/redacted.
5. **Integrity metadata (recommended)**:
   - Add optional `audio_sha256`/`audio_size_bytes` for Claim Check objects and validate on retrieval.

## Testing Recommendations

- Add a security-oriented integration test for Gateway retrieval that verifies:
  - presigned URLs are short-lived;
  - the returned URL never appears in logs;
  - invalid/expired keys fail safely without SSRF behavior.
- Add a “config hardening” smoke test ensuring non-local deployments fail fast if MinIO default creds are detected.
- Add an object integrity test (if checksum fields are added): verify `sha256` matches downloaded object.

## Handoff

## Handoff to Planner/Implementer

**From**: Security
**Artifact**: agent-output/security/010-text-to-speech-security-pre-implementation.md
**Status**: APPROVED_WITH_CONTROLS
**Key Context**:
- Claim Check introduces secrets + data retention risks; edge presigning is the right boundary but needs TTL + logging controls.
- Unpinned images/models are the largest supply chain risk in this plan.

**Recommended Action**: Update Plan 010 implementation tasks to include the required controls above (especially pinning + secrets + edge URL TTL), then proceed to implementation with those controls treated as acceptance criteria.
