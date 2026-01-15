# System Architecture — Universal Speech Translation Platform

**Last Updated**: 2026-01-15

## Changelog

| Date | Change | Rationale | Plan |
|------|--------|-----------|------|
| 2026-01-15 | Initial architecture baseline + decisions for Epic 1.1 | Establishes the Hard MVP backbone (Kafka + Schema Registry + shared contract) and constrains scope to avoid creep | Epic 1.1 (Shared Infrastructure & Contract Definition) |
| 2026-01-15 | Pinned canonical `AudioInputEvent`, topic taxonomy, and SR governance notes | Removes naming drift; makes contract + registry behavior explicit for downstream epics | Epic 1.1 (post-delivery alignment) |
| 2026-01-15 | Epic 1.2 pre-planning guardrails (topics, audio format, failure signaling, delivery semantics) | Prevents downstream integration drift between plans and the v0.1.0 infrastructure contract | Epic 1.2 (ASR Service) |

## Purpose
Deliver a **hard MVP** event-driven speech translation pipeline that is:
- Measurable (end-to-end latency + correlation IDs)
- Decoupled (services communicate only via events)
- Expandable (new services can subscribe to existing contracts)

## High-Level Architecture
- **External Producer/Client** publishes an audio-ingress event (MVP can be a CLI/script).
- **ASR Service** consumes audio events and produces recognized text events.
- **Translation Service** consumes recognized text events and produces translated text events.
- **Kafka** is the event bus.
- **Confluent Schema Registry** governs Avro schemas.
- A **Shared Contract Artifact** (schemas + optional generated bindings) is the canonical integration surface.

## Components & Boundaries

### Infrastructure (shared)
- Kafka cluster (single-node for local dev; scalable later)
- Schema Registry (single-node for local dev)

### Shared Contract Artifact (shared)
- Owns the canonical Avro `.avsc` files and event envelope.
- MAY provide generated bindings (e.g., Python classes) but MUST NOT contain business logic.

### Microservices (independent)
- ASR Service: audio → text
- Translation Service: text → translated text
- Optional later: TTS Service: translated text → synthesized audio

## Runtime Flows (Hard MVP)
1. Producer publishes `AudioInputEvent` (topic: `speech.audio.ingress`) with a `correlation_id`.
2. ASR consumes audio event and publishes `TextRecognizedEvent` preserving `correlation_id`.
3. Translation consumes `TextRecognizedEvent` and publishes `TextTranslatedEvent` preserving `correlation_id`.
4. Consumer/CLI prints final result (and later attaches latency metrics).

## Data Boundaries & Contracts
- All inter-service data crosses boundaries as **Avro-encoded events**.
- Schema Registry subjects are the source of truth for compatibility.
- Correlation tracking is mandatory: `correlation_id` MUST be present on all MVP events.

### MVP Topic Taxonomy
- `speech.audio.ingress` → `AudioInputEvent`
- `speech.asr.text` → `TextRecognizedEvent`
- `speech.translation.text` → `TextTranslatedEvent`

## Dependencies
- Kafka
- Schema Registry
- Avro tooling for serialization/deserialization

## Quality Attributes (MVP priorities)
- **Simplicity / Scope control**: no extra flows, no API gateway, no auth requirements for MVP.
- **Interoperability**: single envelope + strict schemas.
- **Observability**: correlation IDs first; metrics later (Epic 1.4).
- **Evolvability**: backward-compatible schema evolution.

## Decisions (ADRs inlined)

### Decision: Shared Contract Artifact is allowed (narrow exception)
**Context**: The broader thesis documentation emphasizes microservice independence and “zero shared dependencies”, but Epic 1.1 explicitly requires a shared library/module for contracts.

**Choice**:
- Establish a **Shared Contract Artifact** as the only shared dependency.
- Restrict it to: Avro schemas, envelope definition, generated bindings.
- Forbid: domain/business logic, service-to-service imports, shared runtime logic beyond serialization and correlation helpers.

**Rationale**:
- Keeps integration stable and measurable.
- Enables fast expansion (new consumers) without re-integrating every pair of services.

**Consequences**:
- Introduces a governance surface: versioning and compatibility must be managed.

### Decision: Contract strategy = Standardize across services (Option A)
**Context**: Target is a walking skeleton with minimal moving parts.

**Choice**:
- Adopt a single canonical topic taxonomy and one event envelope for MVP.

**Alternatives**:
- Adapter/bridge service to map service-local schemas (rejected for MVP due to added moving parts).

### Decision: Schema compatibility mode
**Choice**:
- Schema Registry compatibility MUST be set to `BACKWARD` (or stricter) for MVP subjects.

### Decision: Schema Registry subject naming strategy (MVP)
**Choice**:
- Subject naming MUST use `TopicNameStrategy`.
- For topic `X`, the value subject is `X-value` (e.g., `speech.audio.ingress-value`).

**Rationale**:
- Minimizes ambiguity for independent service teams and avoids drift between record names and topic routing in the hard MVP.

### Decision: Canonical naming must be explicit
**Context**: The roadmap names `AudioProcessingEvent`, while existing draft planning references `AudioInputEvent`.

**Requirement**:
- Pick ONE canonical audio-ingress event name and topic naming scheme and keep it consistent across docs and services.

**Choice (pinned)**:
- Canonical audio-ingress event is `AudioInputEvent`.

### Decision: Message size policy (MVP)
**Choice**:
- Kafka broker max message size: 2 MiB (`message.max.bytes=2097152`) for local dev MVP.
- `AudioInputEvent` inline audio payload hard cap: 1.5 MiB.
- Larger-than-cap audio is rejected in v0.1.0 (reference/URI pattern is deferred).

### Decision: ASR topic bindings are non-negotiable (Epic 1.2)
**Context**: The ASR service is the first real microservice to bind to the shared contract. Topic-name drift between plans and the shared infra smoke test will break integration.

**Choice**:
- ASR MUST consume `AudioInputEvent` from topic `speech.audio.ingress`.
- ASR MUST publish `TextRecognizedEvent` to topic `speech.asr.text`.

**Consequences**:
- Any alternate topic names (e.g., `audio-input`, `text-recognized`) are treated as a plan defect unless an explicit architecture change is approved.

### Decision: Supported audio format for MVP
**Context**: Allowing multiple formats expands the decoding surface area and increases integration ambiguity.

**Choice**:
- For MVP, `AudioInputEvent.payload.audio_format` MUST be `"wav"`.
- If `audio_format` is not `"wav"`, services MUST log and drop the event (no crash).

**Alternatives**:
- Best-effort decode multiple formats (rejected for MVP due to non-determinism and operational complexity).

### Decision: Failure signaling (MVP)
**Context**: Introducing new error-event schemas or DLQ patterns in Epic 1.2 increases contract surface area and coordination cost.

**Choice**:
- For MVP, ASR failures (oversize payloads, empty payloads, decode errors, model errors) MUST be handled by **logging + dropping** the event.
- The system MUST NOT introduce new error-event schemas in Epic 1.2 without an explicit architecture decision.

### Decision: Delivery semantics (MVP)
**Context**: Kafka consumer processing is typically at-least-once. Exactly-once processing requires additional infrastructure and complexity.

**Choice**:
- MVP processing semantics are **at-least-once**; duplicate outputs are possible.
- Downstream services and demos MUST tolerate duplicates (use `correlation_id` for traceability; dedupe is out-of-scope for MVP).

## Recommendations
- Keep event set minimal for v0.1.0: audio ingress + recognized text + translated text.
- Avoid streaming/chunking until after the hard MVP.
