# Analysis 003: Translation Service Research Gaps

## Value Statement and Business Objective
**As** the architecture reviewer,
**I need** to validate the unstated assumptions in Plan 003 before implementation,
**So that** the Translation Service can be implemented without ambiguity or surprise rework.

## Current Context
- **Plan**: agent-output/planning/003-translation-service-plan.md defines the MVP scope for Epic 1.3 and relies on the shared contracts described in agent-output/architecture/system-architecture.md.
- **Architecture**: The master doc mandates canonical topics (`speech.asr.text`, `speech.translation.text`), Avro envelopes, and correlation tracking; it leaves some operational semantics (language defaults, failure behavior) unconstrained.
- **Supporting docs**: The thesis MVP plan (`Analysis-and-design-of-a-platform-for-real-time-speech-translation-/docs/MVP-FIRST_PLAN.md`) and the end-to-end flow diagrams (`docs/end-to-end-flows.md`) describe `target_language` metadata but do not fix defaults or handling policies.
- **Shared schema/tooling**: `shared/speech-lib/src/speech_lib/events.py` and the serialization test confirm the Avro contract requires `text`, `source_language`, and `target_language` in `TextTranslatedEvent` and that sample data currently uses `target_language = "es"`.

## Research Findings (Gaps / Unverified Assumptions)
1. **Target-language configuration is not defined**
   - _Observation_: The plan currently says `payload.target_language` comes "from config/mock (e.g. "es")." There is no canonical default or documented config key elsewhere in the repo—`MVP-FIRST_PLAN.md` lists the field as required but does not prescribe a default or allowed set, and the `shared` tests simply hardcode "es" in the example.
   - _Impact_: Implementers may choose inconsistent defaults (EN→ES, EN→EN, etc.) or expose a per-deployment option without guidance, which hinders repeatable demos and QA.
   - _Research need_: Determine whether the Translation Service should hardcode a single target language (and which one) for the MVP or expose an explicit environment/configuration variable with validation.

2. **Failure-handling semantics (“log and drop”) are underspecified for Kafka offsets**
   - _Observation_: Neither the architecture doc nor the plan describes what "drop" means at the Kafka level. Without clarification, the consumer could either (a) log and commit the offset (true drop) or (b) leave it uncommitted and retry forever, depending on the Kafka client/handler implementation.
   - _Impact_: A poison event (malformed payload, translator error) might cause the service to spin or skip an offset unexpectedly, undermining reliability and observability.
   - _Research need_: Confirm the expected offset/commit behavior upon logging an error (e.g., log→commit→continue) and whether any metrics or alerts should accompany drop events.

3. **Language metadata propagation is assumed but unverified**
   - _Observation_: `TextRecognizedEvent` includes `language` in its payload (`TextRecognizedPayload.language`). The plan currently copies that value into the output `source_language`, but this assumption is not documented in the architecture decisions and should be deliberately noted.
   - _Impact_: If future producers stop filling `payload.language`, the Translation Service might emit `source_language` as empty, breaking downstream semantics or metrics.
   - _Research need_: Confirm that the contract guarantees `TextRecognizedEvent.payload.language` is populated, or alternatively add validation/logging if the field is missing.

## Next Steps
1. Decide and document the MVP target-language configuration surface (e.g., a single env var with default `"es"` and optional override). Capture this in the plan so QA/demo expectations are consistent.
2. Define Kafka consumer failure semantics for translation errors: when to commit offsets, whether to emit metrics/log markers, and how to avoid poison-pill loops.
3. Explicitly call out the dependency on `TextRecognizedEvent.payload.language` in the plan (and potentially add validation) so translators cannot proceed with empty source-language metadata.
