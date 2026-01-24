# Plan 009: Voice Activity Detection (VAD) Service

**Plan ID**: 009
**Target Release**: v0.4.0
**Epic Alignment**: Epic 1.6 Voice Activity Detection (VAD) Service
**Process Improvement**: Includes scaffolded QA artifact stub (PI-003).
**Status**: Revised (Measurement Method Clarified)

## Changelog

| Date | Event | Summary |
|------|-------|---------|
| 2026-01-19 | Initial approval | Plan approved by Critic after Architecture Findings 009 validation |
| 2026-01-19 | QA hardening revision | Testing Strategy and Acceptance Criteria expanded per Architecture Findings 010 (integration points & failure modes) |
| 2026-01-19 | Measurement clarification | Added Success Metric Measurement Method section per Critique Finding 8 (methodology underspecified) |

## Value Statement and Business Objective
As a System Architect, I want to filter out silence *before* the heavy ASR service, so that I don't waste GPU/CPU cycles transcribing background noise and latency is improved.

**Measure of Success**:
- Reduction in total audio duration processed by ASR (≥ 30% reduction on "sparse speech" test set).
- Latency P50 unchanged or improved (VAD overhead < ASR savings).

### Success Metric Measurement Method

**Duration Computation**:
- Audio duration is computed from WAV file headers (`num_samples / sample_rate_hz`).
- "Duration processed by ASR" = sum of all segment durations emitted by VAD for a given request.
- Baseline (Pipeline A) = full original audio duration.
- VAD Mode (Pipeline B) = sum of `(end_ms - start_ms)` across all `SpeechSegmentEvent` for the same `correlation_id`.

**Dataset Definition ("Sparse Speech")**:
- A representative test set of audio files containing:
  - ≥ 40% silence or non-speech (background noise, pauses).
  - At least 10 distinct audio samples.
  - Total duration ≥ 5 minutes across all samples.
- Sources: synthetic test audio (see [tests/smoke_infra.py pattern](tests/smoke_infra.py)) or curated samples from open datasets (e.g., LibriSpeech with added silence padding).

**Transcript Quality Guardrail**:
- Transcript Word Error Rate (WER) MUST NOT increase by more than 5 percentage points (pp) compared to the baseline (Pipeline A).
- Qualitative validation: manually review transcripts for at least 3 samples to confirm no critical content is dropped (e.g., sentence fragments, missing keywords).
- If WER degrades beyond the 5pp threshold, VAD configuration (threshold, padding) must be tuned before declaring success.

**Sample Size**:
- Minimum N=10 samples for initial validation.
- Recommended N=50 for thesis-grade evidence (if time permits).

## Objective
Implement a dedicated Voice Activity Detection (VAD) microservice using `onnx-community/silero-vad` to segment audio streams. This service effectively acts as a filter, consuming raw audio ingress and producing only speech segments for downstream ASR, reducing computational load and standardizing inputs.

## Context
- **Architecture**: Validated in [Architecture Findings 009](agent-output/architecture/009-voice-activity-detection-architecture-findings.md).
- **QA Integration Points**: Detailed in [Architecture Findings 010](agent-output/architecture/010-vad-qa-integration-points-architecture-findings.md).
- **Roadmap**: Epic 1.6 in release v0.4.0.
- **Dependencies**: Uses `AudioInputEvent` (existing) and requires defining `SpeechSegmentEvent`.
- **Preceded by**: Epic 1.5 (Ingress Gateway) - VAD consumes the gateway's output.

## Assumptions
- `silero-vad` (ONNX) is suitable for CPU-only execution in the docker container.
- Latency overhead of VAD inference is less than the gain from skipping silence processing in ASR.
- Kafka ordering by key (`correlation_id`) is sufficient to maintain segment order.

## Constraints (Architecture Findings 009)
- **Topic Taxonomy (Strict)**:
    - Input: `speech.audio.ingress` (consumes `AudioInputEvent`)
    - Output: `speech.audio.speech_segment` (produces `SpeechSegmentEvent`)
