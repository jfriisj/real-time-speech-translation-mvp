# System Architecture — Universal Speech Translation Platform

**Last Updated**: 2026-01-27

## Changelog

| Date | Change | Rationale | Plan |
|------|--------|-----------|------|
| 2026-01-15 | Initial architecture baseline + decisions for Epic 1.1 | Establishes the Hard MVP backbone (Kafka + Schema Registry + shared contract) and constrains scope to avoid creep | Epic 1.1 (Shared Infrastructure & Contract Definition) |
| 2026-01-15 | Pinned canonical `AudioInputEvent`, topic taxonomy, and SR governance notes | Removes naming drift; makes contract + registry behavior explicit for downstream epics | Epic 1.1 (post-delivery alignment) |
| 2026-01-15 | Epic 1.2 pre-planning guardrails (topics, audio format, failure signaling, delivery semantics) | Prevents downstream integration drift between plans and the v0.1.0 infrastructure contract | Epic 1.2 (ASR Service) |
| 2026-01-19 | Added MVP+ extension guardrails (Gateway, VAD, TTS, speaker context) | Ensures planned pipeline additions do not break v0.2.x reproducibility and makes voice-cloning context propagation explicit | v0.3.0–v0.4.0 (Epics 1.5–1.7) |
| 2026-01-19 | Epic 1.6 VAD pre-planning constraints (segmentation semantics + ordering) | Prevents non-deterministic ASR behavior and avoids schema/topic drift before planning | Epic 1.6 (VAD Service) |
| 2026-01-19 | Added QA integration points + failure-mode checklist for VAD stage | Improves test coverage at service boundaries (SR/Kafka/VAD/ASR) and reduces regressions during v0.4.0 hardening | Plan 009 (VAD) |
| 2026-01-25 | Epic 1.7 TTS pre-planning constraints (AudioSynthesisEvent payload strategy, object-store guardrails) | Prevents Kafka payload cap violations and clarifies how synthesized audio and speaker context are transported | Epic 1.7 (TTS Service) |
| 2026-01-25 | Epic 1.7 TTS model pivot to Kokoro ONNX + pluggable synthesizer requirement | Stabilizes CPU/GPU runtime via ONNX and preserves future ability to swap to IndexTTS/Qwen without contract changes | Findings 011 |
| 2026-01-27 | Epic 1.7 TTS governance gaps recorded (missing Plan 010 + evidence artifacts) | Restores documentation traceability for contract decisions and release gating; prevents “phantom requirements” | Findings 012 |
| 2026-01-27 | Plan 010 (TTS) pre-implementation review | Confirms architectural fit; requires plan deltas to avoid premature storage dependency and to align payload thresholds with Kafka invariants | Findings 015 |
| 2026-01-27 | Epic 1.8 artifact persistence (MinIO/S3) pre-planning constraints | Approves claim-check support to keep Kafka payloads small and enable auditability, with required retention + security guardrails | Findings 013 |
| 2026-01-27 | Plan 010 (TTS) re-review after contract additions | Flags required alignment fixes (speaker context pass-through, SR compatibility wording, retention defaults, `audio_uri` ownership) before implementation | Findings 017 |
| 2026-01-27 | Plan 010 (TTS) pre-implementation review (Rev 29) | Confirms architectural fit; requires pinning topic/subject naming and repairing acceptance criteria text to prevent integration drift | Findings 019 |
| 2026-01-27 | Scope shift: Claim Check enablement pulled into Epic 1.7 | Records that v0.5.0 introduces object storage/Claim Check for TTS output as a pilot; Epic 1.8 becomes the platform-wide rollout | Findings 020 |

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
- Planned: Ingress Gateway: external streaming ingress (WebSocket/gRPC) → `AudioInputEvent`
- Planned: VAD Service: silence removal / segmentation (`AudioInputEvent` → `SpeechSegmentEvent`)
- Planned: TTS Service: translated text → synthesized audio (`TextTranslatedEvent` → `AudioSynthesisEvent`)
	- Runtime: Kokoro-82M (ONNX) for CPU/GPU stability
	- Architecture: pluggable synthesizer backend (factory) to allow future model swaps

### Planned supporting infrastructure (v0.3.0+)
- MAY introduce an object store (e.g., MinIO/S3) if payloads must be transported by URI rather than inline (speaker reference context and/or synthesized audio output).
	- For v0.6.0+, object storage is the preferred mechanism for persisting intermediate artifacts for thesis auditability (Claim Check pattern).

