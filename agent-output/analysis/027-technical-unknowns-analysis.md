---
ID: 027
Origin: 027
UUID: 7c1c14e0
Status: Active
---

# Analysis 027: Technical Unknowns — Deep Investigation (Stability, E2E Timeouts, Dependency Readiness)

## Changelog
| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | User → Analyst | Deep investigation requested | Initialized analysis scope, gathered existing evidence from QA reports + Memory, and defined hypotheses + fastest disconfirming tests. |
| 2026-01-28 | User → Analyst | Category (A) selected | Reproduced `AudioSynthesisEvent` timeout locally, then ran successful follow-up traces and captured Kafka consumer lag/offsets for the TTS pipeline. |

## Value Statement and Business Objective
**As** an operator/contributor,
**I need** the current “technical unknowns” converted into verified, evidence-backed causes,
**so that** the v0.6.0 integrated delivery train can proceed without recurring flaky E2E failures and ambiguous blame.

## Objective
1) Enumerate the technical unknowns currently blocking confidence (especially E2E timeouts and startup readiness).
2) Classify each as **Verified**, **High-confidence inference**, or **Hypothesis**, with evidence.
3) Define the minimum tests/telemetry required to collapse uncertainty quickly.

## Scope
**In scope** (based on current repo evidence):
- E2E timeouts waiting for `AudioSynthesisEvent`.
- Translation service readiness and its downstream impact on TTS E2E.
- Startup dependency readiness races (Schema Registry/Kafka).

**Out of scope**:
- Implementing fixes.
- Changing service code, configs, or plans.

## Methodology
Note: The repo’s requested `analysis-methodology` skill file was not found in-workspace (`**/*analysis-methodology*` returned none). Proceeding with a lightweight evidence protocol:
- Prefer determinations via reproduction/trace.
- When not provable, record hypotheses with confidence, fastest disconfirming test, and missing telemetry.

## Current Evidence (Verified)
### E1 — TTS QA indicates E2E timeouts (current state can be flaky)
- QA report for Plan 010 records that e2e inline/URI smoke tests timed out waiting for `AudioSynthesisEvent` on 2026-01-28.
- Unit tests and lint passed, pointing away from pure unit-level logic errors.

Source: `agent-output/qa/010-text-to-speech-qa.md`.

### E2 — Schema Registry readiness work exists and E2E once passed
- QA report for Plan 011 indicates an E2E TTS pipeline smoke run passed after translation readiness changes.
- Integration test for translation was skipped; coverage on `translation_service/main.py` remains low.

Source: `agent-output/qa/011-schema-registry-readiness-qa.md`.

### E3 — Local reproduction: smoke test can timeout even when TTS eventually publishes
Setup notes (local workstation):
- Host Python did not ship with `pip`; running the E2E smoke test required using the existing `.venv` and installing the local `speech-lib` via `uv pip`.

Observed behavior:
- Running `tests/e2e/tts_pipeline_smoke.py` via `.venv/bin/python` with `TTS_SMOKE_TIMEOUT=90` produced `TimeoutError: Timed out waiting for AudioSynthesisEvent`.
- Shortly after, the running `tts-service` container logs showed it *did* publish `AudioSynthesisEvent` for the same run’s `correlation_id` (example seen in logs: `tts-smoke-da079c85-f875-4ba4-9d33-3320124e3109`).

Interpretation:
- This establishes that the E2E symptom can be explained by “output event arrives after client timeout” (not necessarily “no output ever”).

### E4 — Follow-up: subsequent runs succeed quickly; consumer lag is zero
- A follow-up run with `TTS_SMOKE_TIMEOUT=300` completed successfully in ~7.6 seconds wall time.
- A subsequent run with `TTS_SMOKE_TIMEOUT=90` also succeeded in ~6.4 seconds.
- Kafka consumer group `tts-service` showed `LAG=0` on `speech.translation.text` at the time of inspection.

## High-Confidence Inferences
### I1 — E2E timeouts can be “late output” rather than “missing output”
**Why**:
- In at least one reproduced case, `tts-service` published the output event after the smoke test timed out.
- Follow-up runs were fast, suggesting intermittency (warm-up effects, scheduling variance, or occasional stalls) rather than a deterministic always-broken pipeline.

**Confidence**: Medium.

## Hypotheses (with disconfirming tests)
Note: `tests/e2e/tts_pipeline_smoke.py` publishes `TextTranslatedEvent` directly to `speech.translation.text` and waits on `speech.tts.audio`. This bypasses the translation service, so translation-service health is not a causal factor for failures of this specific smoke test.