- **Event Semantics**:
    - `SpeechSegmentEvent` must be **self-contained** (full audio segment inline).
    - Must preserve `correlation_id`.
    - Must include `start_ms`, `end_ms`, and `segment_index`.
- **Ordering**: Output events MUST be keyed by `correlation_id` to ensure partition locality and ordering.
- **Backward Compatibility**: ASR must support *both* `AudioInputEvent` and `SpeechSegmentEvent` (via configuration or dual-subscribe) to preserve the v0.2.x benchmark baseline.
- **Audio Format**: Invariant `wav` only. Non-wav inputs are logged and dropped.
- **Configuration**: VAD thresholds (silence trigger, min speech duration) must be runtime configurable (env vars), not hardcoded.

## Plan Steps

### 1. Shared Infrastructure & Contract Updates
**Objective**: Define the new event schema and topic.
- [ ] Create `SpeechSegmentEvent` Avro schema in `shared/schemas/avro/`.
    - **Note**: Align field names with `AudioInputEvent` conventions.
    - Fields:
        - `correlation_id` (string)
        - `segment_id` (string) *[New architectural requirement]*
        - `segment_index` (int)
        - `start_ms` (long)
        - `end_ms` (long)
        - `audio_bytes` (bytes) *[renamed from audio_payload]*
        - `sample_rate_hz` (int) *[renamed from sample_rate]*
        - `audio_format` (string, doc="wav") *[New architectural requirement]*
- [ ] Update `speech-lib`:
    - Generate Python class for `SpeechSegmentEvent`.
    - Register new schema with Schema Registry during initialization.
    - Add `speech.audio.speech_segment` subject configuration.

### 2. VAD Service Implementation
**Objective**: Create the silence-filtering microservice.
- [ ] Create `services/vad/` module structure (Dockerfile, pyproject.toml, src).
- [ ] Implement Consumer for `speech.audio.ingress` (`AudioInputEvent`).
- [ ] Integrate `onnx-community/silero-vad` (via `onnxruntime`).
    - **Note**: Ensure model is downloaded/cached during build or volume-mounted to avoid runtime fetch failures.
- [ ] Implement Segmentation Logic:
    - Buffer audio (if needed by model window).
    - Detect speech segments.
    - Slice audio bytes.
- [ ] Implement Producer for `speech.audio.speech_segment` (`SpeechSegmentEvent`).
    - **CRITICAL**: Set Kafka message key = `correlation_id`.
- [ ] Add configuration management (thresholds, window sizes).

### 3. ASR Service Migration (Dual-Mode)
**Objective**: Enable ASR to consume segments without breaking legacy support.
- [ ] Refactor ASR `main.py` consumer loop.
- [ ] Introduce configuration `ASR_INPUT_TOPIC`.
    - Default/Legacy: `speech.audio.ingress`
    - VAD-Mode: `speech.audio.speech_segment`
- [ ] Update ASR business logic to handle `SpeechSegmentEvent` payload.
- [ ] Create [UAT Artifact Stub](agent-output/uat/009-voice-activity-detection-uat.md) (PI-003 Requirement).
    - **Note**: The core `transcribe` function likely takes bytes; ensure both event types unpack to the same internal byte structure.
    - **Note**: Logging should now include `segment_index` if present.

### 4. Integration & Deployment
**Objective**: Wire it up in Docker Compose.
- [ ] Update `docker-compose.yml`:
    - Add `vad` service.
    - Determine ASR configuration (keep as strict dependency or allow toggle). *Decision: For this Epic, default ASR to consume VAD output to verify the feature, but enable fallback via ENV.*
- [ ] Create [QA Artifact Stub](agent-output/qa/009-voice-activity-detection-qa.md) (PI-003 Requirement).

### 5. Version Management
- [ ] Update `agent-output/releases/v0.4.0.md` (create if missing) to track inclusion of Epic 1.6.

## Testing Strategy
*Updated per Architecture Findings 010 (QA integration points & failure modes)*

- **Unit Tests**:
    - Test VAD logic with synthetic silence/speech wav files.
    - Verify schema serialization/deserialization.
    - Test edge cases: all-silence input (zero segments), very short speech, speech at start/end boundaries.
