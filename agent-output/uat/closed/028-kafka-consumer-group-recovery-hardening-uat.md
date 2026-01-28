---
ID: 028
Origin: 028
UUID: 4f6b2c1d
Status: Committed for Release v0.5.0
---

# UAT Report: Plan 028: Kafka Consumer Group Recovery Hardening (Reduce post-restart tail latency)

**Plan Reference**: [agent-output/planning/closed/028-kafka-consumer-group-recovery-hardening-plan.md](agent-output/planning/closed/028-kafka-consumer-group-recovery-hardening-plan.md)
**Date**: 2026-01-28
**UAT Agent**: Product Owner (UAT)

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | QA | Validate value statement | Targeted unit tests pass and the implementation doc logs mid-project smoke tooling updates; QA report still marks integration evidence as pending. |
| 2026-01-28 | UAT | Validate QA evidence + business value | Implementation delivers the value statement per the implementation summary, but QA remains in-progress and no integration results have been posted; release blocked until QA updates the record. |
| 2026-01-28 | QA | Record integration evidence | Compose rebuild plus steady-state/cold-start `tests/e2e/tts_pipeline_smoke.py` runs and their telemetry outputs are recorded in the QA artifact. |
| 2026-01-28 | DevOps | Record commitment | UAT artifact marked as committed for release v0.5.0 and moved to closed/ during Stage 1 processing. |

## Value Statement Under Test
As an operator/contributor, I want services to recover Kafka consumption quickly after restarts, so that end-to-end smoke tests and development bring-up are reliable and do not fail due to predictable consumer group stabilization delays.

## UAT Scenarios
### Scenario 1: Rapid post-restart consumption with observable telemetry
- **Given**: Kafka-consuming services start with the shared consumer tuning helper and emit the low-volume telemetry events defined in the plan.
- **When**: A service (e.g., TTS) restarts and a publish occurs immediately afterward.
- **Then**: The tuned consumer parameters, assignment acquisition, and first input timestamps demonstrate the restart tail latency shrink and remain diagnosable.
- **Result**: PASS
- **Evidence**: The implementation summary documents the shared helper, per-service telemetry, and the targeted consumer wrapper on-assign updates that realize this behavior ([agent-output/implementation/closed/028-kafka-consumer-group-recovery-hardening-implementation.md](agent-output/implementation/closed/028-kafka-consumer-group-recovery-hardening-implementation.md)).

### Scenario 2: Smoke tooling distinguishes steady-state vs cold-start recovery
- **Given**: The `tests/e2e/tts_pipeline_smoke.py` script can run in either `steady-state` or `cold-start` mode against the local stack.
- **When**: Both modes are executed after rebuilding the compose stack.
- **Then**: Steady-state runs pass without waiting for rebalances, and cold-start runs intentionally exercise the restart path, generating telemetry for assignment vs input timing.
- **Result**: PASS
- **Evidence**: Test execution logs in the implementation doc record rebuilding the stack and running `TTS_SMOKE_MODE=steady-state`/`cold-start` smoke scripts plus the script itself captures the mode logic ([tests/e2e/tts_pipeline_smoke.py](tests/e2e/tts_pipeline_smoke.py), [agent-output/implementation/closed/028-kafka-consumer-group-recovery-hardening-implementation.md](agent-output/implementation/closed/028-kafka-consumer-group-recovery-hardening-implementation.md)).

## Value Delivery Assessment
The implementation doc ties the shared consumer tuning helper, low-volume telemetry, and smoke tool updates back to the plan’s value statement: restart recovery latency is reduced while the telemetry sequence (config → assignment → first input) remains available for diagnostics. QA now adds runtime proof by logging both steady-state and cold-start smoke runs, completing the audited evidence chain.

## QA Integration
**QA Report Reference**: [agent-output/qa/closed/028-kafka-consumer-group-recovery-hardening-qa.md](agent-output/qa/closed/028-kafka-consumer-group-recovery-hardening-qa.md)
**QA Status**: QA Complete
**QA Findings Alignment**: QA now records the compose rebuild plus steady-state and cold-start `tests/e2e/tts_pipeline_smoke.py` runs. Both modes succeeded while emitting the required `kafka_consumer_*` telemetry events, so the integration evidence chain is complete.

## Technical Compliance
- **Plan deliverables**: PASS (shared consumer config builder + validation, unified telemetry events, `KafkaConsumerWrapper` on-assign support, service wiring updates, and smoke-mode separation are all documented in the implementation log).<br>- **Test coverage**: Unit coverage plus steady-state/cold-start TTS smoke integration are now QA-verified, demonstrating both the helper wiring and telemetry events behave under the tuned configuration.<br>- **Known limitations**: None remaining; QA confirmed the integration gate has closed.

## Objective Alignment Assessment
**Does code meet original plan objective?**: YES<br>**Evidence**: The shared helper plus per-service instrumentation deliver the rapid restart recovery telemetry timeline called for in the plan, and the smoke tooling isolates steady-state vs cold-start behavior for operators; QA confirms both modes run with the expected telemetry ([agent-output/implementation/028-kafka-consumer-group-recovery-hardening-implementation.md](agent-output/implementation/028-kafka-consumer-group-recovery-hardening-implementation.md), [agent-output/qa/028-kafka-consumer-group-recovery-hardening-qa.md](agent-output/qa/028-kafka-consumer-group-recovery-hardening-qa.md)).<br>**Drift Detected**: None.

## UAT Status
**Status**: UAT Complete<br>**Rationale**: QA now confirms both steady-state and cold-start smoke runs succeeded with the tuned Kafka consumer settings and low-volume telemetry, satisfying the value statement with audited evidence.

## Release Decision
**Final Status**: APPROVED<br>**Rationale**: QA confirms both steady-state and cold-start smoke runs pass with the tuned Kafka consumer configuration, so the value statement is validated and the change is release-ready. <br>**Recommended Version**: patch (v0.5.0)<br>**Key Changes for Changelog**:
- Standardized consumer tuning helper + validation with per-service telemetry events to expose assignment and first-input timing.
- Added on-assign support to `KafkaConsumerWrapper` and rewired every Kafka consumer to use the wrapper, removing direct `subscribe` calls.
- Extended `tests/e2e/tts_pipeline_smoke.py` with explicit steady-state vs cold-start modes and documented the compose rebuild + smoke command sequence.

## Next Actions
1. Notify DevOps that QA and UAT artifacts now document the steady-state and cold-start smoke evidence so Plan 028 can be included in v0.5.0.<br>2. Monitor runtime telemetry for the `kafka_consumer_*` events in the upcoming release candidate to ensure the restart recovery behavior observed in QA reproduces in more complex workloads.
