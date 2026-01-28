# Universal Speech Translation Platform - Product Roadmap

**Last Updated**: 2026-01-29
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
| 2026-01-27 10:00 | Scope Shift (Epics 1.7 & 1.8) | Pulled MinIO/Claim Check infrastructure from Epic 1.8 into Epic 1.7 to support TTS large audio requirements. |
| 2026-01-27 10:30 | Started Epic 1.8 | Commencing platform-wide rollout of Claim Check persistence (S3/MinIO) for deep auditing/Thesis validation. |
| 2026-01-28 10:00 | Added Epic 1.9 / Release v0.4.1 | Defined explicit work item for Service Startup Resilience following Translation Service fix (Plan 011). |
| 2026-01-28 10:15 | Resequencing (Resilience First) | Paused Epics 1.7 (TTS) and 1.8 (Persistence) to prioritize Epic 1.9 (Resilience) and enforce strict dependency order (1.9 -> 1.8 -> 1.7). |
| 2026-01-28 12:00 | Released v0.4.1 | Delivered Epic 1.9 (Service Startup Resilience); Added Epic 1.9.1 (Hardening) to Backlog for future deterministic verification. |
| 2026-01-28 17:00 | Plan 029 retrospective closed | Recorded Plan 029 (uv-first test workflow) as committed for v0.5.0 and updated the release tracker accordingly. |
| 2026-01-28 18:10 | Plan 028 committed locally | Stage 1 commit created for Plan 028; v0.5.0 now has all targeted plans committed locally and is ready for release approval. |
| 2026-01-28 18:20 | Stage 2 release approved (v0.5.0) | User requested Stage 2 release execution (tag/push/publish) now that all targeted plans are committed locally. |
| 2026-01-29 09:00 | Released v0.5.0 | Stage 2 executed (tag/push complete); rolled Active Release Tracker forward to v0.6.0. |

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
**Status**: In Progress

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
- [ ] **Diagnostic**: Full unit and E2E test suite executed with passed results.
- [ ] **Stabilization**: Root cause of reported instability identified and fixed.

**Status Notes**:
- 2026-01-28: Reopened to address regression/instability. Objective is to run full diagnostics (Unit + E2E) to isolate the failure mode.
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

## Release v0.4.1 - Stability & Resilience
**Status**: Released
**Released**: 2026-01-28
**Strategic Goal**: Eliminate startup race conditions and improve platform reliability independent of orchestration tools.

### Epic 1.9: Service Startup Resilience
**Priority**: P1
**Status**: Delivered

**User Story**:
As an Operator,
I want all microservices to autonomously wait for infrastructure dependencies (Schema Registry/Kafka),
So that the platform starts up reliably without crash loops, even without external orchestration delays.

**Business Value**:
- **Reliability**: Prevents "CrashLoopBackOff" in Kubernetes or failure in simple localized runs.
- **Portability**: Ensures services are robust regardless of deployment method (Compose, K8s, bare metal).

**Dependencies**:
- Pattern established in Translation Service (Plan 011).

**Acceptance Criteria**:
- [x] **ASR Service**: Implements bounded wait loop for Schema Registry.
- [x] **VAD Service**: Implements bounded wait loop for Schema Registry.
- [x] **TTS Service**: Implements bounded wait loop for Schema Registry.
- [x] **Gateway Service**: Implements bounded wait loop for Schema Registry.
- [x] Shared Library remains thin (logic lives in service main loops).

**Status Notes**:
- 2026-01-28: Delivered in v0.4.1. Success metric (single cold start) met; 10x determinism proof deferred to Epic 1.9.1.

---

## Release v0.5.0 - Synthesis (MVP+)
**Status**: Released (2026-01-28)
**Released**: 2026-01-28
**Target Release**: Completed (v0.5.0)

**Strategic Goal**: Complete the output loop with synthesis while stabilizing service startup resilience and QA infrastructure ahead of the next TTS expansion.

### Delivered Work
- **Plan 028**: Kafka consumer recovery hardening (shared tuning helper, structured telemetry, and steady-state vs cold-start smoke instrumentation).
- **Plan 029**: uv-first reproducible QA workflow (runbook, dependency alignment, startup helper contract cleanup) that unblocks deterministic testing for v0.5.0.

### Epic 1.7: Text-to-Speech (TTS) (Stable Outcome)
**Priority**: P1
**Status**: Paused (Waiting for 1.9 & 1.8)

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
- Epic 1.9 (Service Resilience) - *Required for stable testing*.
- Epic 1.8 (Artifact Persistence) - *Required for large audio payload handling*.
- **Infrastructure**: MinIO/S3 and ObjectStorage utility (pulled forward from Epic 1.8).

