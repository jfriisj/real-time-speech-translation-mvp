---
ID: 028
Origin: 028
UUID: 9c17e4a2
Status: Planned
---

# Analysis 028: Category A (TTS) E2E timeouts — cold-start latency dominated by Kafka consumer group rebalance

## Value Statement and Business Objective
The TTS E2E pipeline smoke tests are used as a confidence gate for release readiness. Intermittent timeouts (especially after restarts) reduce trust in the pipeline and slow iteration. The objective of this analysis is to determine whether observed timeouts are caused by “no output produced” failures vs tail-latency mechanics, and to identify the dominant contributor to the cold-start/tail behavior so future investigation can be targeted.

## Objective
- Convert “why does the smoke test time out waiting for `AudioSynthesisEvent`?” from an unknown to a known mechanism with reproducible evidence.
- Distinguish latency sources (consumer positioning, service processing time, Kafka group rebalancing) using measured timestamps.

## Context
- Category A from Analysis 027: E2E smoke can time out waiting for `AudioSynthesisEvent` on `speech.tts.audio`.
- The TTS service consumes `speech.translation.text` with `CONSUMER_GROUP_ID=tts-service` (fixed across restarts).
- The host smoke test (`tests/e2e/tts_pipeline_smoke.py`) primes its output-topic consumer assignment before publishing input, so “missed output due to late subscription” is not a strong fit for the primary flake.

## Methodology
1. Empirically measure end-to-end latency (publish input → output consumed) in steady state.
2. Force cold-starts by restarting the `speech-tts-service` container.
3. Compare two scenarios:
   - **Immediate publish after restart** (worst-case)
   - **Delayed publish after restart** (publish only after waiting >45s)
4. Correlate with TTS logs for correlation_ids and compare against `synthesis_latency_ms` to see whether the delay is inside synthesis vs before synthesis begins.
5. Capture Kafka message timestamp metadata at the consumer (output topic) to rule out consumer-side delays.

## Findings

### Verified
1. **Steady-state publish → consume latency is low (sub-2s)**
   - A dedicated probe (publishing `TextTranslatedEvent` then polling for `AudioSynthesisEvent`) observed: `e2e_wall_s ~0.4–2.0s`.
   - Kafka message timestamp age at consumer was ~`0.01–0.02s`, implying the consumer receives the output almost immediately after the producer writes it.

2. **Immediate publish after restarting `speech-tts-service` produces a consistent ~41–43s delay**
   - Three restart cycles with immediate publish observed `e2e_wall_s`:
     - 40.658s
     - 42.523s
     - 41.850s
   - In TTS logs, the same correlation_ids show `synthesis_latency_ms ~1.7–2.3s`.
   - Conclusion: the ~60–95th percentile latency after restart is dominated by pre-synthesis delay (time before the service begins processing the event), not by the ONNX inference itself.

3. **Waiting 55s after restart before publishing collapses e2e back to ~2s**
   - Restart TTS, wait 55 seconds, then publish:
   - Observed `e2e_wall_s ~2.0s`.
   - This is a strong match for Kafka consumer-group rebalance/session-timeout behavior after a crash/restart with a *fixed* `group.id`.

4. **TTS publish timestamps align with the rebalance-delay hypothesis**
   - In logs, `TTS service started` is emitted shortly after restart.
   - First `Published AudioSynthesisEvent` occurs ~42–44 seconds later when a message is published immediately post-restart.
   - When publish is delayed (55s), this gap disappears.

### High-confidence inference
1. **Dominant cold-start/tail contributor is Kafka consumer group recovery time after restart (not compute)**
   - The ~42s plateau matches typical `session.timeout.ms` defaults in Kafka consumer clients.
   - The “delay disappears when waiting >45s” pattern is hard to explain via ONNX/model-init alone (model-init would delay the *startup log*, and would not reliably vanish with a 55s wait before publishing).

### Hypotheses (remaining unknowns)
1. **Why did a prior run time out at 90s and still later publish?**
   - Confidence: Medium.
   - Fastest disconfirming test: reproduce a >90s delay with controlled restart/publish timing and capture Kafka group coordinator logs/metrics (or consumer debug logs) to verify actual rebalance duration.
   - Missing telemetry: consumer group assignment events (assignment acquired timestamp, partition list) and consumer config values (`session.timeout.ms`, `max.poll.interval.ms`, `group.instance.id`) logged at startup.

## System Weaknesses (Architecture / Code / Process)
- **Architecture**: E2E “timeout” conflates multiple latency sources (Kafka group stabilization vs compute vs storage), making failures ambiguous.
- **Code/Telemetry**: TTS logs only record `synthesis_latency_ms` (post-consumption). There is no structured log for:
  - message-consumed timestamp
  - partition assignment obtained timestamp
  - “processing start” timestamp
   This prevents a deterministic breakdown of the ~95% of cold-start time that is currently “invisible”.
- **Process**: Smoke tests run with shortened timeouts during investigation; without an explicit note that post-restart tail can be ~50s, engineers can mistake expected rebalance delay for functional failure.

## Instrumentation Gaps

### Normal (always-on)
- Log once per startup:
  - consumer config values relevant to rebalance (`group.id`, `session.timeout.ms`, `heartbeat.interval.ms`, `max.poll.interval.ms`).
- Log once per partition assignment change:
  - assignment acquired timestamp and assigned partitions.
- Log per message (structured):
  - `event_name=tts_input_received`, `correlation_id`, `kafka_partition`, `kafka_offset`, and `kafka_timestamp_ms`.

### Debug (opt-in)
- Enable confluent-kafka debug categories for consumer group join/rebalance (`debug=consumer,cgrp,protocol`).
- Emit periodic “waiting_for_assignment” heartbeats with elapsed seconds during startup for quick triage.

## Analysis Recommendations (next steps)
1. Re-run the smoke test with a deliberately short timeout (e.g., 30s) under two conditions:
   - publish immediately after restart (expected fail)
   - publish after waiting 55s (expected pass)
   This validates that the test failure mode is latency-driven and not functional failure.
2. If >90s delays recur, collect a Docker logs snapshot (all services + Kafka) and enable debug-level consumer group logs for a single run.
3. Add the missing “assignment acquired / input received” timestamps (Normal telemetry) to make future RCA deterministic.

## Open Questions
1. What exact Kafka client defaults are currently in effect for `tts-service` (especially `session.timeout.ms`)? (Not logged today.)
2. Do other services (ASR/translation/VAD) share the same fixed group.id + restart behavior, implying similar tail latency in other pipeline segments?
3. Is the earlier >90s delayed publish explained by a different mechanism (e.g., repeated crash loops, coordinator instability, or model-cache cold download), or was it an outlier of the same rebalance phenomenon?

## Changelog
- 2026-01-28: Created from Category A deepening work; added verified cold-start evidence and rebalance-delay determination.
- 2026-01-28: Marked Planned; used as input to Plan 028.
