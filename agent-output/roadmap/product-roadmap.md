# Universal Speech Translation Platform - Product Roadmap

**Last Updated**: 2026-01-15
**Roadmap Owner**: Roadmap Agent
**Strategic Vision**: Deliver a scalable, event-driven platform for real-time speech translation that demonstrates low-latency orchestration of independent AI microservices. The focus is on architectural proof, measurable performance, and expandability through shared contracts, serving as a robust foundation for academic research and future commercial application.

## Change Log
| Date & Time | Change | Rationale |
|-------------|--------|-----------|
| 2026-01-15 10:00 | Initial Roadmap Creation | Defining Hard MVP scope based on Thesis MVP Plan |
| 2026-01-15 19:30 | Epic 1.1 Delivered & AC Update | Updated status to Delivered; renamed AudioProcessingEvent to AudioInputEvent per Retrospective 001 findings. |

---

## Release v0.1.0 - The 'Hard MVP' Skeleton
**Target Date**: 2026-02-15
**Strategic Goal**: Establish the "Walking Skeleton"—a functional, event-driven pipeline that moves data end-to-end with correct correlation and schema validation. Prioritize architectural integrity over feature breadth.

### Epic 1.1: Shared Infrastructure & Contract Definition (Shared)
**Priority**: P0
**Status**: Delivered

**User Story**:
As a System Implementer,
I want a unified event bus and a strict Avro schema contract,
So that microservices can communicate reliably without direct dependencies or integration breakages.

**Business Value**:
- **Decoupling**: Enables independent service scaling and development.
- **Type Safety**: Prevents runtime errors caused by mismatched data formats.
- **Expandability**: Sets the standard (Shared Service) that allows new services (TTS, Sentiment) to plug in easily later.

**Dependencies**:
- Kafka & Schema Registry availability (local or deployed).

**Acceptance Criteria**:
- [x] Kafka and Schema Registry running locally via Docker Compose.
- [x] "Golden" Avro schemas defined for `AudioInputEvent`, `TextRecognizedEvent`, and `TextTranslatedEvent`.
- [x] Shared Python library/module created containing generated classes/models for these schemas.
- [x] Common `correlation_id` propagation logic active in the shared library.

**Constraints**:
- Must use Avro.
- Must use Confluent Schema Registry.

---

### Epic 1.2: Audio-to-Text Ingestion (ASR Service)
**Priority**: P0
**Status**: Planned

**User Story**:
As a User,
I want my speech audio to be captured and converted to text events,
So that the system has raw material to translate.

**Business Value**:
- **Core Capability**: First step in the value chain.
- **Modularity**: Isolates heavy processing (Whisper/etc.) from the rest of the flow.

**Dependencies**:
- Epic 1.1 (Shared Contracts).

**Acceptance Criteria**:
- [ ] ASR Service consumes `AudioInputEvent` (or accepts raw audio input for MVP demo).
- [ ] ASR Service successfully produces `TextRecognizedEvent` to Kafka.
- [ ] Output events contain correct `correlation_id` from input.
- [ ] Basic error handling (e.g., empty audio) produces error logs/events.

---

### Epic 1.3: Text-to-Text Translation (Translation Service)
**Priority**: P0
**Status**: Planned

**User Story**:
As a User,
I want recognized text to be translated into my target language,
So that I can understand the content.

**Business Value**:
- **Core Value Prop**: This is the "Translation" in "Translation Platform".
- **Scalability**: Allows this CPU/GPU-bound task to scale independently of audio processing.

**Dependencies**:
- Epic 1.1 (Shared Contracts).
- Epic 1.2 (for end-to-end testing, though traceable independently).

**Acceptance Criteria**:
- [ ] Translation Service consumes `TextRecognizedEvent`.
- [ ] Translation Service produces `TextTranslatedEvent`.
- [ ] Translation logic supports at least one language pair (e.g., EN -> ES) reliably.
- [ ] `correlation_id` is preserved.

---

### Epic 1.4: End-to-End Traceability & Latency (Shared / Integration)
**Priority**: P0
**Status**: Planned

**User Story**:
As a Researcher/Thesis Author,
I want to trace a single request from Audio In to Translated Text Out and measure the time,
So that I can validate the performance claims of the architecture.

**Business Value**:
- **Thesis Success**: Provides the data needed for the "measurable performance" goal.
- **Observability**: Proves the "Walking Skeleton" is actually walking.

**Dependencies**:
- Epics 1.1, 1.2, 1.3.

**Acceptance Criteria**:
- [ ] A simple CLI or script exists to inject audio and listen for the final event.
- [ ] Logs/Events show timestamps at Ingress, ASR-Complete, and Translation-Complete.
- [ ] End-to-end latency is calculated and visible.
- [ ] 100 sequential requests complete without dropping the correlation chain.

---

## Release v0.2.0 - Expand & Speak (MVP+)
**Target Date**: TBD
**Strategic Goal**: Demonstrate the "Expandability" of the shared architecture by adding a new modality (TTS) without rewriting existing services.

### Epic 2.1: Speech Synthesis (TTS Service)
**Priority**: P1
**Status**: Planned

**User Story**:
As a User,
I want to hear the translated text spoken,
So that I can consume the translation hands-free / naturally.

**Business Value**:
- **UX**: Completes the "Speech-to-Speech" loop.
- **Architecture Proof**: Proves that adding a 3rd service is easy because of the Shared Contracts (Epic 1.1).

**Dependencies**:
- Epic 1.3 (Translation output).

**Acceptance Criteria**:
- [ ] TTS Service consumes `TextTranslatedEvent`.
- [ ] TTS Service produces `AudioSynthesisEvent` (or serves audio file/stream).
- [ ] Integrated into the E2E latency measurement (Epic 1.4 update).

---

## Backlog / Future Consideration
**Strategic Note**: These items are valuable but strictly out of scope for the Hard MVP to ensure Thesis delivery date is met.

### Epic 3.0: Dynamic Model Loading
*Allow changing ASR/Translation models on the fly via control events.*

### Epic 3.1: Stream Processing (Real-time)
*Switch from block-based processing to true streaming (gRPC or chunked Kafka events).*

### Epic 3.2: API Gateway & Auth
*Secure ingestion layer for public-facing usage.*
