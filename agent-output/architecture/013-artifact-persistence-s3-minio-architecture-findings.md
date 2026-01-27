# Architecture Findings 013: Epic 1.8 Artifact Persistence (S3/MinIO) — Claim Check Across Pipeline

**Related Plan (if any)**: agent-output/planning/013-artifact-persistence-s3-minio-plan.md
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | Roadmap | Pre-planning architectural assessment | Approves adding MinIO/S3 for artifact persistence and claim-check payload transport, with required constraints for contracts, security, and shared-lib scope. |

## Context

Epic 1.8 (v0.6.0) proposes persisting intermediate pipeline artifacts (audio and potentially text) to an object store (MinIO/S3) to:
- Improve thesis-grade auditability (“listen to what each stage saw/produced”)
- Reduce Kafka payload pressure (Claim Check pattern)
- Enable optional large-payload transport via URIs rather than inline bytes

The codebase already contains a minimal shared helper `ObjectStorage` (boto3-based) in the shared library.

This assessment focuses on architectural implications on:
- Contracts / schema evolution
- Security + retention
- Service boundaries and shared dependency creep

## Findings

### Must Change

- **Standardize claim-check semantics across events (not ad-hoc `payload_url`)**
  - The contract must define a consistent pattern for “inline bytes vs external URI” to avoid one-off fields per service.
  - Requirement: each blob-carrying event MUST support *either* inline bytes *or* a URI/reference (exactly-one semantics), with explicit `content_type` metadata.
  - Scope targets:
    - Ingress audio (`AudioInputEvent`)
    - VAD segments (`SpeechSegmentEvent`)
    - TTS output (`AudioSynthesisEvent`)

- **Preserve backward compatibility (Schema Registry `BACKWARD` or stricter)**
  - Schema evolution must be additive (new optional fields, or a union record) so existing consumers keep working.

- **Define retention/TTL and deletion responsibilities up-front**
  - Artifact retention MUST be time-bounded (thesis-friendly default: 24h), configurable by environment.
  - Ownership MUST be explicit:
    - Who creates keys
    - Who is allowed to delete
    - Whether lifecycle rules are managed centrally (preferred) vs by services

- **Security guardrails for URIs are mandatory**
  - Presigned URLs are bearer credentials; they MUST NOT be logged in full.
  - URIs must be time-bounded (presigned) or access-controlled (service credentials). No “public bucket” default.
  - Storage endpoints must remain internal-only in docker-compose/dev unless explicitly exposed.

- **Prevent shared-lib SDK creep**
  - The shared library may provide a thin storage interface, but MUST NOT become an application SDK.
  - Required constraint: storage helper must be optional for services (feature-flagged), and must not pull in business policy (retries, routing, orchestration).

### Risks

- **New operational dependency & failure modes**
  - Object store outages can break URI-based flows.
  - Required mitigation: services must degrade gracefully (fallback to inline when small; or reject with clear logs when URI required but store unavailable).

- **Privacy/data handling risk**
  - Audio artifacts are sensitive. Persisting them increases governance burden.
  - Required mitigation: explicit TTL, minimized scope (only what’s needed for audit), avoid long-lived user identity semantics.

- **Consistency risk for key naming / correlation**
  - If different services choose incompatible key schemes, replay/debugging becomes hard.
  - Required mitigation: define a canonical key structure keyed by `correlation_id` and stage (e.g., `corr/{correlation_id}/stage/{service}/{timestamp}.wav`).

### Alternatives Considered

- **Inline-only (no object store)**
  - Rejected for v0.6.0 because it cannot scale and will eventually violate Kafka payload invariants.

- **Always-URI (force storage for all artifacts)**
  - Acceptable as a deployment mode, but rejected as a universal default due to added dependency for small payloads.

- **Separate “artifact service” microservice**
  - Not recommended for thesis MVP+; adds routing/auth complexity. Introduce only if governance requirements grow.

## Integration Requirements

- Add MinIO/S3 as optional shared infrastructure.
- Define a consistent event-level claim-check contract:
  - inline bytes field
  - URI/reference field
  - content type
  - optional integrity metadata (recommended: `sha256`)
- Ensure all services can run with storage disabled (baseline path remains valid).
- Establish lifecycle proof/evidence expectations for thesis reproducibility (e.g., lifecycle rule documentation).

## Consequences

- Improves auditability and enables reliable handling of large audio payloads.
- Adds dependency and governance overhead; must be controlled with TTL, security, and clear failure semantics.

## Handoff

## Handoff to Planner/QA

**From**: Architect
**Artifact**: agent-output/architecture/013-artifact-persistence-s3-minio-architecture-findings.md
**Status**: APPROVED_WITH_CHANGES
**Key Context**:
- Standardize claim-check semantics across events; don’t introduce ad-hoc `payload_url` fields.
- Retention/TTL + non-logging of presigned URLs are mandatory.
- Storage helper must remain thin and optional to avoid shared-lib creep.

**Recommended Action**: In the plan, explicitly define schema evolution approach (optional fields/unions), URI failure behavior, and MinIO lifecycle/retention evidence.