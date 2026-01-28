---
ID: 030
Origin: 030
UUID: 2d5f7a9c
Status: Planned
---

# Analysis 030: Kafka Consumer Group Recovery Tail — What’s Actually Happening in Compose Right Now

## Changelog
| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | User → Analyst | Deep investigation requested | Determined the dominant source of uncertainty was a mismatch between workspace code and running Compose images; reproduced the ~45s restart tail on the old image and the reduced ~10–15s tail after rebuilding `tts-service` with Plan 028 tuning. |
| 2026-01-28 | Planner → Planner | Incorporated into Plan 028 | Updated Plan 028 Milestone 1 to require image/workspace parity verification before collecting any baseline evidence; moved this analysis to `closed/`. |

## Value Statement and Business Objective
Restart-induced tail latency (and the resulting “smoke test timeouts”) erodes confidence in end-to-end pipeline health and slows iteration. The business objective is to make post-restart behavior **predictable, diagnosable, and measurably improved** so the v0.5.0 release train can proceed without flaky gating.

## Objective
1) Convert “is the ~40–45s post-restart delay real in *this* environment?” into a known.
2) Convert “did Plan 028 tuning actually reduce the restart tail?” into a known.
3) Identify what remains unknown and what evidence is required next.

## Context
- Plan under investigation: `agent-output/planning/closed/028-kafka-consumer-group-recovery-hardening-plan.md`.
- Prior analysis: `agent-output/analysis/closed/028-tts-e2e-timeouts-rebalance-latency-analysis.md` attributes ~41–43s tail to Kafka consumer group recovery behavior.
- Running environment: local Docker Compose stack was already up.

## Methodology
Followed the repo’s analysis methodology:
- Prefer **Proven** findings via direct reproduction and container inspection.
- When uncertain, record gaps with the fastest disconfirming tests and required telemetry.

## Findings

### F1 (Proven): The Compose stack was running *stale service images* relative to the workspace
Evidence:
- `speech-tts-service` initially did **not** contain the Plan 028 tuning field (`Settings.consumer_session_timeout_ms`), confirming its image was older than the workspace code.
- After rebuilding and recreating `tts-service`, the field existed and defaulted to `15000`.

Impact:
- Any timing measurements collected before rebuilding were measuring **pre-Plan-028 behavior**, even though the workspace contains Plan 028 code.

### F2 (Observed): Pre-rebuild `tts-service` shows ~45s post-restart end-to-end delay
Evidence (reproduction):
- Restarted `tts-service` and ran `tests/e2e/tts_pipeline_smoke.py` in cold-start mode.
- The run completed successfully but took ~46s end-to-end (wall-clock between starting smoke and PASS), consistent with the earlier ~41–43s plateau.

Interpretation:
- This aligns with Kafka consumer group dead-member expiration / rebalance delays consistent with default Confluent consumer settings (often ~45s).

### F3 (Proven): After rebuilding `tts-service` with Plan 028 tuning, restart tail collapses to ~10–15s
Evidence:
- Rebuilt `tts-service` (`docker compose build tts-service`) and recreated the container (`docker compose up -d --force-recreate tts-service`).
- Immediately after restart, `tts-service` logs show:
  - `kafka_consumer_config_effective … session_timeout_ms=15000 heartbeat_interval_ms=5000`
  - `kafka_consumer_assignment_acquired` about ~9–10s after service start
  - `Published AudioSynthesisEvent` about ~11–12s after service start
- The cold-start smoke test run that was triggered immediately after restart completed in ~13s (plus ~10s container restart time).

Interpretation:
- This is consistent with the hypothesis in Analysis 028: the dominant tail component is **time-to-assignment / group recovery**, not synthesis compute.
- It also upgrades the “tuning helps” claim from inference to **Proven** for `tts-service` in this environment.

### F4 (Proven): VAD/ASR/Translation containers are also stale (Plan 028 changes not yet validated there)
Evidence:
- `speech-vad-service`, `speech-asr-service`, and `speech-translation-service` containers currently lack the new Plan 028 settings fields (e.g., `consumer_session_timeout_ms`).

Impact:
- Cross-service standardization (a core Plan 028 deliverable) is not yet validated end-to-end in the running Compose environment.

## Remaining Gaps
| # | Unknown | Blocker | Required Action | Owner |
|---|---------|---------|-----------------|-------|
| 1 | Do VAD/ASR/Translation show the same tail reduction after applying Plan 028 tuning? | Those containers are still running older images. | Rebuild/recreate each service image, then repeat the same “restart → publish → first output/first consume” measurement and capture the required logs. | Analyst / QA |
| 2 | What is the exact distribution of restart tail (p50/p95) after tuning? | Only a small number of manual trials executed; tool execution time limits constrain long runs. | Run a bounded loop (e.g., 10 iterations) and record assignment + publish deltas; store results in an evidence artifact. | QA |
| 3 | Does graceful stop vs ungraceful kill materially change the recovery time? | Mixed stop semantics observed during experimentation. | Run paired trials: `docker compose restart` vs `docker kill + up -d`, compare assignment acquired delta. | Analyst |
| 4 | Baseline evidence artifact is incomplete. | `agent-output/analysis/028-kafka-consumer-group-recovery-baseline.md` is still a placeholder. | Populate with concrete timestamps, effective tuning values, and measured deltas (allowlisted). | QA |

## Instrumentation Notes
For `tts-service` (rebuilt), the Plan 028 always-on telemetry events were observed in logs:
- `kafka_consumer_config_effective`
- `kafka_consumer_assignment_acquired`
- `kafka_consumer_first_input_received`

For the other services, the same events cannot be relied upon until their images are rebuilt to include Plan 028.

## Analysis Recommendations (evidence-only)
1) Rebuild/recreate `vad-service`, `asr-service`, and `translation-service` images and repeat the same restart experiment used here.
2) Populate the evidence placeholder `agent-output/analysis/028-kafka-consumer-group-recovery-baseline.md` with:
   - effective tuning snapshot (allowlisted)
   - restart timestamp, assignment acquired timestamp, first input received timestamp, first output published timestamp
3) Capture Kafka consumer group state (`kafka-consumer-groups --describe`) during at least one cold-start run to tie timing to group membership state.
