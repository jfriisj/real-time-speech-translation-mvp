# Analysis 004: End-to-End Traceability & Latency

## Value Statement and Business Objective
**As** the measurement/observability steward for the Walking Skeleton,
**I need** an external probe that can publish audio ingress, listen for ASR/translation events, and compute latency deltas,
**So that** the thesis can claim the pipeline returns translated text with predictable latency, a preserved `correlation_id`, and high traceability visibility.

## Current Context
- **Plan under review**: [agent-output/planning/004-traceability-and-latency-plan.md](agent-output/planning/004-traceability-and-latency-plan.md) (Epic 1.4, traceability).
- **Roadmap reference**: `Epic 1.4` currently lives under Release v0.2.0 (Core Services) with status Planned; no v0.2.1 release entry exists in [agent-output/roadmap/product-roadmap.md](agent-output/roadmap/product-roadmap.md#L77-L116).
- **Architecture reference**: [agent-output/architecture/system-architecture.md](agent-output/architecture/system-architecture.md#L37-L72) and [agent-output/architecture/005-asr-service-architecture-findings.md](agent-output/architecture/005-asr-service-architecture-findings.md) expect an external producer/CLI to publish `AudioInputEvent` to `speech.audio.ingress` and the downstream services to preserve `correlation_id` and Avro timestamps.
- **Supporting code**: `BaseEvent` in [shared/speech-lib/src/speech_lib/events.py](shared/speech-lib/src/speech_lib/events.py#L22-L54) stamps events with `timestamp=int(time()*1000)` at construction time; both services create their events via this helper. `KafkaConsumerWrapper` in [shared/speech-lib/src/speech_lib/consumer.py](shared/speech-lib/src/speech_lib/consumer.py#L1-L41) defaults to `auto.offset.reset=earliest` and exposes manual `commit_message` for control.

## Methodology
- Read the plan and identified its explicit success criteria (run 100 chained requests, compute deltas, log timestamps) plus release target v0.2.1.
- Cross-referenced the roadmap to confirm the stated release target is absent (only v0.2.0/v0.3.0 entries exist with Epic 1.4 under v0.2.0) and tagged as Planned.
- Consulted the architecture findings for Epic 1.2 and the master architecture doc to understand the canonical external producer expectation and contract constraints (topic names, payload size, correlation enforcement).
- Inspected shared support code for BaseEvent timestamp behavior and consumer configuration to understand what the probe will rely on when it consumes ASR/translation events.
- Reviewed the ASR integration test ([services/asr/tests/test_integration_asr.py](services/asr/tests/test_integration_asr.py#L1-L54)) to confirm how `AudioInputEvent` payloads are created and published, confirming the probe can mimic that approach.

## Findings
### Fact: Release target mismatch
Plan 004 proclaims a new release `v0.2.1 (Performance Validation)` as the target for the probe. The current roadmap documents Release v0.2.0 (Core Services) as Released, and Epic 1.4 is still marked Planned without any new release entry; the next release stub is v0.3.0 (Expand & Speak). Without an official release line for v0.2.1, teams lack clarity on sequencing, gating, and tagging, and there is no process artifact (roadmap entry, release doc) that records who owns a patch bump or how the release differs from v0.2.0.

### Fact: `timestamp` semantics reflect event construction time, not downstream completion
`BaseEvent` instantiates `timestamp` via `int(time() * 1000)` when the event object is created ([shared/speech-lib/src/speech_lib/events.py](shared/speech-lib/src/speech_lib/events.py#L22-L54)). Both `asr-service` and `translation-service` call `BaseEvent(...)` immediately before publishing, meaning T1/T2 are the moments events are emitted; they do not represent when the services started processing or when Kafka consumers acknowledged them. The probe’s delta calculations will therefore measure publication latency (ingress-to-publish) rather than total wall-clock processing inside the consumer loops, which may be acceptable but should be documented explicitly so thesis claims are precise.

### Fact: External probe must behave like the integration harness that publishes `AudioInputEvent`
Architecture findings state the MVP expects an external producer/CLI/script to inject `AudioInputEvent` into `speech.audio.ingress` ([agent-output/architecture/005-asr-service-architecture-findings.md](agent-output/architecture/005-asr-service-architecture-findings.md#L34-L52)). The ASR integration test builds an `AudioInputEvent` with `BaseEvent` and publishes it with `KafkaProducerWrapper` ([services/asr/tests/test_integration_asr.py](services/asr/tests/test_integration_asr.py#L25-L56)). Therefore, the probe should mimic this pattern (create `BaseEvent`, keep audio payload ≤1.5 MiB, send to `speech.audio.ingress`) rather than inventing a new ingress mechanism; otherwise it would drift from the shared contract and may break schedule.

### Fact: Probe consumer behavior needs isolation policies to avoid contaminated measurements
`KafkaConsumerWrapper.from_confluent` defaults to `auto.offset.reset=earliest` and not to “latest”, so a new consumer would reprocess existing history if not configured otherwise ([shared/speech-lib/src/speech_lib/consumer.py](shared/speech-lib/src/speech_lib/consumer.py#L12-L33)). The plan does not explain whether the probe will use a dedicated group ID, commit offsets, or start from the latest message. Without a policy (unique group IDs, `enable.auto.commit` false, explicit seeks), repeated runs risk measuring stale data, interfering with production consumers, or reporting false latency numbers.

## Hypotheses
1. The roadmap team may have intended to introduce v0.2.1 for a measurement release, but until the roadmap explicitly defines that release, the plan’s version bump will conflict with release governance.
2. Because BaseEvent records the timestamp at instantiation, the probe’s latency deltas are effectively publishing latency, not the full service processing latency; if the thesis requires latency between ingest and translation completion, the probes should capture consumer/producer arrival times or use Kafka record timestamps.
3. If the probe commits offsets or reuses a production group ID, we risk interference with QA/production flows; the plan needs to decide whether to treat the probe as a read-only consumer (no commits) or as a separate measurement pipeline.

## Recommendations / Next Steps
1. Align with the roadmap: either add a v0.2.1 release entry for Epic 1.4 (explicitly referencing this measurement probe) or keep the probe within Release v0.2.0 and drop the v0.2.1 mention from the plan. Document which release owns the measurement artifact.
2. Add a “Timestamp Semantics” subsection that clarifies that `timestamp` equals event creation/publication time (via `BaseEvent`) and therefore the probe measures emission time differences, not internal processing. If the thesis requires wall-clock latency between service boundaries, consider capturing Kafka receive times on the probe side to complement the event timestamps.
3. Define probe consumer policies: assign a dedicated group ID (e.g., `traceability-probe`), disable auto-commit (if committing, take care not to affect other consumers), and start from latest offsets (or seek to end) so each run measures fresh requests. Document how the probe handles timeouts/broken chains (e.g., 10s per correlation_id) and how it reports P50/P90/P99 buckets.
4. Reuse the existing integration harness approach when generating `AudioInputEvent` (BaseEvent + ≤1.5 MiB audio payload) so we stay within the architecture’s contract boundaries and avoid extra ingestion layers. Mention this explicitly in the plan’s milestone description.

## Open Questions
1. Who owns/approves the decision to add Release v0.2.1? Should the plan keep the version number or align with existing roadmap releases?
2. What precise definition of `timestamp` should connect to thesis claims (publish time vs processing completion)?
3. Is the probe expected to publish `AudioInputEvent` directly to Kafka, or is there a separate CLI/HTTP ingress described in other docs?
4. What is the desired policy for consumer group IDs, offset commits, and start positions to ensure runs are clean and repeatable?

