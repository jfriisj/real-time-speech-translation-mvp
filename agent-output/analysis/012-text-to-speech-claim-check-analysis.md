# Analysis 012: TTS Claim Check Integration Readiness

**Plan Reference (if any)**: agent-output/planning/010-text-to-speech-plan.md
**Status**: Draft

## Value Statement and Business Objective
As a User, I want the TTS service to finish the speech-to-speech loop without blowing up the event bus, so the implementation must offload large audio payloads to object storage while keeping inline delivery and observability intact.

## Changelog
| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | Planner → Analyst | TTS plan readiness | Confirm the MinIO/Claim Check plumbing, inline-vs-URI toggles, and observability hooks required to lock in Plan 010 Rev 32.

## Objective
Answer the following readiness questions so the planner can close the remaining technical gaps:
1. What pieces of MinIO/Claim Check infrastructure already exist, and can they be relied on when payloads exceed 1.25 MiB? _Success_: cite the compose services/`ObjectStorage` helpers that create `tts-audio` and enforce the 24 h lifecycle.
2. How does the service decide between inline audio and a URI while covering the `DISABLE_STORAGE`, `FORCE_AUDIO_URI`, and `TTS_AUDIO_URI_MODE` toggles? _Success_: list the env vars/defaults and show where the logic lives (`select_audio_transport`).
3. What telemetry or tests produce `synthesis_latency_ms`, `rtf`, and inline/URI proof points so QA can validate the Claim Check path? _Success_: point to the log statement and smoke test that re-fetches MinIO payloads.

## Context
- Relevant modules/files: services/tts/src/tts_service/main.py, config.py, processing.py, tests (test_processing, tts_pipeline_smoke), shared/speech-lib storage/events/producer, docker-compose.yml (minio/minio-init), services/tts/minio-lifecycle.json.
- Known constraints: Inline payloads are capped at `AUDIO_PAYLOAD_MAX_BYTES` (1.25 MiB) and `AudioSynthesisPayload` enforces XOR semantics; large blobs must either be dropped or uploaded to MinIO with a 24 h TTL; presigned URLs must not be logged.

## Methodology
- Reviewed Plan 010 (Rev 32) to understand the updated Claim Check scope and requirements.
- Inspected `services/tts` source (config, main loop, processing) plus shared helpers (`ObjectStorage`, `AudioSynthesisPayload`, `KafkaProducerWrapper`) to uncover the exact gating logic and limits.
- Examined `docker-compose.yml`, `services/tts/minio-lifecycle.json`, and the TTS tests (`test_processing.py`, `tests/e2e/tts_pipeline_smoke.py`) to verify the MinIO bootstrap, lifecycle policy, and QA harness.
- Used `rg`/code browsing to confirm the `AUDIO_PAYLOAD_MAX_BYTES` constant and `compute_rtf` instrumentation.

## Findings
### Facts
1. `shared/speech-lib/src/speech_lib/constants.py` sets `AUDIO_PAYLOAD_MAX_BYTES = int(1.25 * 1024 * 1024)` and `KafkaProducerWrapper` additionally guards against `KAFKA_MESSAGE_MAX_BYTES = 2 * 1024 * 1024`, so the inline cap matches Plan 010.
2. `select_audio_transport` in `services/tts/src/tts_service/processing.py` enforces the inline limit, respects `DISABLE_STORAGE`, fails fast when storage is missing, and respects `FORCE_AUDIO_URI` plus `TTS_AUDIO_URI_MODE` (internal keys vs presigned URLs) while bubbling up `mode` for logging.
3. `ObjectStorage` (shared library) calls `boto3` to `put_object` and optionally `generate_presigned_url`, and `docker-compose.yml` wires up `minio`/`minio-init` to create the `tts-audio` bucket and import `services/tts/minio-lifecycle.json`, which enforces a 1-day expiration rule.
4. `services/tts/src/tts_service/main.py` logs `audio_size_bytes`, `transport_mode`, `synthesis_latency_ms`, and formatted `rtf`, while `compute_rtf` calculates ratio from duration/latency; `tests/e2e/tts_pipeline_smoke.py` publishes phrases, waits for `AudioSynthesisEvent`, and re-fetches URI payloads (via the same `ObjectStorage` helpers) to prove the Claim Check path.
5. `services/tts/tests/test_processing.py` exercises `select_audio_transport`, ensuring inline mode stays inline, storageless drop raises `ValueError`, and URI mode uploads via the `DummyStorage` stub and returns the expected `tts/{correlation_id}.wav` key.

### Hypotheses
1. The planner should explicitly document `TTS_AUDIO_URI_MODE` (`internal` for internal keys vs other values for presigned URLs) so Gateway-like consumers know when to presign keys and when to treat the value as an already-resolved URL.
2. The `DISABLE_STORAGE` flag is already wired into `SelectAudioTransport`; the plan should call out the log-and-drop behavior and tie it to the `FORCE_AUDIO_URI` test switch so QA can quickly exercise the Claim Check fallback when storage is unavailable.
3. Because `docker-compose` creates `tts-audio` (via `minio-init` and `mc ilm import`), the plan should mention the retention policy (24 h TTL) so stakeholders know cleanup is automatic and where to look if MinIO hits storage limits.

## Recommendations
1. Expand Plan 010’s configuration section to enumerate the relevant env vars (`INLINE_PAYLOAD_MAX_BYTES`, `DISABLE_STORAGE`, `FORCE_AUDIO_URI`, `TTS_AUDIO_URI_MODE`, `MINIO_*`, etc.), their defaults, and how they influence inline vs URI paths so implementers do not guess at behavior.
2. Call out the MinIO bootstrap/claim-check lifecycle (compose services + `minio-init` script) so the plan makes it clear that `tts-audio` already exists with a 24‑hour expiration, eliminating the need for manual bucket creation.
3. Highlight the QA/observability hooks: the `producer.publish_event` log around `transport_mode`, `synthesis_latency_ms`, and `rtf`, plus the `tests/e2e/tts_pipeline_smoke.py` harness that re-fetches audio via MinIO, can serve as the plan’s acceptance criteria for Claim Check telemetry.

## Open Questions
1. Should the plan explicitly mandate that `audio_uri` remains an internal key (the `internal` mode) and that the Gateway is responsible for presigning, or is emitting a presigned URL directly acceptable with the same logging guardrails?
2. Do we need a QA/operational checklist that forcibly toggles `FORCE_AUDIO_URI` (or sets `INLINE_PAYLOAD_MAX_BYTES` low) so every release cycle verifies the drop/URI path when MinIO is down? 
3. Given the plan now tightly couples payload size to Claim Check, should we document how to handle longer texts when `DISABLE_STORAGE` is true (e.g., fail loudly with a `ValueError` log and ensure there is monitoring on that log message)?

## Handoff

## Handoff to Planner/Architect
**From**: Analyst
**Artifact**: agent-output/analysis/012-text-to-speech-claim-check-analysis.md
**Status**: Draft
**Key Context**:
- Claim Check infrastructure already exists (MinIO + lifecycle + storage helper) and the service enforces inline caps while logging latency/`rtf` for QA.
- Inline vs URI logic uses `DISABLE_STORAGE`, `FORCE_AUDIO_URI`, and `TTS_AUDIO_URI_MODE`, so the plan should document these knobs instead of leaving them implicit.
**Recommended Action**: Update Plan 010 to spell out the configuration and infrastructure assumptions above, tie QA acceptance to the existing smoke test, and clarify storage fallback expectations before handing the plan to implementers.