### H0 — The smoke consumer can miss the output or time out during brief stalls
**Confidence**: Medium.
**Fastest disconfirming test**:
- Run the smoke test with a very low timeout (e.g., 30–60s) repeatedly (10–20 iterations) and correlate each failure with:
	- `tts-service` log timestamps for “Published AudioSynthesisEvent correlation_id=…”, and
	- Kafka offsets on `speech.tts.audio`.
If the event is produced but arrives after the timeout window (or is produced before the consumer is fully positioned), it will show up in the logs/offsets despite the client timeout.
**Missing telemetry**:
- Normal: log `event_name=tts_input_received` with `correlation_id` at the moment the message is successfully deserialized (before synthesis).
- Normal: log `event_name=tts_output_published` with `correlation_id` (already present) and add a monotonic duration since input receipt.

### H1 — Translation service is not consistently consuming/producing during the failing E2E runs
**Confidence**: Medium.
**Fastest disconfirming test**:
- During a failing run, produce a single `TextTranslatedEvent` or `TextRecognizedEvent` and observe whether translation logs show consumption and whether `TextTranslatedEvent` reaches Kafka.
**Missing telemetry**:
- Always-on structured log counters: `events_consumed_total`, `events_produced_total` by event type + `correlation_id`.

### H2 — Schema Registry readiness gating still has race/false-positive behavior
**Confidence**: Medium.
**Fastest disconfirming test**:
- Capture a cold-start compose run where failure happens and verify the exact timestamps: SR healthy → translation starts → schemas register → consumer loop begins.
**Missing telemetry**:
- Normal: a single “startup_phase” structured log event with phases (`waiting_for_kafka`, `waiting_for_schema_registry`, `consumer_loop_started`).
- Debug: per-attempt readiness probe timings and exceptions.

### H3 — Kafka consumer group offsets/commit-on-drop semantics cause “silent no output” in E2E
**Confidence**: Low–Medium.
**Fastest disconfirming test**:
- Inspect consumer group lag and offsets for translation/TTS consumers during the test window.
**Missing telemetry**:
- Normal: log when committing offsets for error/drop paths and include reason codes.

## System Weaknesses (Architecture/Process)
- Integration tests being skipped (Plan 011 QA) leaves a gap where regression can reappear without immediate detection.
- E2E success criteria rely on timing and compose bring-up order; without standardized startup-phase logs, attribution becomes guessy.

## Instrumentation Gaps
**Normal (always-on, low volume):**
- `startup_phase` event per service with monotonic timestamps.
- `events_consumed_total` / `events_produced_total` counters (log-structured is fine if metrics not present).
- `drop_reason` taxonomy for log-and-drop decisions.

**Debug (opt-in):**
- Dependency probe attempt logs (SR/Kafka), including exception class and duration.
- Kafka header dump for `traceparent` propagation on a sampled basis.

## Analysis Recommendations (Next Steps)
To convert unknowns → knowns quickly:
1) Reproduce one failing E2E timeout and capture a deterministic “state snapshot” (service logs + consumer group lag + SR health timeline).
2) Trace one `correlation_id` end-to-end: ingress → VAD → ASR → translation → TTS, confirming production points.
3) If reproduction is not possible quickly, pivot to adding the minimal Normal telemetry above (no implementation proposed here; only data requirements).

## Remaining Gaps (Unresolved)
- The specific mechanism for the initial local timeout is not proven (late publish vs consumer positioning vs transient stall).
- We did not capture a synchronized timestamped trace for the failing run (client publish time vs TTS input receipt vs TTS output publish vs consumer poll timeline).
- It is still unknown whether the recurring QA failures (240s default timeout) match the same "late output" pattern or a different failure mode where `tts-service` never publishes.
- The intermittency trigger is not identified (cold-start, model cache miss, CPU contention, Kafka rebalance/assignment timing, Schema Registry latency, or transient deserialization errors).
## Appendix: Local Repro Notes (Category A)
- Compose stack was running; Schema Registry reported healthy.
- Kafka topics present: `speech.translation.text`, `speech.tts.audio`.
- One local run timed out at 90s, while `tts-service` later logged `Published AudioSynthesisEvent` for the same correlation_id (suggesting late output can explain at least some timeouts).
- Subsequent runs completed quickly (~6-8s wall time).
- `tts-service` consumer group lag was 0 when inspected.
