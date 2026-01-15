# MVP-First Plan (Thesis)
## Universal Speech Translation Platform

This document defines a **strict Minimum Viable Product (MVP)** for the master’s thesis project and the **minimum integration contract** required for the services to work together end-to-end.

It is intentionally narrow: anything not explicitly required for the MVP is **out of scope** for the first deliverable.

## 1) MVP Goal

Deliver a demonstrable, end-to-end **event-driven pipeline** that:

1. Accepts live or recorded audio input
2. Performs speech recognition (ASR) to text
3. Translates text to a target language
4. Returns the translated result (text is mandatory; synthesized speech is optional)

Primary thesis focus: **measurable performance optimization** (latency), **scalability** (throughput/concurrency), and **robustness** (fault handling) in an event-driven microservice pipeline.

## 2) MVP Non-Goals (Explicitly Out of Scope)

These items are not required for the MVP and should not block completion:

- A full UI/UX client application (a simple CLI/script publisher + consumer is enough)
- Advanced security (mTLS, OAuth, fine-grained auth), beyond basic local-dev defaults
- Model training / new model development
- Multi-region deployment, service mesh, complex Kubernetes manifests
- Extensive cultural adaptation and bias detection workflows
- Full streaming audio “production-grade” UX (optional later)

## 3) Minimal Architecture (Services and Responsibilities)

### Required services (MVP)

- **ASR Service**: consumes audio events → produces recognized text events
- **Translation Service**: consumes recognized text → produces translated text

### Optional services (MVP+)

- **TTS Service**: consumes translated text → produces synthesized audio

### Infrastructure

- **Kafka** (event bus)
- **Schema Registry** (Avro schema governance)

## 4) MVP Integration Contract (Topics + Schemas)

### Critical decision: contract strategy

For the MVP, choose **one** of these strategies and stick to it end-to-end:

- **A. Standardize contract across services (recommended)**
  - One canonical topic taxonomy
  - One canonical Avro envelope
  - Services publish/consume the same schema subjects

- **B. Keep service-local contracts, add an adapter**
  - Services keep their current topics/schemas
  - A thin “event bridge” maps between ASR → Translation → (TTS)

For the thesis MVP, Strategy A reduces moving parts and simplifies evaluation.

### MVP event types (minimum set)

#### 1) ASR → Translation
- Logical event: `TextRecognizedEvent`
- Required payload fields:
  - `correlation_id` (string UUID)
  - `text` (string)
  - `source_language` (string; ISO 639-1 or BCP-47)
  - `target_language` (string)
  - `timestamp` (timestamp-millis)
  - Optional: `confidence`, `segment_index` (for future streaming)

#### 2) Translation → (Client or TTS)
- Logical event: `TextTranslatedEvent`
- Required payload fields:
  - `correlation_id`
  - `translated_text`
  - `source_language`
  - `target_language`
  - `timestamp`
  - Optional: `quality_score`

#### 3) Optional: Translation → TTS
- Logical event: `TTSRequestEvent`
- Required payload fields:
  - `correlation_id`
  - `text` (translated)
  - `text_language` / `target_language`
  - `audio_format`, `sample_rate` (defaults allowed)

### Canonical Avro envelope (MVP)

To make services interoperate cleanly, the MVP should adopt a **single shared envelope** shape across events.

Minimum recommended envelope:

- `event_id: string`
- `event_type: string`
- `event_version: string`
- `timestamp: long` with `logicalType: timestamp-millis`
- `correlation_id: string`
- `trace_id: ["null","string"]` (optional)
- `source_service: string`
- `payload: <event-specific record>`

Notes:
- Use **one timestamp representation** across all services (recommend `timestamp-millis`).
- Keep `event_version` stable; only bump for schema evolution.

## 5) MVP Success Criteria (Thesis-aligned)

The MVP is complete when:

- An end-to-end run works repeatedly:
  - audio input → ASR text → Translation text → output
- All messages carry the same `correlation_id` across the pipeline
- Avro schemas are registered and validated via Schema Registry
- We can measure and report:
  - **End-to-end latency** (p50, p95)
  - **Throughput** (messages/sec) under increasing load
  - **Failure behavior** (retry, DLQ/error event) for at least one injected fault

## 6) Minimal Test & Measurement Plan

### Functional checks
- “Happy path” integration test publishes one audio event and observes the final translated event.
- “Schema compliance” test: producer fails fast if payload violates schema.

### Performance measurements
- Record timestamps at each stage:
  - `t_in` (ingress), `t_asr_done`, `t_trans_done` (and `t_tts_done` if enabled)
- Compute:
  - $\Delta t_{e2e} = t_{out} - t_{in}$
  - stage latencies per service

### Robustness checks
- Inject one failure:
  - temporarily stop Translation or force a model error
- Observe:
  - retry behavior OR an error event / DLQ routing

## 7) MVP Delivery Checklist

- [ ] One canonical topic list chosen and documented
- [ ] Shared Avro envelope chosen and documented
- [ ] Schemas registered in Schema Registry
- [ ] ASR publishes `TextRecognizedEvent`
- [ ] Translation consumes `TextRecognizedEvent` and publishes `TextTranslatedEvent`
- [ ] Demo script(s) exist to run the pipeline and print results by `correlation_id`
- [ ] Metrics collected for latency and throughput

## 8) Next After MVP (Phase 2)

Only after MVP completion, consider:

- Add TTS as a downstream consumer of `TextTranslatedEvent`
- Add streaming support (partial hypotheses / segments)
- Expand quality metrics and cultural adaptation flows
- Harden ops (K8s, autoscaling policies, security)
