# Architecture Findings 010: QA Integration Points & Failure Modes — VAD Stage (Plan 009)

**Date**: 2026-01-19
**Plan**: agent-output/planning/009-voice-activity-detection-plan.md
**Architecture Master**: agent-output/architecture/system-architecture.md
**Related Findings**: agent-output/architecture/009-voice-activity-detection-architecture-findings.md

**Verdict**: APPROVED (QA Guidance)

## Changelog

| Date | Trigger | Summary |
|------|---------|---------|
| 2026-01-19 | QA hardening request | Enumerated critical boundaries, integration points, and failure modes to test for the VAD stage and downstream consumers |

## Purpose
This document is a QA-focused architectural checklist for the integration surface introduced by adding VAD between ingress and ASR.

It calls out:
- Critical **service boundaries** and **data flows** to validate
- Likely **failure modes** (contract, infrastructure, runtime)
- Concrete **QA test obligations** mapped to those failure modes

## Critical Boundaries (What MUST be tested at integration level)

### 1) Shared Contract Artifact ↔ Services
**Boundary**: services rely on a common event contract (Avro schemas + envelope helpers).

**Why critical**: schema mismatch or evolution mistakes fail at runtime and can silently drop events.

QA MUST validate:
- All relevant subjects are registered in Schema Registry for local compose.
- Services can deserialize events produced by their upstream services.
- Compatibility expectations are upheld (no breaking change for consumers).

### 2) Schema Registry ↔ Producers/Consumers
**Boundary**: runtime schema fetch/lookup and subject naming strategy.

QA MUST validate:
- Subject naming aligns with `TopicNameStrategy` (topic-value subjects).
- Behavior when SR is unavailable: services fail fast with clear logs (or enter a controlled retry loop), but MUST NOT corrupt outputs.

### 3) Kafka Topics & Partitioning
**Boundary**: Kafka enforces at-least-once delivery and ordering only within a partition.

QA MUST validate:
- VAD publishes `SpeechSegmentEvent` with message key = `correlation_id`.
- Ordering is preserved per request (segment indexes monotonic at ASR input).
- Duplicate delivery is tolerated (at-least-once): system remains stable and traceable.

### 4) VAD ↔ ASR Contract Boundary
**Boundary**: VAD produces self-contained segments; ASR consumes either raw ingress (legacy) or segments (VAD mode).

QA MUST validate:
- `SpeechSegmentEvent` is self-contained (no hidden dependence on original audio payload).
- ASR dual-mode selection works and is regression-tested (Pipeline A and Pipeline B).

## Data Flows (Golden Paths)

### Pipeline A (Legacy / Baseline)
`speech.audio.ingress (AudioInputEvent)` → ASR → Translation

Why it matters:
- Preserves v0.2.x reproducibility and provides a baseline for performance/quality comparisons.

### Pipeline B (VAD / New)
`speech.audio.ingress (AudioInputEvent)` → VAD → `speech.audio.speech_segment (SpeechSegmentEvent)` → ASR → Translation

Why it matters:
- Validates the new stage and its contract semantics.

## Failure Modes & QA Tests (By Layer)

### A) Contract / Schema Failure Modes
1. **Schema subject missing or wrong subject name**
   - Symptom: consumers fail to deserialize; producers cannot register.
   - QA test: start stack from cold; assert SR contains `speech.audio.ingress-value`, `speech.audio.speech_segment-value`, `speech.asr.text-value`, `speech.translation.text-value`.

2. **Schema incompatibility / field rename drift**
   - Symptom: runtime deserialization errors, or silent defaulting.
   - QA test: produce a known-good sample event and ensure each consumer deserializes and emits downstream events.

3. **Envelope/correlation propagation broken**
   - Symptom: downstream events can’t be joined/attributed.
   - QA test: assert `correlation_id` is identical across segment(s), ASR output, and translation output.

### B) Kafka Delivery / Ordering Failure Modes
1. **Segment reordering** (wrong message key, multiple partitions, concurrent producers)
   - Symptom: ASR sees segment indexes out of order; transcript becomes non-deterministic.
   - QA test: multi-segment input; assert monotonic `segment_index` at ASR input for same `correlation_id`.
   - Stress variant: run test repeatedly and/or with multiple concurrent correlation IDs.

2. **Duplicate delivery** (at-least-once)
   - Symptom: duplicate downstream outputs; potential “double translation” in client.
   - QA test: simulate consumer restart mid-stream (or re-produce same request) and confirm system remains stable; outputs remain traceable via `correlation_id` and `segment_index`.

3. **Backpressure / consumer lag**
   - Symptom: increasing end-to-end latency; memory growth if buffering is unbounded.
   - QA test: burst multiple requests; verify services stay healthy and do not crash-loop.

### C) VAD Runtime Failure Modes
1. **Model availability / startup dependency**
   - Symptom: container runs but never emits segments; repeated download failures.
   - QA test: cold-start stack with no cache; verify VAD reaches ready state and processes one request.

2. **Non-wav inputs** (format invariant violation)
   - Symptom: decode errors.
   - QA test: publish `audio_format != wav`; ensure VAD logs + drops (no crash, no segment emission).

3. **Oversize payload / truncation risk**
   - Symptom: broker rejects message; consumer exceptions.
   - QA test: boundary test near payload cap to ensure drop behavior is consistent with architecture policy.

4. **Edge segmentation cases**
   - All-silence input → expect zero segments.
   - Very short speech blips → expect either zero segments or minimum-duration behavior (but consistent, configurable).
   - Speech at start/end → verify padding rules don’t create empty slices.

5. **Poison message handling** (corrupt bytes)
   - Symptom: repeated crashes on the same offset; service never makes progress.
   - QA test: publish an invalid WAV payload; verify “log + drop” and consumer continues.

### D) ASR Dual-Mode Failure Modes
1. **Wrong topic binding / misconfiguration**
   - Symptom: ASR appears healthy but produces no outputs.
   - QA test: explicitly run Pipeline A and Pipeline B with `ASR_INPUT_TOPIC` set accordingly; validate outputs.

2. **Segment metadata ignored**
   - Symptom: hard to debug ordering/coverage; missing traceability.
   - QA test: confirm ASR logs include `segment_index` when present and preserves `correlation_id`.

### E) Translation Service Failure Modes (Downstream)
1. **Upstream text event missing fields or empty text**
   - Symptom: translation emits empty outputs or errors.
   - QA test: ensure translation handles empty/whitespace text deterministically (log + drop or emit empty translation, but consistent).

## Acceptance-Criteria-Oriented QA Obligations (Plan 009)

1. **Pipeline A regression MUST pass**
   - Ensures legacy reproducibility isn’t broken by default-to-VAD wiring.

2. **Pipeline B smoke MUST pass**
   - Confirms VAD integration and new topic contract.

3. **Success Metric: ≥ 30% reduction in ASR processed duration**
   - Architectural note: measure should compare total original duration vs total segment duration per request across a sparse-speech dataset.
   - QA must record: dataset description, how duration is computed (from WAV header or sample count), and the aggregate reduction.

## Observability Requirements (QA Leverage)
QA should treat these as “must-have” signals for diagnosing failures quickly:
- Every service logs `correlation_id` for each consumed and produced event.
- VAD logs segment count and each segment’s `segment_index` and offsets (`start_ms`, `end_ms`).
- ASR logs which input topic it is consuming at startup.

## Non-Goals (Explicit)
- Exactly-once processing guarantees.
- DLQ/error-event schemas for MVP.
- Global ordering across correlation IDs.
