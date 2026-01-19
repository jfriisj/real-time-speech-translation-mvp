# Architecture Findings — Epic 1.7 TTS (IndexTTS-2) + Voice Cloning Context

**Date**: 2026-01-19  
**Scope**: Pre-planning architectural assessment for v0.3.0 Epic 1.7 (TTS) and its cross-cutting dependency: propagating speaker/voice context from ingress to TTS.

## Changelog

| Date | Change | Rationale |
|------|--------|-----------|
| 2026-01-19 | Initial findings for TTS + voice cloning context propagation | Prevents schema/topic drift and avoids accidental pipeline coupling before planning |

## Handoff Context

Roadmap v0.3.0 introduces three planned epics:
- Epic 1.5: Ingress Gateway (WebSocket & gRPC)
- Epic 1.6: VAD service (silence removal)
- Epic 1.7: TTS service using `IndexTeam/IndexTTS-2` with optional voice cloning

The open question is: **how does TTS access speaker reference context** (reference audio and/or speaker embedding) if TTS is the last service in the pipeline?

## Architectural Implications

### 1) Contract Surface Area (Schemas)
Voice cloning requires speaker context that originates at ingress (raw audio) and must be available at TTS. This creates cross-cutting contract pressure:
- Either **propagate speaker context through the event chain** (ASR + Translation pass-through)
- Or **store speaker context out-of-band** and propagate only a reference (URI/ID)

This is not an “implementation detail”; it affects:
- Avro schema evolution
- Topic taxonomy
- Message size constraints
- Privacy/data handling policy

### 2) Message Size & Latency
If reference audio is carried inline, each pipeline hop repeats the payload overhead.
- Even a small reference clip (e.g., 3 seconds PCM16 @ 16kHz mono ≈ 96 KB) multiplies across topics.
- The system currently enforces strict message size limits for MVP; v0.3.0 must remain compatible with operational constraints.

If a URI/ID is used, Kafka payloads remain small, but an object store dependency is introduced.

### 3) Data Classification & Governance
Speaker reference audio (or a stable speaker embedding) is **personally identifying** in practice.
Minimum architecture requirements:
- Explicit retention policy (time-bounded, e.g., per session)
- Clear boundary: speaker context is *not* a long-lived user profile unless explicitly introduced
- Auditability: correlation_id must not become a user identifier

### 4) Backward Compatibility & Migration
Existing v0.2.x baseline assumes:
- `AudioInputEvent` -> ASR -> `TextRecognizedEvent` -> Translation -> `TextTranslatedEvent`

v0.3.0 introduces VAD and `SpeechSegmentEvent`. This conflicts with prior “ASR topic bindings are non-negotiable” guidance. The architecture MUST define a migration strategy that preserves:
- Existing benchmarks and reproducibility (v0.2.1)
- Compatibility for existing producers (CLI)

## Design Options for Voice Context Propagation

### Option A — Inline “Reference Clip” in Event Envelope (Recommended for MVP+)
**Approach**: Add optional fields to the shared event envelope (or each event) carrying a short reference clip (bytes) + metadata.

- **Pros**: No new infrastructure; deterministic; easiest to reason about; works if IndexTTS-2 requires raw reference audio.
- **Cons**: Increased Kafka bandwidth and per-hop overhead; must enforce hard caps; increased PII exposure surface.

**Requirements**:
- Hard cap on reference clip size + duration
- Reference clip should be speech-only (best extracted in VAD)
- Explicit “pass-through contract” requirement for ASR/Translation

### Option B — URI/ID to External Object Store (Scalable, More Complex)
**Approach**: Persist reference clip once (e.g., MinIO/S3); propagate `speaker_reference_uri` through events.

- **Pros**: Minimal Kafka overhead; reference clip stored once; better scaling characteristics.
- **Cons**: New dependency (object store), ACLs, lifecycle/cleanup, failure modes (404s), and a new latency component.

**Requirements**:
- Object store lifecycle/TTL
- Signed URLs or service-to-service auth
- Failure behavior when reference unavailable (fallback voice)

### Option C — Speaker Embedding Propagation (Best if Model Supports It)
**Approach**: Compute a speaker embedding at ingress (or in VAD) and propagate the vector (small) through events.

- **Pros**: Minimal payload; avoids storing voice audio; reduces PII exposure vs raw audio.
- **Cons**: Only viable if IndexTTS-2 supports embedding input; risk of “vendor lock” to embedding format.

### Option D — Speaker Profile Service (Not Recommended for Thesis MVP+)
**Approach**: Create a dedicated “speaker profile” microservice and session store.

- **Pros**: Clean separation of concerns; can support multi-session identity.
- **Cons**: Adds identity semantics and storage complexity; expands scope; introduces privacy obligations.

## Recommendation (Architectural Guardrails)

**Verdict**: **APPROVED_WITH_CHANGES**

Before planning/implementation, the epic MUST include an explicit decision for how speaker context is propagated:
- Default: **Option A** (inline reference clip) for MVP+ simplicity and thesis demonstrability.
- Upgrade path: **Option B** if message size/bandwidth becomes a bottleneck.
- Consider **Option C** only if IndexTTS-2 provides a stable, documented embedding interface.

### Required Architecture Constraints
- Speaker context MUST be optional (TTS must degrade gracefully to a default voice).
- Reference clip MUST be short and speech-only; extraction SHOULD be done in VAD.
- Schema changes MUST be backward compatible with v0.2.x subjects (new optional fields or new event types/topics).
- Correlation IDs MUST continue to work end-to-end; speaker context MUST NOT become a durable user identifier.

## Integration Requirements (for the future plan)

Plan name mapping (assumed): `agent-output/planning/006-tts-voice-cloning-plan.md`

The plan MUST cover:
- Topic taxonomy additions for `SpeechSegmentEvent` and `AudioSynthesisEvent`
- Shared schema changes and Schema Registry compatibility approach
- Privacy/retention statement for speaker reference data
- Failure-mode behavior for missing/invalid speaker context (fallback voice)

## Decision Gate (must be answered early)
- Does IndexTTS-2 require **reference audio**, or can it accept a **speaker embedding**?
  - If reference audio is required, Option A or B is mandatory.
  - If embedding is supported, Option C becomes preferred.
