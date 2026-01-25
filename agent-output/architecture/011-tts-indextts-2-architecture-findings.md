# Architecture Findings 011: Epic 1.7 TTS Service (IndexTTS-2)

**Date**: 2026-01-25  
**Scope**: Pre-planning architectural assessment for Epic 1.7 (TTS) before Plan drafting.

## Changelog

| Date | Change | Rationale |
|------|--------|-----------|
| 2026-01-25 | Initial findings for Epic 1.7 (IndexTTS-2) | Close remaining architecture gaps (payload sizing, event contract, speaker context propagation) before planning/implementation |

## Context
Roadmap Epic 1.7 adds a TTS microservice to complete the speech-to-speech loop:
- Input: `TextTranslatedEvent` from topic `speech.translation.text`
- Output: `AudioSynthesisEvent` to topic `speech.tts.audio`

Existing architecture context:
- Speaker context propagation (voice cloning) was previously assessed in [agent-output/architecture/006-tts-voice-cloning-architecture-findings.md](agent-output/architecture/006-tts-voice-cloning-architecture-findings.md).
- Kafka payload policy is currently constrained (2 MiB broker; 1.5 MiB inline payload cap) per [agent-output/architecture/003-audio-payload-policy-architecture-findings.md](agent-output/architecture/003-audio-payload-policy-architecture-findings.md) and [agent-output/architecture/system-architecture.md](agent-output/architecture/system-architecture.md).

## Architectural Implications (What MUST be decided up front)

### 1) Output audio payload size (critical)
Synthesized audio is frequently larger than input text and can easily exceed the MVP Kafka caps depending on:
- sample rate / bit depth / channels
- duration of synthesized output

**This is an architectural decision** (not an implementation detail) because it determines whether the system:
- keeps audio inline in events, or
- introduces an object store dependency and emits URIs.

### 2) Event contract design for `AudioSynthesisEvent`
Epic 1.7 requires a new contract. Architectural decisions must pin:
- required fields (correlation/traceability)
- audio format invariants (match MVP WAV-only policy unless explicitly changed)
- how voice cloning inputs are provided (reference clip vs embedding vs URI)

### 3) Speaker/voice context propagation (cross-cutting)
IndexTTS-2 “voice cloning” implies speaker reference context originates at ingress (gateway) but is consumed at TTS.
We must pin a strategy compatible with:
- payload limits
- privacy/retention
- backward compatibility

### 4) Privacy & governance for speaker context
Speaker reference audio and embeddings are practically identifying.
Minimum requirements:
- optional, session-scoped
- time-bounded retention if stored
- never treat `correlation_id` as a user identifier

## Verdict
**APPROVED_WITH_CHANGES** — Epic 1.7 can proceed to planning once the required constraints below are accepted and reflected in the future plan.

## Required Architecture Constraints (must appear in Plan 010+)

### A) Topic taxonomy (pinned)
- Input: `speech.translation.text` → `TextTranslatedEvent`
- Output: `speech.tts.audio` → `AudioSynthesisEvent`

### B) Correlation & ordering
- `AudioSynthesisEvent` MUST preserve `correlation_id`.
- Producer MUST key output messages by `correlation_id`.

### C) Audio format invariants
- For MVP+, `AudioSynthesisEvent.audio_format` MUST be `"wav"` unless an explicit architecture decision changes the global WAV-only invariant.
- If non-wav is requested/received, service MUST log and fall back (or drop) without crashing.

### D) Payload transport strategy (must pick one)
Pick one of the following and document it explicitly in the plan:

**Option D1 (Inline-only, MVP simple)**
- `AudioSynthesisEvent` carries `audio_bytes` inline.
- Hard cap enforced so it stays within Kafka invariants.
- Plan MUST define a maximum synthesized duration and output encoding parameters to guarantee the cap.

**Option D2 (Dual-mode inline-or-URI, recommended)**
- `AudioSynthesisEvent` supports either `audio_bytes` (inline) OR `audio_uri` (external), exactly one set.
- Inline when within cap; URI when output would exceed cap.
- Requires an object store (MinIO/S3) only when needed.

Given existing payload constraints and the likelihood of longer utterances, **D2 is recommended**.

### E) Speaker context propagation
- Speaker context MUST be optional and MUST degrade gracefully to a default voice.
- Plan MUST explicitly choose among:
  - reference audio (inline/URI),
  - embedding (inline),
  - none (non-cloning baseline).

### F) Failure semantics
- Follow MVP failure policy unless otherwise decided: log + drop, or log + fallback voice.
- If object store is used: define behavior for missing/expired URIs (fallback voice; do not crash-loop).

### G) Measurement & thesis-grade evidence (required for this epic)
Epic 1.7 must define measurable performance and quality checks. At minimum:
- latency budget for synthesis (e.g., P50/P90), and/or Real-Time Factor (RTF)
- payload-size distribution (how often URI path is used)
- qualitative audio acceptability criteria (even if subjective)

## Plan/Implementation Integration Requirements
Future plan name mapping (assumed): `agent-output/planning/010-text-to-speech-plan.md` (or equivalent).
The plan MUST:
- reference this findings doc and the prior voice-cloning findings doc
- include an explicit “Success Metric Measurement Method” section (per process improvements)
- call out whether an object store dependency is introduced (and how it is isolated)

## Decision Gate Questions (answer before planning)
1. What synthesis output duration do we consider “in scope” for MVP+ demos (seconds)?
2. Do we accept an object store dependency for large outputs (recommended), or do we cap output duration aggressively?
3. Does IndexTTS-2 accept speaker embeddings directly, or only reference audio?
