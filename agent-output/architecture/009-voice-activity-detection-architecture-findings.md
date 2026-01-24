# Architecture Findings 009: Epic 1.6 Voice Activity Detection (VAD) Service — Pre-Planning Review

**Date**: 2026-01-19
**Epic**: 1.6 Voice Activity Detection (VAD) Service
**Roadmap Reference**: agent-output/roadmap/product-roadmap.md
**Assumed Future Plan Name (per request)**: agent-output/planning/009-voice-activity-detection-plan.md
**Architecture Master**: agent-output/architecture/system-architecture.md

**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Trigger | Summary |
|------|---------|---------|
| 2026-01-19 | Pre-planning gate (Epic 1.6) | Pinned VAD stage boundary, segmentation semantics, and migration constraints to protect v0.2.x reproducibility and prevent schema/topic drift |

## Scope of Review
This review assesses architectural implications and non-negotiable constraints for introducing a VAD stage between Gateway and ASR:
- New event contract (`SpeechSegmentEvent`) and topic usage
- Migration strategy for ASR (legacy `AudioInputEvent` vs segmented input)
- Ordering, correlation, and partitioning requirements
- Performance/latency implications and operational constraints
- Boundary discipline (what belongs in VAD vs Gateway/ASR/shared contract)

## Architectural Fit
A dedicated VAD microservice aligns with the platform’s core qualities:
- **Decoupling**: Keeps silence-filtering policy isolated from ASR implementation details.
- **Scalability**: Allows independent scaling/tuning of the segmentation stage.
- **Measurability**: Adds a well-defined stage for latency attribution and compute savings measurement.

## Must Change (Required)

1. **Define `SpeechSegmentEvent` semantics explicitly (not just a name)**
   The platform already reserves `SpeechSegmentEvent`, but the plan MUST make its semantics unambiguous.

   Required semantics (architecture-level):
   - **Self-contained segment**: each produced segment MUST be independently consumable by ASR without requiring the original full audio.
   - **Segment identity**: MUST include a stable segment identifier and sequence index.
   - **Time mapping**: MUST include start/end offsets relative to the original audio stream (e.g., `start_ms`, `end_ms`).
   - **Correlation**: MUST preserve the original `correlation_id` (segment events share the same `correlation_id`).

2. **Pin ordering/partitioning rule to avoid segment reordering**
   Kafka ordering is per-partition, not global. If segments for a single request can reorder, ASR output becomes non-deterministic.

   Requirement:
   - Produce `SpeechSegmentEvent` with Kafka message key set to `correlation_id` (or another stable per-request key), ensuring all segments for one request land on the same partition and retain order.

3. **Preserve v0.2.x baseline and testing repeatability**
   Epic 1.6 must not “erase” the legacy path.

   Requirement:
   - v0.2.x reproducibility MUST remain possible by continuing to support the pre-VAD flow (`AudioInputEvent` → ASR) for benchmarks/regression.
   - Migration MUST be explicit: ASR either supports both inputs (preferred for transition) or a feature flag toggles which topic it consumes.

4. **Avoid contract inflation: VAD cannot introduce new cross-cutting fields without governance**
   VAD’s job is segmentation, not enriching unrelated metadata.

   Requirement:
   - Any new fields added to the shared envelope (e.g., speaker context for future TTS voice cloning) MUST be proposed as a separate architecture decision or bundled with the Epic 1.7 plan; Epic 1.6 must keep schema changes minimal.

## Should Change (Strong Recommendations)

1. **Keep audio format invariant: WAV only (for now)**
   The architecture master already pins MVP `audio_format == "wav"`.

   Recommendation:
   - VAD should treat non-wav as invalid and drop with logs (consistent with MVP failure signaling).

2. **Establish “silence policy” configuration boundaries**
   VAD involves thresholds and post-processing heuristics. These are policy knobs.

   Recommendation:
   - Thresholds MUST be runtime configuration (env/config) rather than encoded into schemas or shared contract libraries.

3. **Emit coarse segmentation metadata for observability**
   Recommendation:
   - Include fields that let QA/benchmarks validate behavior without reading raw audio (e.g., speech probability summary, total speech duration per request, number of segments).

## Key Risks
- **Reordering risk**: Segment events can reorder without an explicit partitioning rule.
- **Schema churn risk**: Overloading Epic 1.6 with speaker-context or streaming semantics creates premature coupling.
- **Latency regression risk**: VAD can add compute cost; if configured incorrectly, it may increase end-to-end latency.

## Alternatives Considered
- **Inline VAD inside ASR**: Rejected (couples policy + compute, limits independent scaling, complicates rollback).
- **VAD in the Gateway**: Rejected (expands ingress complexity and resource footprint; complicates security boundary).
- **No segmentation event; mutate `AudioInputEvent`**: Rejected (breaks v0.2.x reproducibility and increases ambiguity for consumers).

## Integration Requirements (Non-Negotiable)
- VAD consumes `AudioInputEvent` from topic `speech.audio.ingress`.
- VAD publishes `SpeechSegmentEvent` to topic `speech.audio.speech_segment`.
- Preserve `correlation_id` end-to-end.
- Ensure per-request ordering by partition keying segments consistently (recommended: key = `correlation_id`).
- Failure behavior remains MVP-simple: log + drop; no new error-event schemas.

## Notes for Future Planning
- If Epic 1.7 (TTS) requires speaker reference context, VAD is a natural place to extract a short, speech-only reference clip. This MUST remain optional and MUST be handled under explicit schema governance.

