# Plan 001: Shared Infrastructure & Contract Definition
**Target Release**: v0.1.0 (The 'Hard MVP' Skeleton)
**Epic Alignment**: Epic 1.1: Shared Infrastructure & Contract Definition
**Status**: DELIVERED

## 1. Value Statement and Business Objective
**As a** System Implementer,
**I want** to establish a unified event bus and a strict, versioned Avro schema contract,
**So that** independent microservices can communicate reliably with type safety, zero direct coupling, full traceability, and foundational security.

## 2. Context
This plan addresses the foundational "Shared Infrastructure" requirement of the Hard MVP. It prevents the "integration hell" of mismatched JSON formats by enforcing schemas upfront. It creates the "Shared Service" (reusable library) with strict boundaries.

**Inputs**:
- `docs/MVP-FIRST_PLAN.md` (Defines architecture: Kafka + Schema Registry)
- `docs/event-driven-flows.md` (Defines target event types and Avro strategy)
- `agent-output/roadmap/product-roadmap.md` (Epic 1.1 constraints - Status: Delivered)
- `agent-output/security/001-shared-infrastructure-security-architecture-review.md` (Security constraints)
- `agent-output/analysis/001-shared-infrastructure-analysis.md` (Current blockers resolution)
- `agent-output/architecture/001-shared-infrastructure-architecture-findings.md` (Architecture required changes)
- `agent-output/architecture/003-audio-payload-policy-architecture-findings.md` (Payload policy & size limits)
- `agent-output/process-improvement/001-sequencing-validation.md` (Validated alignment of naming conventions)

## 3. Assumptions & Open Questions
- **Assumption**: We will use a local Docker Compose setup for Kafka, Zookeeper, and Schema Registry for development.
- **Assumption**: Python is the primary language for the shared library.
- **Assumption**: Mandated security controls (localhost/private network mapping) are sufficient for MVP.
- **DECISION**: Max Kafka message size is 2 MiB for MVP. Audio payloads > 1.5 MiB are rejected (no reference/URI support in v0.1.0).

## 4. Plan: Implementation Steps

### 4.0 Contract Canon (Architecture Mandate)
**Objective**: Pin the canonical naming and topic taxonomy before any code.
- **Canonical Audio Event**: `AudioInputEvent` (Renaming `AudioProcessingEvent` to match plan preference).
- **Subject Naming Strategy**: `TopicNameStrategy` (e.g., topic `speech.audio.ingress` has value schema subject `speech.audio.ingress-value`).
- **Topic Taxonomy**:
  - `speech.audio.ingress` (Audio input)
  - `speech.asr.text` (Recognized text)
  - `speech.translation.text` (Translated text)
- **Message Size Policy**:
  - Max broker message: `2097152` bytes (2 MiB).
  - Audio payload limit in `AudioInputEvent`: `1.5 MiB` (1,572,864 bytes).
  - Strategy for large audio: Reject >1.5 MiB in MVP (reference support out of scope for Hard MVP).

### Milestone 1: Infrastructure Bring-up & Security Hardening
**Objective**: Get the message bus running securely for local dev.
1. Create or update `docker-compose.yml` in project root (or `infrastructure/`).
2. Define services: `zookeeper`, `kafka`, `schema-registry`.
3. **Security Control**: Configure networking to bind ports ONLY to `127.0.0.1` (no external exposure).
4. **Security Control**: Use a private Docker network for inter-service communication.
5. **Security Control**: Configure `message.max.bytes=2097152` (2 MiB) on Kafka brokers.
6. **Governance**: Set Schema Registry default compatibility to `BACKWARD` (via env var or config).
7. **Validation**: Use `compose-bringup` to verify accessibility; scan ports to confirm no 0.0.0.0 exposure.

### Milestone 2: Schema Definition (The Contract)
**Objective**: Define the "Golden" Avro schemas with required envelope fields.
1. Create directory structure for shared schemas (e.g., `shared/schemas/avro/`).
2. Create `BaseEvent.avsc` (Common Envelope) including **MANDATORY** security/tracing fields:
   - `event_id` (UUID)
   - `correlation_id` (UUID - Critical for Epic 1.4)
   - `timestamp` (longmillis)
   - `event_type` (string)
   - `source_service` (string - Critical for origin tracking)
3. Create `AudioInputEvent.avsc` (Canonical Name) with payload: audio bytes (max 1.5MB enforcement logic in lib).
4. Create `TextRecognizedEvent.avsc` (payload: text, confidence).
5. Create `TextTranslatedEvent.avsc` (payload: translated text, source/target lang).
6. **Validation**: Use `jq` or a script to validate JSON examples against these schemas.

### Milestone 3: Shared Python Library (`speech-lib`)
**Objective**: Create the reusable code for services to use with strict supply-chain boundaries.
1. Initialize a Python package `shared/speech-lib`.
2. **Security Constraint**: Verify `setup.py`/`pyproject.toml` contains minimal dependencies.
3. Implement **Schema Registry Client Wrapper** (Configured for internal access only).
4. Implement **Event Models (Pydantic/Dataclasses)** representing the schemas.
5. Implement **Producer Wrapper**:
   - **Allowed Scope**: Serialization, envelope population, size check.
   - **Forbidden Scope**: No retries, routing logic, or model validation.
   - Method `publish_event(topic, event_model)` enforces `event_id`, `source_service`, `correlation_id`.
   - Rejects payloads > 1.5MB before sending.
6. Implement **Consumer Wrapper**:
   - **Allowed Scope**: Deserialization only.
   - Method `consume_events(topics)` handling deserialization.
7. Implement **Correlation Context Manager**.

### Milestone 4: Integration Verification (Smoke Test)
**Objective**: Prove the library talks to the infra and security controls are active.
1. Create a script `tests/smoke_infra.py` using `speech-lib`.
2. Action: Produce a `TextRecognizedEvent` to topic `speech.asr.text`.
3. Action: Consume the event immediately.
4. Verify: Payload matches, Schema Registry has registered the subject `speech.asr.text-value`.
5. **Security Test**: Verify attempt to connect to Kafka from non-localhost IP fails (if testable locally) or verify `netstat` binding.
6. **Security Test**: Verify producer rejects oversized payload (>1.5MB).

## 5. Testing Strategy
- **Unit Tests**: Test the Pydantic models and serialization logic in `speech-lib` in isolation.
- **Integration Tests**: The `smoke_infra.py` script acts as the integration test for this epic.
- **Verification**: Run `docker logs` on Schema Registry to see registration activity.

## 6. Risks
- **Schema Evolution Complexity**: Changing schemas later is hard. *Mitigation*: Stick to the MVP schema defined in `MVP-FIRST_PLAN.md` strictly.
- **Library Path Issues**: Python absolute imports in mono-repos can be tricky. *Mitigation*: Use editable pip install (`pip install -e ./shared/speech-lib`) in service Dockerfiles.

## 7. Version Management
- **Target Version**: v0.1.0 (Component: `speech-lib`)
- **Deliverables**:
    - `shared/speech-lib/pyproject.toml` version set to `0.1.0`.
    - `CHANGELOG.md` in `shared/speech-lib` created.
    - Infrastructure `docker-compose.yml` committed.
