# Analysis 008: TTS Voice Context Unknowns

**Plan Reference (if any)**: agent-output/planning/010-tts-voice-cloning-plan.md
**Status**: Draft

## Changelog
| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-19 | Analyst (self) | Investigate unknowns blocking the speaker-context architecture decision | Enumerated questions about IndexTTS-2 data shape, propagation path, and governance before locking the schema/contract |

## Objective
Answer the concrete unknowns that must be resolved before finalizing the architecture for Epic 1.7 (TTS/voice-cloning). The questions are:
1. Does IndexTTS-2 require raw reference audio or is a speaker embedding sufficient (and if so, what format)?
2. What sample rate, duration, and payload size does IndexTTS-2 expect for voice cloning so we can honor Kafka message-size limits?
3. How should speaker-context data be propagated (inline payload, reference URI, or embedding) across Gateway → VAD → ASR → Translation → TTS while respecting privacy/retention expectations?
4. What permissions/retention policy is required for storing speaker reference data if we persist it out-of-band?
5. What failure modes (missing reference, incompatible format) need to be handled gracefully so TTS can still run without crashing?

## Context
- Target area: `services/tts` behavior (future service) and the cross-service event contract/metadata that carries speaker context.
- Relevant artifacts: `agent-output/architecture/system-architecture.md`, `agent-output/architecture/006-tts-voice-cloning-architecture-findings.md`, `agent-output/roadmap/product-roadmap.md` (v0.4.0 & backlog sections).
- Constraints: Avro message-size limit (≈2 MiB broker cap, 1.5 MiB inline payload), correlation IDs must be preserved, speaker-context data is optionally optional for baseline voice output, and privacy/retention guardrails must not leak PII.

## Methodology
- Reviewed the roadmap/architecture artifacts to understand the current decision state (v0.4.0 release plan + options A/B/C from Architecture Findings 006).
- Inspected the architecture diagram and notes to track where speaker context could be injected or stored (Gateway → VAD → ASR → Translation → TTS).
- Scoped the unknowns to those explicitly blocking the choice among the listed options (inline clip vs URI vs embedding) and the associated governance implications.
- Did not have vendor docs in the repo, so recommendations rely on empirical research/testing steps.

## Findings
### Facts
- The roadmap schedules Epic 1.7 (TTS with IndexTTS-2) in v0.4.0, and the architecture findings already documented the need to propagate speaker context for voice cloning, but no data shape or flow has been finalized.
- Current architecture master allows speaker context as optional metadata; the implementations of Gateway/VAD/ASR/Translation treat it as pass-through without enforcing any format.
- There is no existing QA artifact or doc describing how much data the TTS model expects or how to represent it in Kafka events.

### Hypotheses
- Hypothesis 1: IndexTTS-2 requires a short (3–5 second) WAV clip (≈96 KB raw PCM @ 16kHz) as reference audio; if true, we must evaluate whether duplicating it across every pipeline hop (VAD → ASR → Translation → TTS) fits within the 1.5 MiB cap when combined with the main audio/payload.
- Hypothesis 2: A speaker embedding (vector) would allow us to keep Kafka payloads small, but only if IndexTTS-2 accepts embeddings and we can compute/serialize them reliably upstream (probably in VAD or a dedicated extractor); until this is confirmed we cannot commit to building an embedding pipeline.
- Hypothesis 3: Persisting the reference clip in an object store and passing a URI would reduce Kafka footprint but introduces storage governance and availability/resiliency concerns; until we know the TTS QoS expectations we cannot judge whether the added complexity is warranted.
- Hypothesis 4: If the speaker context is absent or invalid, TTS must revert to a default speaker or voice; we need to tier fallback behavior and communicate it in the architecture decision.

## Recommendations
1. **Vendor Research / Prototype**: Consult IndexTTS-2 documentation (or run a small experiment) to determine whether it can accept embeddings, what formats/durations are required, and what the API/SDK expects as input. Document the sample size + encoding so we can budget it in Kafka messages.
2. **Payload Modeling**: Once the required payload size is known, model how the chosen propagation strategy (inline clip vs embedding vs URI) affects message size and latency at each pipeline hop; identify whether a split (e.g., store clip once in object store, propagate URI) is necessary to stay within the 1.5 MiB cap.
3. **Governance Proposal**: Draft a retention/privacy statement for the speaker context (if stored) covering TTL, access patterns, and how correlation IDs are kept separate from identifiable speaker data; bring this to the architecture decision review so compliance is baked in.
4. **Failure Handling Strategy**: Define fallback behavior for missing/invalid speaker context (e.g., default voice, degrade gracefully) and surface it in the architecture decision so implementers know what to do when the data is unavailable.
5. **Decision Gate**: Freeze the speaker-context propagation path only after #1–#4 are resolved; otherwise, leave the schema change as optional fields referenced in the Architecture Findings with the understanding that the final contract will not be locked until the unknowns are resolved.

## Open Questions
- Does IndexTTS-2 require raw reference audio or can it consume embeddings? If raw audio, what are the constraints (duration, format, sample rate)?
- If the reference clip is a few hundred kilobytes, can our Kafka topology carry it across all stages without violating the 1.5 MiB limit when combined with the existing payload?
- Would storing the clip in an object store (and passing a URI) be acceptable, or does that violate the thesis goal of a lightweight walking skeleton?
- What privacy/retention expectations apply to the reference clip (e.g., must it be deleted after the session, who can read it)?
- How should downstream services behave when speaker context is missing or invalid—should they fall back to default voice or raise an error?

## Handoff
**To**: Planner/Architect (future epic 1.7 planning)
**Artifact**: agent-output/analysis/008-tts-voice-context-unknowns-analysis.md
**Status**: Draft – needs the research recommended above before being marked complete
**Key Context**:
- The speaker-context propagation path is the last blocking uncertainty for the TTS architecture decision.
- Until the IndexTTS-2 data expectations are known, the plan must treat speaker context as an optional field (in the schema) and delay committing to a propagation pattern.
**Recommended Action**: Execute the vendor research/prototype steps, model the payload impact, set governance/retention expectations, and document the failover behavior so the architecture decision can be finalized.