- **Integration Tests**:
    - **Pipeline B Smoke Test**: Ingress -> VAD -> ASR -> Translation.
        - Verify `speech.audio.speech_segment` topic contains expected events.
        - Verify ASR successfully transcribes segments.
    - **Ordering Verification**: Send multi-segment audio, verify segments arrive at ASR in `segment_index` order.
    - **Schema Registry Validation**:
        - Cold-start stack; assert all required subjects exist (`speech.audio.ingress-value`, `speech.audio.speech_segment-value`, `speech.asr.text-value`, `speech.translation.text-value`).
        - Verify TopicNameStrategy naming convention.
    - **Correlation Propagation**: Assert `correlation_id` identical across segment(s), ASR output, translation output.
    - **At-Least-Once Semantics**:
        - Test duplicate event delivery tolerance (simulate consumer restart mid-stream).
        - Verify system remains stable and traceable via `correlation_id` + `segment_index`.
- **Failure Mode Tests** (Architecture Findings 010 requirements):
    - **Non-WAV Input**: Publish `audio_format != "wav"`; verify VAD logs + drops without crash.
    - **Poison Message**: Publish corrupt WAV bytes; verify VAD logs + drops and continues consuming.
    - **Oversize Payload**: Test near payload cap boundary; verify consistent drop behavior.
    - **Backpressure**: Burst multiple concurrent requests; verify services remain healthy and latency stable.
- **Regression**:
    - **Pipeline A (Legacy)**: Run ASR consuming `speech.audio.ingress` directly; verify no breakage from dual-mode implementation.

## Validation (Acceptance Criteria)
*Updated per Architecture Findings 010 (critical boundary validation)*

- [ ] VAD service running in Docker.
- [ ] **Schema Registry Integration**: All required subjects registered and queryable (`speech.audio.speech_segment-value` using TopicNameStrategy).
- [ ] **Pipeline B (VAD mode)**: Input raw audio → VAD emits segments → ASR transcribes → Translation produces output.
- [ ] **Pipeline A (Legacy regression)**: ASR consuming `speech.audio.ingress` directly still works.
- [ ] **Segmentation correctness**: Input with 5s silence + 5s speech produces `SpeechSegmentEvent` ONLY for speech segment.
- [ ] **Correlation propagation**: `correlation_id` matches across segment(s), ASR output, translation output.
- [ ] **Ordering guarantee**: Multi-segment input produces monotonic `segment_index` at ASR input for same `correlation_id`.
- [ ] **Failure resilience**: Non-wav input logged + dropped without crash; poison message logged + dropped; consumer continues.
- [ ] **Duplicate tolerance**: System remains stable under at-least-once delivery (e.g., consumer restart mid-stream).
- [ ] **Backpressure handling**: Burst test with multiple concurrent requests completes without crashes or memory leaks.
- [ ] **Observability**: VAD logs segment count, offsets, and `correlation_id` for each request; ASR logs which input topic it consumes at startup.
- [ ] **Success Metric Check**: Verify audio duration reduction on sparse-speech test set meets ≥ 30% target.

## Risks
- **ASR Complexity**: Handling two input types might clutter ASR code. *Mitigation: Adapter pattern at the consumer edge.*
- **Model Download**: Silero VAD download might fail in restricted environments. *Mitigation: Bake into image or use local cache.*
- **Fragmented Context**: Cutting audio too aggressively might chop words. *Mitigation: Configurable padding (pre/post speech silence).*
- **Segment Reordering** (Architecture Findings 010): Wrong message key or multi-partition distribution could break ordering. *Mitigation: CRITICAL requirement enforced—VAD MUST key by `correlation_id`.*
- **Schema Registry Outage**: Runtime SR unavailability could block event production/consumption. *Mitigation: Services must fail fast with clear logs; tested explicitly in failure mode suite.*
- **Poison Message Loop**: Corrupt audio payload could cause crash-loop. *Mitigation: "Log + drop" policy enforced; validated via poison message test.*

