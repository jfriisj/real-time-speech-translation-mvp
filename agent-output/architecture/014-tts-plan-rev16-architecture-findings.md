# Architecture Findings 014: Epic 1.7 TTS Service — Plan 010 (Rev 16) Pre-Implementation Review

**Date**: 2026-01-26  
**Scope**: Architectural fit review of Plan 010 Revision 16 *before* implementation proceeds.

## Changelog

| Date | Trigger | Summary |
|------|---------|---------|
| 2026-01-26 | Pre-implementation review request | Reviewed Plan 010 (Rev 16) against the master architecture and prior Findings 013. Issued required changes to remove remaining architectural ambiguities and to pin missing guardrails (CPU/GPU profile clarity, input bounds). |

## Handoff Context
- Roadmap Epic 1.7 requires completing the output loop with synthesis and emphasizes **runtime stability on both CPU and GPU** using Kokoro ONNX.
- The master architecture pins the D2 transport strategy for TTS outputs (inline `audio_bytes` **or** external `audio_uri`) to respect Kafka payload invariants.
- Prior architecture decision record: [agent-output/architecture/013-tts-kokoro-onnx-architecture-findings.md](agent-output/architecture/013-tts-kokoro-onnx-architecture-findings.md).

## Architectural Fit Review

### Fits the current architecture (✅)
- **Event-driven boundary**: Plan consumes `TextTranslatedEvent` and produces `AudioSynthesisEvent`, consistent with the master architecture’s topic taxonomy and service boundaries.
- **Payload policy compliance**: Plan mandates dual-mode transport (inline bytes vs URI), consistent with the D2 guardrail in the master architecture.
- **Schema governance**: Plan explicitly requires optional (union-with-null) new fields and Schema Registry backward compatibility.
- **Privacy/retention intent**: Plan includes log redaction and a 24h retention policy for object-store artifacts.

### Architectural tensions / risks (⚠️)
- **CPU/GPU delivery profile ambiguity**: Plan says GPU must be “config-ready” and selectable “via configuration or deployment profile”, but does not clearly pin the v0.5.0 artifact strategy (single image with optional deps vs two distinct images/profiles). This has downstream operational and reproducibility consequences.
- **Missing explicit input bounds**: The master architecture’s payload constraints (broker cap + inline cap) are pinned, but Plan 010 Rev 16 does not explicitly specify a max input text length (or max output duration). This is a practical architectural guardrail to prevent runaway compute, unbounded synthesis, and brittle payload behavior.
- **Metrics boundary clarity**: Plan defines latency as `TextTranslatedEvent` → `AudioSynthesisEvent`. In URI mode, upload time is part of user-visible service behavior; it should be explicit whether acceptance metrics are “inference-only” or “service end-to-end” to avoid non-comparable benchmarks across profiles.

## Required Changes (MUST before implementation)

1) **Pin CPU/GPU runtime profile strategy for v0.5.0**
- Plan MUST explicitly state one of:
  - **Option A**: “CPU-only image for v0.5.0; GPU is deferred to a later release”, OR
  - **Option B**: “Two deployment profiles/images (CPU and GPU) exist; CPU is the validated default for v0.5.0”, OR
  - **Option C**: “Single image supports both via optional dependency groups, with explicit run profiles and documented constraints.”
- Rationale: The roadmap and Findings 013 require the “reliable on CPU/GPU” thesis requirement to be translated into an operationally clear deployment story.

2) **Add an explicit input-bound guardrail (text length or duration)**
- Plan MUST pin either:
  - Maximum input text length (characters/tokens), OR
  - Maximum output audio duration.
- Rationale: Prevents unbounded compute and makes payload/latency goals enforceable.

3) **Clarify measurement boundaries for performance claims**
- Plan MUST explicitly define whether the primary acceptance metric is:
  - **InferenceLatencyMs** (model runtime only), OR
  - **ServiceLatencyMs** (consume → publish, including URI upload when applicable),
  and (if both are tracked) which is the primary release gate.
- Rationale: Ensures reproducible benchmarking and prevents cross-run disputes.

## Recommended Improvements (SHOULD)

1) **Strengthen layering as an internal architecture invariant**
- Plan SHOULD explicitly reflect the internal layering mandated in Findings 013:
  - orchestration (Kafka + logging)
  - synthesizer backend
  - storage adapter
- Rationale: Keeps service responsibility creep in check.

2) **Retention verification artifact**
- Plan SHOULD specify where the “MinIO 24h retention rule present” evidence will live (architecture/QA artifact location), without prescribing HOW to test.

3) **Speaker mapping contract documentation**
- Plan SHOULD clarify how `speaker_id` is interpreted (e.g., data-driven map with fallback) so that the contract remains stable even if Kokoro’s internal voice assets evolve.

## Alternatives Considered
- **Always-URI output**: simplifies payload safety but forces object-store dependency for all cases.
- **Inline-only output with aggressive duration caps**: simpler but fragile, risks Kafka cap violations.
- **Separate “speaker profile” service**: rejected for MVP+ due to added identity/privacy scope.

## Integration Requirements
- TTS outputs MUST remain compatible with Kafka payload policy and Schema Registry backward compatibility.
- Any new dependencies introduced into `speech-lib` MUST remain generic adapters (no business logic) and must not create cross-service coupling.

## Verdict
**APPROVED_WITH_CHANGES**

Implementation may proceed only after the MUST items above are reflected in Plan 010 (Rev 16+) or explicitly waived with an architecture master decision.
