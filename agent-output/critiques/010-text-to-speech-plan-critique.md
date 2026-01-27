# Plan Critique: 010-text-to-speech (TTS)

**Artifact**: agent-output/planning/010-text-to-speech-plan.md
**Related Analysis**: agent-output/analysis/010-text-to-speech-plan-analysis.md
**Related Architecture Findings**: agent-output/architecture/017-text-to-speech-plan-architecture-findings.md
**Date**: 2026-01-27
**Status**: APPROVED (Revision 4)

## Changelog

| Date | Handoff | Request | Summary |
|------|---------|---------|---------|
| 2026-01-27 | User → Critic | Critique for clarity/completeness/scope/risks/alignment | Initial critique created. |
| 2026-01-27 | User → Critic | Re-critique after plan revision | Reviewed Plan 010 Rev 24; contract gates mostly resolved; remaining scope/QA/governance items noted. |
| 2026-01-27 | User → Critic | Re-critique after plan revision | Reviewed Plan 010 Rev 25; addressed QA threshold concern and clarified `audio_uri` consumer + expiry behavior; governance note remains. |
| 2026-01-27 | User → Critic | Re-critique after architecture re-review | Reviewed Plan 010 Rev 25 against Findings 017; identified architectural misalignment on speaker context, schema compatibility wording, retention defaults, and `audio_uri` ownership. |
| 2026-01-27 | User → Critic | Re-critique after plan revision | Reviewed Plan 010 Rev 26; Verified alignment with Architecture Findings 017. All blocking issues resolved. |
| 2026-01-27 | User → Critic | Critique for clarity/completeness/scope/risks/alignment | Reviewed Plan 010 Rev 26 against the planner rubric; corrected outdated critique assertions; captured remaining non-blocking risks/questions. |

## Value Statement Assessment
- **Present and well-formed**: “As a User, I want…, So that…” is clear.
- **Business objective is understandable** (hands-free consumption) and matches the epic intent.

## Overview
Plan 010 (Rev 26) is **architecturally aligned** and ready for implementation. It correctly incorporates the Claim Check pattern, adheres to Schema Registry compatibility policies (`BACKWARD`), ensures pass-through of speaker context for future extensibility, and defines a robust URI lifecycle managed by the Gateway.

## Roadmap Alignment
- **Aligned**: Target release `v0.5.0` and Epic 1.7 user story match the roadmap wording.
- **Minor documentation drift risk**: the roadmap “Status Notes” mention an older plan revision; this does not block the plan but can confuse cross-team readers.

## Architectural Alignment
- **Aligned**: Plan explicitly references Findings 017 and matches its requirements.
- **Speaker Context**: Correctly set to "Pass-through" to support future Voice Cloning without contract breakage.
- **Claim Check**: Correctly implements strict inline (<1.25 MiB) vs external (>1.25 MiB) handling.
- **Security**: "Don't log presigned URLs" constraint is present.
- **Microservices**: Decoupling logic (SynthesizerFactory) from implementation (Kokoro ONNX) is preserved.

## Completeness (Contract Decision Gates)
- **Message/schema contract**: Present (producer/consumer, evolution rules, Registry `BACKWARD`).
- **Speaker context propagation**: Present (explicit pass-through requirement).
- **Data retention & privacy**: Present (24h default target + configurable; “do not log presigned URLs”).
- **Observability**: Present (trace propagation + required log fields). Consider adding minimal metrics as a future refinement (non-blocking).

## Scope Assessment
- Scope is properly constrained to the TTS service implementation.
- Integration points with Gateway (for URI presigning) and MinIO (for object storage) are clearly defined.
- Future dependencies (Voice Cloning) are enabled by the contract but excluded from current processing scope, which is appropriate for MVP.

## Clarity Notes
- The plan is generally clear and structured.
- The “Verification & Acceptance” section is readable, but some bullets read like QA test steps (e.g., “Send ‘Hello World’ …”). Per repo guidance, consider keeping plan-level acceptance as observable outcomes and moving procedural test steps into QA artifacts.

## Technical Debt Risks
- **Low**: The updated plan mitigates the major debt risk (contract divergence) by strictly adhering to the "Backward Compatible" and "Pass-through" strategies.

## Risks & Rollback Thinking
- Risks are plausible and include mitigations (model download/caching; tokenization complexity).
- Rollback intent is good (avoid a total pipeline stall), but the proposed “system-speech fallback / mock for v0.5.0 demo” may conflict with the stated strategic constraint (“must use Kokoro-82M”). This is not a blocker, but it should be clarified as either (a) a non-release demo-only fallback, or (b) an explicit exception process.

## Findings

### Critical (Blocking)

#### C1 — Speaker Context Propagation Misaligned with Architecture
**Status**: RESOLVED

**Resolution**: Plan Rev 26 now explicitly states: "The service receives optional `speaker_reference_bytes` ... and propagates it to `AudioSynthesisEvent`. (Even if Kokoro does not use it)." This aligns with the "Pass-through" architecture requirement.

#### C2 — QA Thresholds Missing
**Status**: RESOLVED

**Resolution**: Plan Rev 26 includes explicit performance verification intent (RTF measured/recorded) without over-specifying plan-level benchmark protocols.

#### C3 — Retention Default Conflicts with Architecture Guardrail
**Status**: RESOLVED

**Resolution**: Plan Rev 26 updates retention to "24h default (configurable)", aligning with the architecture guardrail.

#### C4 — Schema Compatibility Conflicts with Registry Policy
**Status**: RESOLVED

**Resolution**: Plan Rev 26 specifies "Schema Compatibility: BACKWARD", matching the platform Registry policy.

### Major (Important)

#### M5 — URI Ownership/Expiry Strategy Fragile
**Status**: RESOLVED

**Resolution**: Plan Rev 26 adopts the "Internal Key (Preferred)" strategy where the Gateway is responsible for presigning at read-time, addressing the fragility of long-lived presigned URLs.

## Recommendations
- **Proceed to Implementation**: The plan is now robust and aligned with all known constraints.
- **QA Handover**: Ensure QA has a clear, agreed method to capture RTF/latency evidence (the linked analysis calls out this unknown).
- **Gateway Team**: Confirm the Gateway presigning responsibility for internal object keys is tracked as an integration requirement.

## Questions (Non-Blocking)
1. For the “hard reject > 500 chars” rule, should “drop” route to a DLQ / error topic (for debuggability), or is log-only sufficient for MVP?
2. Is “system-speech fallback / mock” an acceptable rollback for release artifacts, or only for local/demo runs?
3. Do we want a minimal metrics contract (counters + histogram) in v0.5.0, or is logging + tracing sufficient until v0.6.0 observability work?
