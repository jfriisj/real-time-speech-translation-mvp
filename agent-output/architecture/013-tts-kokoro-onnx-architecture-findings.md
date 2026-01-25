# Architecture Findings 013: Epic 1.7 TTS Service (Kokoro ONNX)

**Date**: 2026-01-25  
**Scope**: Pre-implementation architectural review of Plan 010 (TTS) after the roadmap pivot to ONNX-backed Kokoro.

## Changelog

| Date | Change | Rationale |
|------|--------|-----------|
| 2026-01-25 | Initial findings for Kokoro ONNX pivot | Validate architectural fit, enforce service boundary, and pin the model-switch strategy for future IndexTTS/Qwen iterations. |

## Handoff Context
- Roadmap Epic 1.7 now targets a **stable** CPU/GPU runtime by using `onnx-community/Kokoro-82M-v1.0-ONNX`.
- Plan 010 implements **dual-mode transport** (inline bytes vs MinIO URI), **speaker context propagation**, and a **pluggable synthesizer** so we can later swap to `IndexTeam/IndexTTS-2` or `Qwen3-TTS` without changing the event contracts.

## Architectural Fit Review

### Fits the current architecture (✅)
- **Event-driven boundary**: Consumes `TextTranslatedEvent` on `speech.translation.text` and produces `AudioSynthesisEvent` on `speech.tts.audio` (matches system topic taxonomy).
- **Payload policy compliance**: Uses the architecture’s required D2 strategy (inline-or-URI) so synthesized audio cannot violate Kafka message caps.
- **Schema governance**: Uses optional fields and backward-compatibility language consistent with Schema Registry constraints.
- **Model stability objective**: ONNX Runtime aligns with the platform’s earlier ONNX usage (VAD) and supports CPU/GPU stability goals.

### Architectural tensions / risks (⚠️)
- **Service responsibility creep**: The TTS service necessarily consumes/produces Kafka events and may upload to MinIO for URI mode. That’s acceptable, but it MUST remain strictly limited to “synthesis + transport of synthesized audio” and avoid taking on cross-service concerns (e.g., playback client responsibilities, dataset management, or additional APIs).
- **Speaker context semantics**: Plan 010 states `speaker_reference_bytes` is propagated but **ignored** by Kokoro (style vectors are keyed by `speaker_id`). This is acceptable for the ONNX baseline, but the “source audio sample for cloning context” must remain preserved end-to-end so future models can consume it.
- **Schema change scope**: Plan 010 adds `model_name` to `AudioSynthesisEvent`. Unless it is optional (union with null + default), it risks breaking compatibility guarantees.

## Required Changes (MUST before implementation)
1. **Enforce “TTS-only” service boundary**
   - The implementation MUST structure the service into clear internal layers:
     - Orchestration (Kafka consume/produce + metrics/logging)
     - Synthesizer backend (Kokoro ONNX)
     - Optional storage adapter (MinIO) for URI mode
   - No additional endpoints or responsibilities beyond producing `AudioSynthesisEvent`.

2. **Make `model_name` schema-safe**
   - If `model_name` is introduced into Avro, it MUST be optional (`["null","string"]`) with a sensible default (or omitted entirely) to maintain backward compatibility.

3. **Pin the “pluggable synthesizer” contract**
   - The synthesizer interface MUST be stable across models:
     - Inputs: `text`, optional `speaker_reference_bytes`, optional `speaker_id`
     - Output: PCM/wav bytes + sample rate + duration metadata
   - Backend selection MUST be configuration-driven (factory) and NOT leak model-specific imports into the orchestration layer.

4. **Provider selection is explicit**
   - The plan MUST clarify whether the delivered container targets:
     - CPU-only (`onnxruntime`) or
     - GPU-enabled (`onnxruntime-gpu`)
   - Avoid “try both at runtime” ambiguity; treat CPU/GPU images as explicit deployment profiles.

## Recommended Improvements (SHOULD)
- **Speaker ID mapping contract**: Define a canonical mapping strategy (`speaker_id` → Kokoro voice/style) in configuration and document fallback behavior.
- **Operational constraints**: Add a hard maximum on input text length (or expected max output duration) to keep RTF/latency predictable and avoid runaway payload sizes.
- **ONNX asset caching**: Ensure model/voice assets are cached in a deterministic location to keep cold-start behavior measurable.

## Alternatives Considered
- **Keep IndexTTS-2 now**: Rejected for the current epic due to runtime stability/weight risks on constrained hardware.
- **Always-URI output**: Simplifies payload caps but forces MinIO dependency even for small outputs; not recommended for MVP+.
- **Dedicated speaker profile service**: Rejected for MVP+ due to expanded privacy/identity scope.

## Integration Requirements
- **System Architecture** must reflect:
  - TTS engine is Kokoro ONNX
  - Object-store is used only for `audio_uri` outputs (speaker context remains inline for now)
  - ONNX Runtime becomes a first-class inference dependency
- **Plan 010** should remain consistent with:
  - Kafka payload policy (broker 2 MiB, inline cap 1.5 MiB)
  - Schema Registry compatibility mode (`BACKWARD` or stricter)

## Verdict
**APPROVED_WITH_CHANGES**

Implementation may proceed only after the MUST items above are reflected in the plan and architecture master (or explicitly waived).