## Runtime Flows (Hard MVP)
1. Producer publishes `AudioInputEvent` (topic: `speech.audio.ingress`) with a `correlation_id`.
2. ASR consumes audio event and publishes `TextRecognizedEvent` preserving `correlation_id`.
3. Translation consumes `TextRecognizedEvent` and publishes `TextTranslatedEvent` preserving `correlation_id`.
4. Consumer/CLI prints final result (and later attaches latency metrics).

## Runtime Flows (Planned MVP+ / v0.3.0)
1. External devices connect to the **Ingress Gateway** (WebSocket/gRPC).
2. Gateway publishes `AudioInputEvent` to `speech.audio.ingress` with `correlation_id`.
3. **VAD Service** consumes `AudioInputEvent`, removes silence, and publishes `SpeechSegmentEvent`.
4. **ASR Service** consumes `SpeechSegmentEvent` and publishes `TextRecognizedEvent`.
5. **Translation Service** consumes `TextRecognizedEvent` and publishes `TextTranslatedEvent`.
6. **TTS Service** consumes `TextTranslatedEvent` and publishes `AudioSynthesisEvent` (and/or an optional client-facing stream).

## Data Boundaries & Contracts
- All inter-service data crosses boundaries as **Avro-encoded events**.
- Schema Registry subjects are the source of truth for compatibility.
- Correlation tracking is mandatory: `correlation_id` MUST be present on all MVP events.

### MVP Topic Taxonomy
- `speech.audio.ingress` → `AudioInputEvent`
- `speech.asr.text` → `TextRecognizedEvent`
- `speech.translation.text` → `TextTranslatedEvent`

### Planned Topic Taxonomy (v0.3.0+)
- `speech.audio.speech_segment` → `SpeechSegmentEvent`
- `speech.tts.audio` → `AudioSynthesisEvent`

### Speaker Context (Planned)
Speaker context is optional metadata originating at ingress and usable at TTS.

Architecture requirements:
- Speaker context MUST be optional and MUST NOT be required for baseline TTS functionality.
- Intermediate services (ASR, Translation) MUST treat speaker context as pass-through metadata.
- Speaker context is treated as sensitive data; retention MUST be time-bounded (session-scoped) if stored.

Implementation note (v0.5.0):
- The Kokoro ONNX baseline MAY use `speaker_id` to select a style/voice.
- `speaker_reference_bytes` MUST still be propagated end-to-end for future backends (IndexTTS/Qwen) even if the baseline does not consume it.

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

### Decision: Claim Check pattern is introduced for audio artifacts (v0.5.0 pilot; v0.6.0 rollout)
**Context**: Persisting audio artifacts (ingress audio, VAD segments, TTS output) improves auditability and avoids Kafka payload failures for non-trivial durations.

**Choice (guardrail)**:
- Blob-carrying events MUST support either inline bytes OR an external URI/reference (exactly one set) with explicit `content_type` metadata.
- **v0.5.0 pilot**: TTS output (`AudioSynthesisEvent`) may use Claim Check to prevent Kafka payload invariant violations.
- **v0.6.0 rollout**: the pipeline may expand Claim Check / artifact persistence across ingress audio and VAD segments for thesis-grade auditability.
- The system MUST remain operable with object storage disabled (baseline inline path remains valid where size permits).

**Rationale**:
- Preserves Kafka throughput and reduces broker pressure.
- Enables thesis-grade “inspect each stage” workflows.

**Consequences**:
- Introduces new dependency and failure modes; services must degrade gracefully if URIs expire/missing.

### Decision: Object storage retention and URI security are mandatory (v0.6.0)
**Choice (guardrail)**:
- Artifact retention MUST be time-bounded (default target: 24 hours) and configurable by environment.
- Presigned URLs (if used) MUST NOT be logged in full and MUST be time-bounded.

**Consequences**:
- Adds governance requirements (lifecycle rules, internal-only endpoints by default in dev).

### Decision: ASR topic bindings are non-negotiable (Epic 1.2)
**Context**: The ASR service is the first real microservice to bind to the shared contract. Topic-name drift between plans and the shared infra smoke test will break integration.

**Choice**:
- ASR MUST consume `AudioInputEvent` from topic `speech.audio.ingress`.
- ASR MUST publish `TextRecognizedEvent` to topic `speech.asr.text`.

