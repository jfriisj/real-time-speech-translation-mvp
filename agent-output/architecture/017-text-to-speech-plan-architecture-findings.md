# Architecture Findings 017: Plan 010 (Epic 1.7 TTS) — Re-Review (Rev 25)

**Related Plan (if any)**: agent-output/planning/010-text-to-speech-plan.md (Rev 25)
**Related Analysis (if any)**: agent-output/analysis/010-text-to-speech-plan-analysis.md
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | User | Architectural alignment review | Re-review of Plan 010 Rev 25; identifies misalignment with master architecture on speaker context propagation, schema compatibility, and retention defaults; requires plan deltas before implementation. |

## Context

Plan 010 defines the MVP+ TTS service that consumes `TextTranslatedEvent` and produces `AudioSynthesisEvent`, with Claim Check (inline bytes vs URI) to avoid Kafka payload violations.

This re-review is triggered because Plan 010 Rev 25 introduced new “Contract Decisions” (speaker context, retention semantics, URI type/expiry behavior, schema compatibility language) that must match the master architecture decisions in agent-output/architecture/system-architecture.md.

## Findings

### What Fits
- **Claim Check guardrails** are directionally correct: the plan keeps the inline-vs-URI split and requires “exactly one of `audio_bytes` / `audio_uri`”, matching the platform’s blob-transport strategy.
- **Optional storage dependency** is correct for current maturity: the service remains operable when object storage is unavailable.
- **Security hygiene**: “do not log presigned URLs” aligns with the architecture’s URI security guardrails.

### Must Change (Required)

1) **Speaker context propagation is architecturally misaligned**
- **Architecture master requirement**: speaker context MUST remain optional but MUST be propagated end-to-end (even if the baseline model does not use it).
- **Plan Rev 25 currently**: decides speaker context is “None” and explicitly drops `speaker_reference_bytes`.
- **Required plan delta**: update the contract so speaker context is treated as pass-through metadata and is preserved into `AudioSynthesisEvent` (or explicitly state that `AudioSynthesisEvent` includes optional speaker context fields and that the TTS service copies them through unchanged).

2) **Schema compatibility language conflicts with Schema Registry policy**
- **Architecture master decision**: Schema Registry compatibility MUST be `BACKWARD` (or stricter) for MVP subjects.
- **Plan Rev 25 currently**: describes “forward-compatible” consumers.
- **Required plan delta**: align to the architecture language: additive evolution with optional fields/unions, assuming Registry is enforcing backward compatibility for producers.

3) **Retention default conflicts with the architecture guardrail**
- **Architecture master guardrail**: artifact retention MUST be time-bounded with default target **24 hours**, configurable by environment.
- **Plan Rev 25 currently**: sets **7 days** as an expected lifecycle policy.
- **Required plan delta**: change retention expectation to “time-bounded, configurable; default target 24h unless environment overrides”. If 7 days is required for thesis evidence, that must be proposed as an explicit architecture change (with privacy/cost rationale).

4) **`audio_uri` responsibility boundary is under-specified for reliability**
- Plan Rev 25 states `audio_uri` is a presigned URL (15 min) and expiry requires client re-synthesis.
- Architecture requires URI-based flows to **degrade gracefully** on missing/expired URIs.
- **Required plan delta**: specify which component is responsible for URI refresh/recovery:
  - Preferred: `AudioSynthesisEvent.audio_uri` carries an internal object reference/key, and gateway is responsible for presigning at read-time.
  - Acceptable MVP alternative: TTS emits presigned URLs, but gateway must be able to re-issue/re-presign (client-only “re-synthesize” is fragile and increases compute).

### Should Change (Strongly Recommended)

- **Align “Claim Check introduced in v0.6.0” vs “used in v0.5.0” narrative**
  - The master architecture introduces Claim Check as a platform decision (v0.6.0+), but also allows earlier adoption per-service when payload pressure demands it.
  - Recommendation: clarify in the plan that Claim Check support is implemented now for TTS because synthesized output can exceed Kafka invariants, while broader persistence/auditability remains Epic 1.8 (v0.6.0).

- **Avoid hard-coding presign TTL values in the plan**
  - TTL belongs to environment/security posture; recommend describing “time-bounded presigned URLs with configurable TTL”.

## Integration Requirements

Before implementation proceeds, Plan 010 must be revised to:
- Preserve optional speaker context end-to-end (pass-through semantics).
- Align schema evolution to Registry `BACKWARD` compatibility enforcement.
- Align retention defaults to the master guardrail (24h target, configurable).
- Clarify `audio_uri` semantics and which boundary (TTS vs gateway) owns presigning and expiry recovery.

## Consequences
- If unchanged, the plan will cause contract drift and block later voice/persona work (Epic 1.7+ / voice cloning) by discarding speaker context.
- Retention mismatch increases privacy risk and undermines architecture consistency.
- Ambiguous URI ownership increases operational flakiness (expired links, re-synthesis storms).

## Handoff

**From**: Architect
**Artifact**: agent-output/architecture/017-text-to-speech-plan-architecture-findings.md
**Status**: APPROVED_WITH_CHANGES

**Required Action**: Planner must update Plan 010 to address the required deltas above, then re-submit for architectural approval.
