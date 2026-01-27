# Universal Speech Translation Platform - Product Roadmap

**Last Updated**: 2026-01-19
**Roadmap Owner**: Roadmap Agent
**Strategic Vision**: Deliver a scalable, event-driven platform for real-time speech translation that demonstrates low-latency orchestration of independent AI microservices. The focus is on architectural proof, measurable performance, and expandability through shared contracts, serving as a robust foundation for academic research and future commercial application.

## Change Log
| Date & Time | Change | Rationale |
|-------------|--------|-----------|
| 2026-01-15 10:00 | Initial Roadmap Creation | Defining Hard MVP scope based on Thesis MVP Plan |
| 2026-01-15 19:30 | Epic 1.1 Delivered & AC Update | Updated status to Delivered; renamed AudioProcessingEvent to AudioInputEvent per Retrospective 001 findings. |
| 2026-01-15 20:30 | Released v0.1.0 & Rescoped v0.2.0 | Release v0.1.0 completed (Infrastructure); moved Services to v0.2.0 to reflect iterative delivery pipeline. |
| 2026-01-19 08:30 | Released v0.2.0 (Core Services) | Delivered Epic 1.2 (ASR) and Epic 1.3 (Translation) establishing the full event pipeline. |
| 2026-01-19 15:30 | Added v0.2.1 (Traceability) | Created a patch release entry for Epic 1.4 measurement tooling and governance artifacts. |
| 2026-01-19 16:00 | Sequencing Validation (PI-003) | Confirmed process improvements (Analyst Checks, Planner Stubs) do not affect v0.3.0 delivery timeline. |
| 2026-01-19 17:00 | Released v0.3.0 (Ingress) | Delivered Epic 1.5 (Phase 1); Moved Epics 1.6 & 1.7 to new v0.4.0 Release to reflect iterative delivery. |
| 2026-01-25 10:00 | Pivoted Epic 1.7 to Kokoro ONNX | Changed TTS model strategy from IndexTTS-2 to Kokoro ONNX for runtime stability; mandated pluggable architecture for future swaps. |

---

## Release v0.1.0 - Shared Infrastructure Foundation
**Released**: 2026-01-15
**Strategic Goal**: Establish the "Walking Skeleton" foundation—a functional event bus and schema contract that allows subsequent services to integrate without coupling.

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

## Release v0.2.0 - Core Services (The 'Walking Skeleton')
**Released**: 2026-01-19
**Strategic Goal**: Implement the core functional services (ASR, Translation) on top of the shared infrastructure to achieve end-to-end data flow.

### Epic 1.2: Audio-to-Text Ingestion (ASR Service)
**Priority**: P0
**Status**: Delivered

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
- [x] ASR Service consumes `AudioInputEvent` (or accepts raw audio input for MVP demo).
- [x] ASR Service successfully produces `TextRecognizedEvent` to Kafka.
- [x] Output events contain correct `correlation_id` from input.
- [x] Basic error handling (e.g., empty audio) produces error logs/events.

---

### Epic 1.3: Text-to-Text Translation (Translation Service)
**Priority**: P0
**Status**: Delivered

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
- [x] Translation Service consumes `TextRecognizedEvent`.
- [x] Translation Service produces `TextTranslatedEvent`.
- [x] Translation logic supports at least one language pair (e.g., EN -> ES) reliably.
- [x] `correlation_id` is preserved.

**Status Notes**:
- 2026-01-19: Implementation exceeded MVP scope by integrating real Hugging Face model (CPU-optimized) instead of mock, validating better functional value.

---

---

## Release v0.2.1 - Traceability & Thesis Validation
**Status**: Released
**Released**: 2026-01-19

**Strategic Goal**: Establish a traceability probe and reproducible latency measurement methodology for thesis validation without changing core services.

### Epic 1.4: End-to-End Traceability & Latency (Shared / Integration)
**Priority**: P0
**Status**: Delivered

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
- [x] A simple CLI or script exists to inject audio and listen for the final event.
- [x] Logs/Events show timestamps at Ingress, ASR-Complete, and Translation-Complete.
- [x] End-to-end latency is calculated and visible.
- [x] 100 sequential requests complete without dropping the correlation chain.

**Status Notes**:
- Baseline run (N=100) recorded 100/100 success, P50=1045ms, P90=1155.8ms, P99=1402.73ms and is documented in [docs/benchmarks/001-mvp-latency-baseline.md](docs/benchmarks/001-mvp-latency-baseline.md).
- Release doc [agent-output/releases/v0.2.1.md](agent-output/releases/v0.2.1.md) records tagging, QA/UAT sign-offs, and benchmark publication.
- Retrospective [agent-output/retrospectives/004-traceability-and-latency-retrospective.md](agent-output/retrospectives/004-traceability-and-latency-retrospective.md) captured lessons on warmup/cold-start handling and roadmap governance.
---

## Release v0.3.0 - Ingress Gateway (Connectivity)
**Status**: Released
**Released**: 2026-01-19

**Strategic Goal**: Transform the "Walking Skeleton" into a "Usable Platform" by adding client connectivity (WebSocket) to decouple external clients from Kafka.

### Epic 1.5: Ingress Gateway — Phase 1 (WebSocket)
**Priority**: P1
**Status**: Delivered

**User Story**:
As a Client Developer (Web/Mobile),
I want to stream audio via WebSocket to a single entry point,
So that I can connect external devices (microphones, browsers) to the pipeline without direct Kafka access or local CLI scripts.

