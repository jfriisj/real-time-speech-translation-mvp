# Architecture Findings 011: Epic 1.7 TTS (Kokoro ONNX) — Payload Strategy, Voice Context, and Service Boundaries

**Related Plan (if any)**: agent-output/planning/010-text-to-speech-plan.md (referenced by other artifacts; file not present in repo)
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | Roadmap | Pre-planning architectural assessment | Confirms TTS boundary, contract implications, and non-negotiable guardrails (payload + privacy + pluggability). |

## Context

Epic 1.7 adds a **Text-to-Speech (TTS)** stage to complete the “speech-to-speech” loop:
- Input: `TextTranslatedEvent`
- Output: `AudioSynthesisEvent`

The architecture has already pinned several constraints in the master doc:
- Kafka payload invariants (2 MiB broker, 1.5 MiB inline cap)
- Speaker context propagation must be optional and must not force identity semantics
- TTS backend pivoted to **Kokoro-82M ONNX** for CPU/GPU runtime stability
- Synthesizer backend must be **pluggable** (factory-selected)

This findings note focuses on architectural implications and decision gates (not implementation steps).

## Findings

### Must Change

- **Contract MUST support “claim check” for synthesized audio**
  - `AudioSynthesisEvent` must support either inline `audio_bytes` OR `audio_uri` (exactly-one semantics).
  - Rationale: avoids violating Kafka payload invariants for non-trivial durations.

- **Speaker context MUST remain optional pass-through metadata**
  - The baseline Kokoro ONNX backend may ignore voice cloning inputs, but contracts must not block future backends.
  - Intermediate services (ASR/Translation) must treat speaker context as pass-through only (no coupling).

- **Object-store usage MUST have explicit lifecycle/TTL and failure semantics**
  - If `audio_uri` is used, the platform must define:
    - TTL / retention window (e.g., 24h for thesis auditability)
    - Behavior when URI expired/missing (log + degrade, must not crash pipeline)

- **Pluggable synthesizer is a hard boundary, not a convenience**
  - Code must not couple event contracts to a specific model’s input representation.
  - Backend selection is configuration/deployment, not a compile-time dependency chain across services.

### Risks

- **PII and data governance risk**
  - Synthesized audio and speaker reference audio are sensitive; storing them (or exposing presigned URLs) introduces privacy and access-control obligations.
  - Correlation IDs must not become user identity; no “profile” semantics without an explicit new epic/decision.

- **Latency and determinism risk from storage dependency**
  - Using `audio_uri` adds another network hop + failure mode.
  - This is acceptable for MVP+ if it is optional and degradation is defined.

- **Contract drift risk**
  - Multiple documents reference a Plan 010 file that is not present. This undermines traceability and governance for schema changes.

### Alternatives Considered

- **Inline-only synthesized audio**
  - Rejected as the default because it is fragile against payload limits. Acceptable only for tiny demo outputs.

- **Always-URI synthesized audio**
  - Acceptable as a deployment mode, but rejected as a mandatory default because it introduces a hard dependency on object storage even when payloads are small.

- **Speaker embedding propagation**
  - Preferred long-term if a stable, documented embedding interface exists across TTS backends. Not required for Kokoro baseline.

## Integration Requirements

- TTS must subscribe to `speech.translation.text` (`TextTranslatedEvent`) and publish to `speech.tts.audio` (`AudioSynthesisEvent`).
- Event schemas must remain backward compatible via optional fields (Schema Registry `BACKWARD` or stricter).
- If URIs are emitted:
  - URIs must be time-bounded (presigned) or access-controlled
  - Cleanup/TTL rules must be auditable

## Consequences

- The platform gains a scalable audio output path without Kafka overload.
- The platform assumes a new operational surface: object storage reliability, lifecycle management, and access policy.

## Handoff

## Handoff to Planner/QA

**From**: Architect
**Artifact**: agent-output/architecture/011-tts-kokoro-onnx-architecture-findings.md
**Status**: APPROVED_WITH_CHANGES
**Key Context**:
- `AudioSynthesisEvent` must support inline-or-URI to protect Kafka invariants.
- Speaker context must remain optional pass-through metadata.
- Storage lifecycle/TTL + missing-URI behavior must be explicitly defined.

**Recommended Action**: Restore/locate the Plan 010 document (or update references), then validate TTS schema/topic decisions against Schema Registry compatibility and payload limits.