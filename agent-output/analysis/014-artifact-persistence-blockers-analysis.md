# Analysis 014: Artifact Persistence Blockers — Deeper Claim Check Unknowns

**Plan Reference (if any)**: agent-output/planning/010-text-to-speech-plan.md
**Status**: Draft

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | Quest for clarity | Continue artifact-persistence research | Dug deeper into the storage helper, TTS processing loop, and MinIO lifecycle to expose contradictions and blockers before locking in Epic 1.8.

## Objective

Answer the follow-up questions and contradictions identified after analysis 013 so that Epic 1.8 planning can proceed.

New questions / contradictions to resolve:
1. The shared `ObjectStorage.upload_bytes` helper returns a presigned URL by default, but the architecture now forbids bearer URLs in events—how do we guarantee internal references instead? (Plan 010 assumes `TTS_AUDIO_URI_MODE=internal` yet there is no enforcement.)
2. The plan’s “log-and-drop large payloads when storage is down” assumption maps to a raised `ValueError`, but we need to confirm what signal (log vs. error event) planning requires and ensure the rest of the pipeline treats it as a controlled drop.
3. MinIO lifecycle is applied via `services/tts/minio-lifecycle.json`, but nobody currently owns verifying the bucket/key naming, TTL configuration, or cleanup proof—who is the owner of these lifecycle guardrails before Epic 1.8 expands persistence?

Stop condition: Planning can proceed once the above contradictions are resolved and documented such that (a) Claim Check references are guaranteed to be internal non-secret identifiers, (b) storage failure and oversize behavior is deterministic and observable, and (c) lifecycle/naming ownership is pinned down for the pilot with evidence of TTL compliance.

## Context

- Relevant modules/files: agent-output/planning/010-text-to-speech-plan.md (Claim Check assumptions, env var contract), services/tts/src/tts_service/main.py (processing loop, failure handling), services/tts/src/tts_service/processing.py (transport selection), shared/speech-lib/src/speech_lib/storage.py (`ObjectStorage` helper), services/tts/minio-lifecycle.json (TTL policy), agent-output/architecture/system-architecture.md (Claim Check guardrails), and the newly created agent-output/architecture/022-artifact-persistence-rollout-architecture-findings.md.
- Known constraints: Kafka message cap (1.5 MiB), Claim Check for payloads > 1.25 MiB, retention target 24h, non-logging of presigned URLs, ability to operate with storage disabled.

## Methodology

- Re-read Plan 010 to enumerate assumptions around storage, including `audio_uri_mode`, `DISABLE_STORAGE` fallbacks, and lifecycle ownership commitments.
- Studied `services/tts/src/tts_service/processing.py` and `main.py` to understand how the helper is used, how failure surfaces, and whether the outer loop implements the log-and-drop behavior assumed by the plan.
- Examined `shared/speech-lib/src/speech_lib/storage.py` to see what the helper returns by default and how it could be configured to emit internal keys.
- Checked `services/tts/minio-lifecycle.json` to confirm retention settings and noted that no service currently validates or reports on lifecycle/lifeline compliance.
- Cross-referenced architecture guardrails (system-architecture.md) and the new Findings 022 to identify contradictions.

## Findings

