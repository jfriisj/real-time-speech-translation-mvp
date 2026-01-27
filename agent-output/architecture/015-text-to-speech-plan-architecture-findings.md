# Architecture Findings 015: Plan 010 (Epic 1.7 TTS) — Pre-Implementation Review

**Related Plan (if any)**: agent-output/planning/010-text-to-speech-plan.md (Rev 21)
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | Planner | Architecture review | Confirms Plan 010 matches the master architecture for Kokoro ONNX + pluggable backend + claim-check output, with required changes for dependency boundaries and payload invariants. |

## Context

Plan 010 proposes implementing the TTS service for v0.5.0:
- Consumes `TextTranslatedEvent` from `speech.translation.text`
- Produces `AudioSynthesisEvent` to `speech.tts.audio`
- Uses Kokoro-82M ONNX via ONNX Runtime
- Uses a factory pattern for pluggable synthesizer backends
- Uses claim-check (inline bytes vs URI) for synthesized audio payload transport

This review checks fit against the master architecture decisions in agent-output/architecture/system-architecture.md and Findings 011.

## Findings

### What Fits
- **Correct boundary**: TTS is an independent service consuming from Kafka and emitting an event (no direct service coupling).
- **Correct backend strategy**: Kokoro ONNX + pluggable factory matches the pinned architecture decision.
- **Correct payload strategy**: inline-or-URI output aligns with the Epic 1.7 guardrail to avoid Kafka payload violations.

### Must Change

- **Do not hard-depend on Epic 1.8 (object storage) for v0.5.0 baseline correctness**
  - Plan currently assumes `ObjectStorage` is “available and working (per Epic 1.8 findings)”. Epic 1.8 is scheduled for v0.6.0.
  - Required: TTS MUST remain operable with object storage disabled.
    - Acceptable behaviors when storage is disabled:
      - Inline-only mode with an explicit max-duration/size cap and logging + dropping if exceeded, OR
      - URI mode disabled and oversize audio rejected with clear logs.

- **Align payload thresholds with architectural invariants (MiB vs MB) and the 1.5 MiB cap**
  - Architecture invariant: 1.5 MiB inline payload hard cap (broker 2 MiB).
  - Plan uses `1.0 MB` as the switch threshold; that is fine as a conservative threshold, but MUST be expressed as bytes/MiB and justified.
  - Required: Use explicit byte constants and a safety margin below 1.5 MiB (e.g., switch to URI at ≤1.25 MiB) and document why.

- **Schema contract MUST include content metadata and correlation semantics**
  - Architecture requires `correlation_id` propagation.
  - Required: `AudioSynthesisEvent` schema MUST include:
    - `correlation_id` (required)
    - `audio_format` (pinned to `wav` for MVP)
    - `content_type` (e.g., `audio/wav`) or equivalent
  - If `request_id` is included, Plan MUST define whether it is distinct from `correlation_id` and how it is populated.

- **Claim-check semantics MUST be standardized and validated at runtime**
  - Avro cannot enforce “exactly one of `audio_bytes` or `audio_uri`”.
  - Required: Producer MUST validate and enforce exactly-one semantics before publishing.
  - Required: If `audio_uri` is emitted, service MUST avoid logging full presigned URLs.

### Risks
- **Tokenization/phonemization complexity**: the plan acknowledges this; ensure the factory isolates these dependencies.
- **Operational dependency drift**: if the team “just enables MinIO” for v0.5.0, retention/TTL and URL-security requirements may be missed.

### Alternatives Considered
- **Inline-only output**: acceptable only for short demo outputs; fragile against payload caps.
- **Always-URI output**: acceptable as a deployment mode but should not be mandatory for baseline runs.

## Integration Requirements
- Topic bindings MUST remain:
  - consume `speech.translation.text` (`TextTranslatedEvent`)
  - produce `speech.tts.audio` (`AudioSynthesisEvent`)
- Schema Registry compatibility MUST remain `BACKWARD` (or stricter).
- Services MUST tolerate at-least-once semantics (duplicates); correlation_id must be preserved.

## Consequences
- With the required changes, Plan 010 will be stable for v0.5.0 without prematurely forcing v0.6.0 storage infrastructure.
- Clarifying payload thresholds and schema metadata reduces integration and benchmarking failures.

## Handoff

## Handoff to Implementer

**From**: Architect
**Artifact**: agent-output/architecture/015-text-to-speech-plan-architecture-findings.md
**Status**: APPROVED_WITH_CHANGES
**Key Context**:
- v0.5.0 TTS must not require object storage to function.
- Payload thresholds must respect the 1.5 MiB inline cap and use explicit bytes/MiB.
- Enforce exactly-one semantics for `audio_bytes` vs `audio_uri` at runtime and avoid logging full presigned URLs.

**Recommended Action**: Update the plan to incorporate the must-change items before implementation begins.