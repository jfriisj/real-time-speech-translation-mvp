# Architecture Findings 019: Plan 010 (Epic 1.7 TTS) — Pre-Implementation Review (Rev 29)

**Related Plan (if any)**: agent-output/planning/010-text-to-speech-plan.md (Rev 29)
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | User | Architectural fit review | Reviewed Plan 010 Rev 29 against the architecture master; confirmed core fit (Claim Check, XOR payload, retention, privacy) and identified required plan text fixes to prevent integration drift (topic/subject naming, schema artifact naming, acceptance criteria corruption). |

## Context

- What is being assessed: Plan 010 Rev 29 for the TTS service consuming `TextTranslatedEvent` and producing `AudioSynthesisEvent` with a Claim Check pattern (inline bytes or URI).
- Affected modules/boundaries:
  - Event contracts: `shared/schemas/avro/AudioSynthesisEvent.avsc` governed by Schema Registry.
  - Runtime boundary: `services/tts` as an independent microservice.
  - Downstream boundary: `gateway` and web client consumption of synthesized audio.
  - Optional dependency boundary: object storage (MinIO/S3) with time-bounded retention.

## Findings

### What Fits
- **Claim Check / payload strategy**: Plan’s XOR invariant (`audio_bytes` XOR `audio_uri`) matches the master guardrail for blob-carrying events and avoids Kafka payload cap violations.
- **Storage optionality**: The service remains operable when object storage is disabled (inline-only), aligning with the architecture requirement to degrade gracefully.
- **Retention + privacy**: Default 24h target retention and “do not log presigned URLs” match the architecture’s artifact retention and URI security decisions.
- **Speaker context propagation**: Plan explicitly preserves speaker context as optional pass-through metadata, consistent with master “speaker context MUST be propagated end-to-end”.
- **Observability direction**: Required fields (`correlation_id`, `synthesis_latency_ms`, `rtf`, transport mode) match architecture priorities (correlation first, metrics later).

### Must Change
1) **Topic + Schema Registry subject naming must be explicit**
- **Architecture master decision**: Topic taxonomy includes `speech.translation.text` (input) and `speech.tts.audio` (output). Subject naming is `TopicNameStrategy` → `speech.tts.audio-value`.
- **Plan Rev 29 issue**: It names the input topic but does not explicitly pin the output topic and subject naming.
- **Required plan delta**: Add a short “Kafka bindings” line that pins:
  - Input topic: `speech.translation.text`
  - Output topic: `speech.tts.audio`
  - SR subject (value): `speech.tts.audio-value`

2) **Schema artifact naming in M1 conflicts with repo source-of-truth**
- **Plan Rev 29 issue**: M1 references `speech.tts.audio-value.avsc`, but the repo’s canonical schema is `shared/schemas/avro/AudioSynthesisEvent.avsc`.
- **Risk**: Developers may create a second schema file or register a conflicting record/subject pairing.
- **Required plan delta**: Update M1 deliverable to reference the actual repo schema path and clarify that “`speech.tts.audio-value`” is the Schema Registry subject name (not the file name).

3) **Acceptance criteria text corruption must be fixed before implementation**
- **Plan Rev 29 issue**: The Functional Verification section is partially corrupted (broken `DISABLE_STORAGE` line).
- **Risk**: Implementation and QA will interpret verification differently, leading to “done” disagreements.
- **Required plan delta**: Repair the section and ensure the three functional cases are cleanly stated:
  - Small output: inline bytes
  - Large output with storage: URI/key
  - Large output with `DISABLE_STORAGE=true`: log-and-drop

### Risks
- **Tokenizer + platform dependency drift**: Plan correctly mandates `phonemizer`/`espeak-ng`, but without a pinned version and container verification steps, deployments can differ between dev and CI.
- **Evidence path governance**: Plan points to `report-output/qa-evidence/`; ensure this is a stable convention so reviewers can find artifacts.

### Alternatives Considered
- **Always-URI TTS output** (rejected): violates “operable without object storage” and increases failure modes for small outputs.
- **Inline-only output with strict duration cap** (rejected): fragile; likely violates Kafka invariants for realistic phrases.

## Integration Requirements

- Update Plan 010 Rev 29 to explicitly pin Kafka topic names + SR subject naming (TopicNameStrategy).
- Update M1 deliverables to reference `shared/schemas/avro/AudioSynthesisEvent.avsc` as the schema artifact.
- Repair the corrupted acceptance criteria section to prevent inconsistent QA/UAT interpretation.

## Consequences

- With the above fixes, Plan 010 Rev 29 is architecturally fit and can proceed to implementation without introducing contract or boundary drift.
- If left unfixed, topic/schema naming ambiguity risks split-brain integration (different teams register/consume different subjects), increasing rework and release risk.

## Handoff

## Handoff to Planner / Implementer

**From**: Architect
**Artifact**: agent-output/architecture/019-text-to-speech-plan-architecture-findings.md
**Status**: APPROVED_WITH_CHANGES
**Key Context**:
- The design aligns with master architecture (Claim Check XOR, optional storage, 24h retention, speaker context pass-through), but the plan must pin topic/subject names, correct schema artifact naming, and fix corrupted acceptance criteria text.

**Recommended Action**: Apply the required plan text deltas, then proceed to implementation and QA evidence capture.