### Facts
- `ObjectStorage.upload_bytes` calls `generate_presigned_url` by default and only returns a bucket/key when `return_key=True`; Plan 010 currently only mentions emitting `tts/{correlation_id}.wav` (implying the internal key path) without explaining the `return_key` toggle (shared/speech-lib/src/speech_lib/storage.py).
- `select_audio_transport` uses `return_key=audio_uri_mode == "internal"`; `audio_uri_mode` defaults to `internal` per plan, so the current implementation strips the `s3://` prefix to publish only the key, but this relies on the caller never flipping the mode, and no enforcement exists (services/tts/src/tts_service/processing.py#L55-L87).
- The consumer loop in `services/tts/src/tts_service/main.py` catches `ValueError`, logs a warning, and continues, effectively implementing the planned “log-and-drop” semantics, but there is no upstream observable signal (metrics, error event, DLQ) beyond the log entry (main.py#L88-L132).
- The `minio-lifecycle.json` file in `services/tts` enforces a 24-hour expiration rule on all keys in `tts-audio`, but nothing in the plan or architecture states who owns verification or raises alarms when artifacts overstay or naming policy diverges (services/tts/minio-lifecycle.json).

### Contradictions / Blockers
- **Presigned URL vs internal key**: The helper’s default is to emit bearer URLs unless the caller explicitly asks for a key. Architecture now forbids embedding such URLs in events, but the shared helper still surfaces them by default. Without either a default change or a distributed enforcement policy, other services introduced in Epic 1.8 may inadvertently publish presigned URLs.
- **`audio_uri_mode` drift risk**: Even though the plan sets `TTS_AUDIO_URI_MODE=internal`, there is no safeguard preventing operators or future services from setting `audio_uri_mode` to `presigned`. That would violate the guardrail, and even TTS currently has no validation or warning when `audio_uri_mode` is misconfigured.
- **Log-only failure signal**: “Log-and-drop” is implemented, but the broader pipeline or QA harness has no way to detect recurring droppages beyond scanning logs; planning may require an explicit error event/metric to surface Claim Check failures (esp. since the architecture aims for measurable observability per Epic 1.8). The failure pathways must be documented (e.g., metric name, log template) so QA can assert compliance.
- **Lifecycle ownership gap**: While MinIO enforces TTL via lifecycle policy, it is unclear whether the pilot (TTS service) or platform (operations) is expected to own the bucket/key naming strategy and to document evidence of TTL enforcement. Without a named owner, Epic 1.8 rollout may duplicate TTL logic or leave gaps when other services write to the bucket.

## Recommendations
- Update `speech_lib.storage.ObjectStorage` (or wrap it) so that the default Claim Check path exposes only bucket/key references; expose an explicit `presigned` path for the Gateway or other edge components. Document this change and ensure all consumers know which variant to call.
- Guard `TTS_AUDIO_URI_MODE` by validating the value at startup and warning (or failing) if it is set to anything other than `internal` for the pilot release; optionally, add an integration test to ensure internal-only behavior.
- Define the observable signal for storage failures (metric, structured log, event) so QA and monitoring know when Claim Check writes drop; include the log template (already in main.py) in the plan’s acceptance criteria if that log is the canonical indicator.
- Assign an owner (TTS or platform ops) for the object lifecycle policy, including documenting the naming scheme (`tts/{correlation_id}/{stage}.wav`?), TTL proof (MinIO lifecycle), and verification steps; add this to plan acceptance criteria so Epic 1.8 can rely on the same guardrails.

## Open Questions

1. Should `ObjectStorage` default to returning a non-secret bucket+key, or should services wrap it to enforce that policy? (Without a default change, Epic 1.8 must coordinate across services to avoid accidental presigned URLs.)
2. Do we need a structured signal (metric/event) beyond the `LOGGER.warning` in `main.py` for oversized payload drops, or is log scanning sufficient for this pilot? If a metric is required, who emits it?
3. Who owns the naming/TTL lifecycle guardrails for the bucket as more services start writing artifacts? Is it the TTS pilot, a platform team, or an explicit plan artifact that Epic 1.8 inherits?

## Stop Condition

Planning can proceed when: (1) the Claim Check helper’s output is guaranteed to be a non-secret reference (and presigning is explicitly delegated to the edge), (2) storage failure/oversize behavior has a deterministic and observable signal (log, metric, or event) so QA can assert it, and (3) ownership/lifecycle expectations (naming, TTL, cleanup proof) are documented for the pilot so Epic 1.8 can reuse them without duplicating logic.

## Handoff

## Handoff to Planner/Architect

**From**: Analyst
**Artifact**: agent-output/analysis/014-artifact-persistence-blockers-analysis.md
**Status**: Draft
**Key Context**:
- Deepened the Claim Check investigation by aligning helper defaults, failure signaling, and lifecycle ownership with the architecture guardrails.
**Recommended Action**: Resolve the contradictions/questions listed above so Epic 1.8 planning has a precise, enforceable contract for artifact persistence.