**Scope Note**: Phase 1 delivered WebSocket ingress. gRPC support deferred to Epic 1.5b.

**Business Value**:
- **Usability**: Moves from "CLI-based demo" to "Real-world Platform".
- **Security**: Decouples external clients from internal message bus.

**Acceptance Criteria**:
- [x] Gateway Service exposes WebSocket endpoint for audio streaming.
- [x] Gateway produces `AudioInputEvent` to Kafka.
- [x] Supports multiple concurrent client connections.
- [x] Security controls enforced (DoS protection, container hardening, network isolation).

**Deferred to Follow-up Epic**:
- gRPC endpoint support (Epic 1.5b)

---

## Release v0.4.0 - Optimization (MVP+)
**Status**: Released
**Released**: 2026-01-25

**Strategic Goal**: Optimize throughput via silence filtering.

### Epic 1.6: Voice Activity Detection (VAD) Service
**Priority**: P1
**Status**: Delivered

**User Story**:
As a System Architect,
I want to filter out silence *before* the heavy ASR service,
So that I don't waste GPU/CPU cycles transcribing background noise and latency is improved.

**Business Value**:
- **Performance**: Directly supports Thesis hypothesis on "efficiency".
- **Cost**: Reduces token/compute usage on downstream models.
- **Latency**: Smaller payloads = faster transit.

**Dependencies**:
- Placed *after* Gateway (Epic 1.5) and *before* ASR (Epic 1.2).

**Acceptance Criteria**:
- [x] VAD Service consumes `AudioInputEvent` from Gateway.
- [x] VAD Service uses `onnx-community/silero-vad` model (ONNX runtime) for low-latency detection.
- [x] VAD Service detects speech segments.
- [x] VAD Service produces `SpeechSegmentEvent` (only containing speech).
- [x] ASR Service updated to consume `SpeechSegmentEvent` instead of raw `AudioInputEvent`.

---

## Release v0.5.0 - Synthesis (MVP+)
**Status**: Planned
**Target Release**: Upcoming

**Strategic Goal**: Complete the output loop with synthesis.

### Epic 1.7: Text-to-Speech (TTS) (Stable Outcome)
**Priority**: P1
**Status**: In Progress

**User Story**:
As a User,
I want to hear the translated text spoken naturally,
So that I can consume the translation hands-free.

**Business Value**:
- **UX**: Completes the "Speech-to-Speech" loop.
- **Stability**: Uses `Kokoro-82M` (ONNX) to ensure reliable runtime on both CPU (Thesis Requirement).
- **Extensibility**: Establishes a pluggable architecture (Factory Pattern) allowing future swaps to `IndexTTS-2` or `Qwen3-TTS` without service rewriting.

**Dependencies**:
- Epic 1.3 (Translation output).

**Acceptance Criteria**:
- [x] **Architecture**: data flow designed to propagate "Source Audio Sample" (or embedding) from Ingress -> TTS for cloning context.
- [ ] TTS Service consumes `TextTranslatedEvent`.
- [ ] TTS Service uses `onnx-community/Kokoro-82M-v1.0-ONNX` (or stable equivalent).
- [ ] TTS Service produces `AudioSynthesisEvent`.
- [x] **Pluggability**: Synthesizer implementation accepts a config switch (Factory pattern) for future model support.
- [ ] Basic duration/speed control implemented.

**Status Notes**:
- 2026-01-25: Plan 010 finalized (Rev 8). Implementation started; Kokoro ONNX scaffolded; Schemas updated.

---

## Release v0.6.0 - Observability & Persistence (Thesis Validation)
**Status**: Planned
**Strategic Goal**: Enable deep auditing of the pipeline by persisting intermediate artifacts (audio/text) effectively implementing "Claim Check" pattern to keep Kafka request size low.

### Epic 1.8: Artifact Persistence (S3/MinIO)
**Priority**: P2
**Status**: Planned

**User Story**:
As a Researcher,
I want to save the intermediate audio input, VAD segments, and synthesized speech to object storage (S3/MinIO),
So that I can manually inspect the quality of each stage and ensure the Event Bus is not clogged with large audio payloads.

**Business Value**:
- **Thesis Validation**: Provides physical evidence of the pipeline's intermediate states.
- **Debugging**: Allows "replay" or inspection of specific failure cases (e.g., "Why did ASR fail? Let's listen to the VAD segment").
- **Scalability**: Removes large blobs from Kafka (Claim Check Pattern), preventing throughput degradation.

**Dependencies**:
- Epic 1.1 (Shared Lib needs `ObjectStorage` support - *Already present*).
- MinIO service in Docker Compose.

**Acceptance Criteria**:
- [ ] MinIO added to `docker-compose.yml`.
- [ ] `ObjectStorage` utility in Shared Lib wired to environment variables.
- [ ] Pipeline Services (Gateway, VAD, ASR, TTS) configured to optionally offload blobs to S3.
- [ ] Events updated to carry `payload_url` (optional) alongside or instead of inline bytes.

---

## Backlog / Future Consideration
**Strategic Note**: These items are valuable but strictly out of scope for the Hard MVP to ensure Thesis delivery date is met.

### Epic 3.0: Dynamic Model Loading
*Allow changing ASR/Translation models on the fly via control events.*

### Epic 3.1: Stream Processing (Real-time)
*Switch from block-based processing to true streaming (gRPC or chunked Kafka events).*

### Epic 1.5b: Ingress Gateway — Phase 2 (gRPC)
*Add gRPC endpoint support to the Gateway service for high-performance inter-service or mobile client communication.*
