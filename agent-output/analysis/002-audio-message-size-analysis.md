# Analysis 002: Audio Payload Policy Unknowns

## Value Statement and Business Objective
**As** the architect on the shared infrastructure epic,
**I need** the open questions around payload sizing and serialization scope resolved,
**So that** we can finalize the contract artifact (schemas + `speech-lib`) without risking mismatched expectations across downstream services or invalid schema submission.

## Current Context and Target Area
- **Plan under review**: agent-output/planning/001-shared-infrastructure-plan.md (Epic 1.1, now delivered).
- **Architecture source**: agent-output/architecture/system-architecture.md (defines canonical naming, topic taxonomy, compatibility rules).
- **Target area**: The `AudioInputEvent` schema/topic (`shared/schemas/avro` + shared library producer/consumer helpers) and `speech-lib` payload handling, because these components enforce message size, schema subjects, and shared artifact boundaries.
- **Question(s)**: (1) Do we reject inline audio payloads bigger than 1.5 MiB in v0.1.0, or do we accept them via a reference/URI pattern? (2) What exact Kafka broker message size limit must we assume in local development? (3) Does the shared artifact need to enforce any additional serialization guarantees (size check, correlation propagation) beyond the current plan text?

## Unknowns Blocking the Architectural Decision
1. **Oversized audio behavior for MVP**: Plan text is inconsistent—one section says audio >1.5 MiB must use a reference/URI, another says the producer rejects oversized payloads. Without this decision we cannot define the schema (inline blob vs reference fields), docs for service implementers, or the shared library’s validation logic.
2. **Kafka broker max message size assumption**: The plan states a 2 MiB limit and approximates it as “~2 minutes of 16kHz mono PCM,” which is factually incorrect and could misalign expectations when services send real audio. We need a confirmed broker config and accurate guidance for the shared producer/consumer to avoid runtime errors or silent truncation.
3. **Shared artifact enforcement scope**: The architecture forbids business logic in the shared contract, yet the plan currently sketches producer/consumer helpers that may drift toward a mini-SDK. We need clarity on whether these helpers should only perform serialization/envelope population (with size/correlation checks) or also orchestrate retries/topic routing.

## Methodology and Evidence
- Reviewed Plan 001 for contradictions in the “Assumptions & Open Questions” section vs “Contract Canon” (lines 18-36) to surface the conflicting statements.
- Cross-checked architecture master (system-architecture.md) for non-negotiables such as canonical naming, compatibility, and shared artifact limits; these decisions highlight where plan ambiguity would violate architecture.
- Considered downstream impact: Epic 1.2 services will implement producers/consumers based on this contract; mismatched expectations (e.g., unexpected rejection of large audio) would break the timeline.

## Recommendations / Next Steps
1. **Decision needed**: Confirm the MVP behavior for payloads >1.5 MiB. If rejection is chosen, update the plan to document that and reflect it in the schema (`AudioInputEvent` uses a fixed `bytes` field); if references are allowed, add the reference field (URI + metadata) and related validation.
2. **Broker configuration**: Ask the infrastructure owner what `message.max.bytes` value the local Kafka will actually run with for v0.1.0 and update the plan/test scripts to assert that value rather than rely on an inaccurate duration estimate.
3. **Shared library scope**: Define an explicit “allowed helpers” list (serialization, envelope filling, correlation propagation, size enforcement) and a “forbidden behavior” list (retries, topic routing, domain validation) so implementers know how far the artifact may evolve.

Once answers arrive, we can re-run this architectural assessment and either approve the implementation or surface any new risks.
