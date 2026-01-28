# Analysis 015: Plan 022 Research Gaps — Audio Metadata, Metrics, and Thresholds

**Plan Reference**: agent-output/planning/022-artifact-persistence-rollout-plan.md
**Status**: Complete

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | Planner/Implementer | Identify research gaps in Plan 022 | Investigated existing audio contracts, shared lib constants, observables, and lifecycle configurations to resolve open questions from Critique Rev 3. |

## Objective

Close the remaining research gaps identified in Critique Rev 3 so Plan 022 can be implemented without ambiguity:
1. **Metadata**: What audio determinism metadata (format, sample rate, etc.) is currently available/required for `*_uri` payloads across VAD and TTS?
2. **Thresholds**: Reconcile the 1.25 MiB plan threshold vs the 1.5 MiB architecture cap.
3. **Observability**: Identify existing counters/logs or define new ones to make the success metric (`claim_check_uri_total / total`) measurable.
4. **Lifecycle**: Confirm current MinIO bucket coverage vs future requirements.

## Context

- **Schemas**: `AudioInputEvent`, `SpeechSegmentEvent`, and `AudioSynthesisEvent` all carry `payload.audio_format` (string) and `payload.sample_rate_hz` (int). `AudioSynthesisEvent` also has `content_type`.
- **Constants**: `AUDIO_PAYLOAD_MAX_BYTES` is defined as `1.25 * 1024 * 1024` (1.25 MiB) in `shared/speech-lib/constants.py`.
- **Architecture**: `system-architecture.md` mentions a "1.5 MiB inline payload hard cap" but the shared lib enforces 1.25 MiB.
- **Observability**: `services/tts/main.py` logs `audio_size_bytes` and `transport_mode` ("inline" vs "uri") but does not emit Prometheus metrics (counters). It relies on structured logs.

## Findings

### Facts

1.  **Audio Metadata Exists**: All relevant schemas (`AudioInputEvent`, `SpeechSegmentEvent`, `AudioSynthesisEvent`) *already* contain `audio_format` and `sample_rate_hz` fields. `AudioSynthesisEvent` explicitly adds `content_type`.
    *   *Gap*: `AudioInputEvent` and `SpeechSegmentEvent` schemas do not strictly require `content_type` yet, but they have format/rate fields.
    *   *Resolution*: Plan should mandate verifying/populating these existing fields when using `*_uri`.

2.  **Threshold Discrepancy**:
    *   Shared Lib `AUDIO_PAYLOAD_MAX_BYTES` = 1,310,720 bytes (1.25 MiB).
    *   System Architecture = 1.5 MiB (1,572,864 bytes).
    *   *Resolution*: Stick to 1.25 MiB as the safe application-level limit (leaving 250KB headroom for headers/envelope overhead within the 1.5 MiB hard cap). Plan should reference `AUDIO_PAYLOAD_MAX_BYTES` constant.

3.  **Observability Gaps**:
    *   Current TTS pilot logs `transport_mode=uri|inline`. This allows log-based counting but isn't a direct metric.
    *   Current TTS pilot logs "Dropping event..." on failure but doesn't have a dedicated `claim_check_failures_total` counter.
    *   *Resolution*: Plan is correct to demand explicit log/metric standardization. Log parsing is the current MVP measurement method; dedicated metrics are an upgrade.

4.  **Lifecycle Coverage**:
    *   Current: `minio-init` setup in `docker-compose.yml` only creates `tts-audio` and applies `services/tts/minio-lifecycle.json`.
    *   Required: `audio-ingress`, `vad-segments`, `asr-transcripts`.
    *   *Resolution*: `minio-init` entrypoint script needs update to create the loop of buckets. `minio-lifecycle.json` needs to be generalized or copied.

### Hypotheses
- Generalizing `minio-lifecycle.json` to a single platform-wide policy file applied to all buckets is cleaner than per-service files.

## Recommendations

1.  **Plan Update (Metadata)**: Explicitly require that producer services populate existing `audio_format` and `sample_rate_hz` fields when using `*_uri`. For schemas lacking `content_type` (Input/Segment), standardize on `audio/wav` for MVP or add the field if schema evolution permits (Plan 022 says additive evolution is ok). *Constraint: Do not break compatibility.*

2.  **Plan Update (Threshold)**: Explicitly cite `shared.constants.AUDIO_PAYLOAD_MAX_BYTES` (1.25 MiB) as the source of truth, noting it provides headroom against the 1.5 MiB architecture hard cap.

3.  **Plan Update (Observability)**: Clarify that "Measurement Method" relies on structured logs with `transport_mode` field (or equivalent) for MVP, unless Prometheus client is being added (not in scope).

4.  **Plan Update (Lifecycle)**: Explicitly task WP2 with updating `minio-init` to iterate over a list of buckets (`audio-ingress`, `vad-segments`, `tts-audio`, `asr-transcripts`) and apply a single shared lifecycle policy.

## Open Questions
- None. All blockers from Critique Rev 3 are resolved by existing code or clear decisions.

## Handoff

## Handoff to Planner

**From**: Analyst
**Artifact**: agent-output/analysis/015-artifact-persistence-rollout-research-gaps.md
**Status**: Complete
**Key Context**:
- Metadata fields exist but need population enforcement.
- 1.25 MiB is the correct code constant (safe limit).
- `minio-init` needs to loop over multiple buckets.

**Recommended Action**: Update Plan 022 with these specifics.