**Consequences**:
- Any alternate topic names (e.g., `audio-input`, `text-recognized`) are treated as a plan defect unless an explicit architecture change is approved.

### Decision: VAD introduces a new segmentation event (v0.3.0+)
**Context**: v0.3.0 introduces a VAD stage to reduce downstream compute and latency. Changing the existing `AudioInputEvent` semantics or reusing `speech.audio.ingress` for both raw and segmented payloads risks breaking v0.2.x reproducibility.

**Choice**:
- Introduce a new event type `SpeechSegmentEvent` on a new topic `speech.audio.speech_segment`.
- Preserve `AudioInputEvent` and `speech.audio.ingress` for ingress and v0.2.x compatibility.

**Consequences**:
- ASR will migrate to consume `SpeechSegmentEvent` for v0.3.0+, but legacy flow can remain for benchmarking and regression testing.

### Decision: `SpeechSegmentEvent` must be self-contained + ordered (Epic 1.6)
**Context**: VAD emits multiple segments per request. Kafka ordering guarantees apply only within a partition. If segments reorder (or require the original full audio), downstream ASR behavior becomes non-deterministic and hard to test.

**Choice**:
- `SpeechSegmentEvent` payload MUST be self-contained (each segment is independently consumable by ASR without requiring the original full audio).
- Segment events MUST preserve the original `correlation_id`.
- Segment events MUST carry offsets relative to the original audio (e.g., `start_ms`, `end_ms`) and a `segment_index`.
- Producers MUST key segment events by a stable per-request key (recommended: `correlation_id`) to keep ordering per request.

**Alternatives**:
- Reuse `AudioInputEvent` for segmented audio (rejected: breaks v0.2.x reproducibility and increases semantic ambiguity).
- Run VAD inside ASR (rejected: couples policy and compute, limits independent scaling).

**Consequences**:
- Adds minimal schema requirements but substantially improves determinism, testability, and observability.

### Decision: Speaker reference context propagation (v0.3.0+)
**Context**: IndexTTS-2 voice cloning requires speaker reference context captured at ingress but consumed at the end of the pipeline.

**Choice (guardrail)**:
- Speaker context MUST be propagated either:
	- Inline as a small optional reference clip/embedding in the event envelope (preferred for MVP+ simplicity), OR
	- As an optional URI/ID referencing an external object store (only if inline propagation becomes a bottleneck).

**Rationale**:
- Prevents passing full raw audio across every stage while enabling voice cloning.
- Keeps the architecture explicit about added dependencies and privacy implications.

**Consequences**:
- Requires schema evolution discipline (optional fields or new event types) and clear retention/cleanup rules if URIs are used.

### Decision: TTS audio output transport strategy (Epic 1.7)
**Context**: Kafka payload caps (2 MiB broker, 1.5 MiB inline payload cap) make it easy for synthesized audio to exceed limits depending on format and duration.

**Choice (guardrail)**:
- The platform MUST support a TTS output strategy that cannot violate the Kafka payload invariants.
- Preferred approach: `AudioSynthesisEvent` supports either inline `audio_bytes` OR an external `audio_uri` (exactly one set).

**Alternatives**:
- Inline-only output with aggressive max-duration caps (acceptable for very short demos, but fragile).
- Always-URI output (adds storage dependency even for small payloads).

**Consequences**:
- If URI output is used, an object store introduces lifecycle/TTL and failure modes (missing/expired URIs) that must degrade gracefully.
- Event schemas must remain backward-compatible by adding optional fields/unions.

### Decision: TTS synthesizer runtime strategy (Epic 1.7)
**Context**: The platform requires a stable runtime for inference on both CPU and GPU, and we want to preserve the option to swap TTS backends later without schema rewrites.

**Choice**:
- Implement the v0.5.0 TTS backend using **Kokoro-82M ONNX** (`onnx-community/Kokoro-82M-v1.0-ONNX`) on ONNX Runtime.
- Require a **pluggable synthesizer interface** (factory-selected) so future iterations can switch to `IndexTeam/IndexTTS-2` or `Qwen3-TTS` without changing event contracts.

**Consequences**:
- ONNX Runtime becomes an explicit dependency for the TTS service.
- Model/backend selection becomes a deployment/config decision; orchestration code must not import model-specific libraries directly.

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