**Acceptance Criteria**:
- [x] **Architecture**: data flow designed to propagate "Source Audio Sample" (or embedding) from Ingress -> TTS for cloning context.
- [x] **Infrastructure**: MinIO added to `docker-compose.yml` and `ObjectStorage` added to shared lib (implements Epic 1.8 core).
- [ ] TTS Service consumes `TextTranslatedEvent`.
- [ ] TTS Service uses `onnx-community/Kokoro-82M-v1.0-ONNX` (or stable equivalent).
- [ ] TTS Service produces `AudioSynthesisEvent` (using Claim Check pattern for payloads > 1.25 MiB).
- [x] **Pluggability**: Synthesizer implementation accepts a config switch (Factory pattern) for future model support.
- [ ] Basic duration/speed control implemented.

**Status Notes**:
- 2026-01-28: Stage 2 release executed; Plans 028 and 029 shipped in v0.5.0, delivering Kafka consumer resilience and the uv-first QA workflow required before Epic 1.7 (TTS) can resume.
 2026-01-27: Infrastructure scope expanded. Plan 010 (Rev 31) pulls MinIO and Claim Check logic into this epic to handle large audio synthesis without blocking on v0.6.0.

---

## Release v0.6.0 - Auditing & Persistence
**Target Date**: Upcoming
**Strategic Goal**: Enable deep auditing by persisting intermediate artifacts (audio/text) effectively implementing "Claim Check" pattern to keep Kafka request size low.

### Epic 1.8Paused (Waiting for 1.9)

**User Story**:
As a Researcher,
I want to save the intermediate audio input, VAD segments, and synthesized speech to object storage (S3/MinIO),
So that I can manually inspect the quality of each stage and ensure the Event Bus is not clogged with large audio payloads.

**Business Value**:
- **Thesis Validation**: Provides physical evidence of the pipeline's intermediate states.
- **Debugging**: Allows "replay" or inspection of specific failure cases (e.g., "Why did ASR fail? Let's listen to the VAD segment").
- **Scalability**: Removes large blobs from Kafka (Claim Check Pattern), preventing throughput degradation.

**Dependencies**:
- Epic 1.9 (Service Resilience) - *Required for stable testing*.: Removes large blobs from Kafka (Claim Check Pattern), preventing throughput degradation.

**Dependencies**:
- Epic 1.1 (Shared Lib needs `ObjectStorage` support - *Delivered in v0.5.0*).
- MinIO service in Docker Compose (*Delivered in v0.5.0*).

**Acceptance Criteria**:
- [x] MinIO added to `docker-compose.yml` (Done in Epic 1.7).
- [x] `ObjectStorage` utility in Shared Lib wired to environment variables (Done in Epic 1.7).
- [ ] Pipeline Services (Gateway, VAD, ASR) configured to optionally offload blobs to S3.
- [ ] Events updated to carry `payload_url` (optional) alongside or instead of inline bytes.

---

### Epic 1.9.1: Service Startup Resilience Hardening
**Priority**: P2
**Status**: In Progress

**User Story**:
As a System Architect,
I want to statistically prove the reliability of service startup (e.g., 10 consecutive flawless starts),
So that I can certify the platform as "production-hardened" rather than just "functional".

**Business Value**:
- **Confidence**: Certifies 99.9% reliability for automated deployments.
- **Thesis Validation**: Provides statistical rigor for reliability claims.

**Dependencies**:
- Epic 1.9 (Base resilience logic).
- Automated CI environment capable of rapid restart loops.

**Status Notes**:
- 2026-01-28: Plan 029 retrospective closed; uv-first test workflow committed for v0.5.0.

---

### Epic 
## Backlog / Future Consideration
**Strategic Note**: These items are valuable but strictly out of scope for the Hard MVP to ensure Thesis delivery date is met.

### Epic 3.0: Dynamic Model Loading
*Allow changing ASR/Translation models on the fly via control events.*

### Epic 3.1: Stream Processing (Real-time)
*Switch from block-based processing to true streaming (gRPC or chunked Kafka events).*

### Epic 1.5b: Ingress Gateway — Phase 2 (gRPC)
*Add gRPC endpoint support to the Gateway service for high-performance inter-service or mobile client communication.*

---

## Active Release Tracker

**Current Working Release**: v0.6.0

| Plan ID | Title | UAT Status | Committed |
|---------|-------|------------|----------|
| 022 | Artifact Persistence (Claim Check) Platform Rollout | Pending | ✗ |

**Release Status**: 0 of 1 plans committed
**Ready for Release**: No
**Release Approval**: Not requested
**Blocking Items**: Plan 022 needs implementation + QA/UAT + Stage 1 commit

### Previous Releases
| Version | Date | Plans Included | Status |
|---------|------|----------------|--------|
| v0.5.0 | 2026-01-28 | 028, 029 | Released |
