# Security Architecture Review 001: Shared Infrastructure & Contract Definition (Epic 1.1)

## Metadata
| Field | Value |
|------|-------|
| Assessment Date | 2026-01-15 |
| Assessor | Security Agent |
| Assessment Type | Targeted Architecture Security Review |
| Mode Determination | Inferred (user requested trust boundaries / threat model implications for Epic 1.1) |
| Scope | agent-output/architecture/system-architecture.md (trust boundaries, data flows, shared contract artifact); Epic 1.1 in agent-output/roadmap/product-roadmap.md |
| Related Plan (future) | agent-output/planning/001-shared-infrastructure-plan.md |
| Version Target | v0.1.0 (Hard MVP) |

## Executive Summary
Epic 1.1 introduces a shared Kafka + Schema Registry backbone and a shared contract artifact. This materially increases the system’s **attack surface** (event bus and schema registry become high-value assets) and creates a new **supply-chain-style trust boundary** (shared contract artifact). The design is acceptable for a hard MVP **only if** local-dev exposure is tightly constrained and minimal integrity controls are applied.

**Overall Risk Rating**: MEDIUM
**Verdict**: APPROVED_WITH_CONTROLS

## Trust Boundaries (What crosses them)

### TB-1: External Producer/CLI → Kafka (Ingress)
- **Data**: audio payloads or references, `correlation_id`, metadata.
- **Trust change**: introduces untrusted input into the event backbone.

### TB-2: ASR Service ↔ Kafka
- **Data**: audio events in; `TextRecognizedEvent` out.
- **Trust change**: ASR processes untrusted data; output becomes trusted-by-consumers unless validated.

### TB-3: Translation Service ↔ Kafka
- **Data**: `TextRecognizedEvent` in; `TextTranslatedEvent` out.
- **Trust change**: translation output may be treated as “safe” by downstream clients.

### TB-4: Services/Clients ↔ Schema Registry (Control Plane)
- **Data**: schema IDs, subjects, schema versions, compatibility settings.
- **Trust change**: Schema Registry is a **control plane**; compromise can undermine validation/integrity guarantees.

### TB-5: Shared Contract Artifact → Services (Build-time / Supply Chain)
- **Data**: `.avsc` schemas, generated bindings, envelope conventions.
- **Trust change**: a shared dependency can become a single point of compromise if it ships executable logic.

## Threat Model Summary (STRIDE)

### Spoofing
- Risk: unauthenticated producers/consumers can impersonate services and publish forged events.
- MVP note: auth is “out of scope”, but **network-level containment** is required.

### Tampering
- Risk: events can be modified in transit on an untrusted network; schema registry responses can be tampered with if exposed.
- Mitigation: keep Kafka/SR on private Docker network; avoid exposing ports beyond localhost.

### Repudiation
- Risk: without auth/audit, producers can deny having sent events.
- MVP mitigation: include `source_service` (or equivalent) in the event envelope; log `event_id` + `correlation_id` consistently.

### Information Disclosure
- Risk: Kafka topics may contain sensitive audio/text; Schema Registry metadata can reveal internal structure.
- MVP mitigation: don’t log raw audio/text by default; treat Kafka as sensitive; keep it local.

### Denial of Service
- Risk: a producer can flood topics; large audio payloads can exhaust broker disk/memory.
- MVP mitigation: enforce message size limits; define a maximum audio payload policy (prefer references for large audio); basic quotas in dev.

### Elevation of Privilege
- Risk: Schema Registry compromise can allow malicious schema changes; consumers may accept altered schemas if compatibility is weakened.
- MVP mitigation: pin compatibility to `BACKWARD` (or stricter), restrict who can register schemas (even if via “team convention” locally).

## Findings

### High (Fix before broad sharing / any non-local deployment)
| ID | Title | Category | Description | Required Controls |
|----|-------|----------|-------------|------------------|
| H-001 | Kafka/SR exposed without auth | Broken Access Control | Kafka and Schema Registry are high-value entry points; if exposed beyond localhost, any actor can publish/consume/register schemas. | Bind ports to `127.0.0.1`; keep services on private Docker network; do not deploy to shared network without ACLs/auth. |
| H-002 | Shared contract artifact can become supply-chain risk | Data Integrity / Supply Chain | A “shared library/module” can centralize compromise if it contains runtime logic or pulls unsafe deps. | Restrict shared artifact to schemas + codegen outputs only; no business logic; version pinning; minimal deps. |

### Medium (Fix for MVP robustness)
| ID | Title | Category | Description | Recommended Controls |
|----|-------|----------|-------------|---------------------|
| M-001 | Oversized audio messages can DoS Kafka | Availability | Audio payloads can exceed broker limits and fill disks quickly. | Define max message size; prefer file/object-store references; reject large payloads early. |
| M-002 | Lack of envelope fields reduces traceability and forensics | Repudiation / Logging | Without `event_id`, `source_service`, timestamps, tracing is weaker. | Ensure envelope includes `event_id`, `timestamp`, `source_service`, `correlation_id`. |

### Low / Informational
| ID | Title | Category | Description | Recommendation |
|----|-------|----------|-------------|---------------|
| L-001 | Topic naming inconsistency can cause misrouting | Insecure Design | `AudioProcessingEvent` vs `AudioInputEvent` naming drift increases integration mistakes. | Choose one canonical audio-ingress event name + topic taxonomy and document it. |

## Required Controls (Gate for APPROVED_WITH_CONTROLS)
1. **Network containment (local dev)**: Kafka and Schema Registry must not be reachable from untrusted networks (bind to localhost; private Docker network).
2. **Shared contract artifact restrictions**: schemas + generated bindings only; no executable business logic.
3. **Event envelope minimum**: `event_id`, `correlation_id`, `timestamp`, `event_type`, `source_service`.
4. **Payload policy**: define max audio payload size and handling strategy for larger inputs.

## Positive Findings
- Architecture explicitly identifies Schema Registry as a contract authority and mandates a compatibility mode.
- Correlation IDs are treated as mandatory across events, which supports later observability and incident analysis.

## Testing Recommendations (Security-relevant)
- Smoke test verifies Schema Registry is not exposed beyond localhost.
- Contract test ensures producers fail fast on schema mismatch.
- Load test publishes large messages to confirm broker limits and rejection behavior.

## Notes / Limitations
- This review assumes the hard MVP is run in a local/dev environment without authentication. If you intend to deploy to any shared network, re-run this as a **Pre-Production Gate** with ACLs, TLS, and auth enabled.
