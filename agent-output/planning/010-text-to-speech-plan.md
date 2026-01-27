# Plan 010: Text-to-Speech (TTS) Service (Kokoro ONNX)

**ID**: 010 (Rev 31)
**Target Release**: v0.5.0
**Epic**: Epic 1.7 (TTS)
**Status**: Approved
**Plan Owner**: Planner Agent
**Date**: 2026-01-27
**Analysis Ref**: agent-output/analysis/010-text-to-speech-plan-analysis.md, agent-output/analysis/011-claim-check-unknowns-analysis.md
**Architecture Ref**: agent-output/architecture/019-text-to-speech-plan-architecture-findings.md, agent-output/architecture/020-claim-check-scope-shift-architecture-findings.md

## Value Statement and Business Objective
As a User, I want to hear the translated text spoken naturally, So that I can consume the translation hands-free.

**Strategic Constraint**: The service must use **Kokoro-82M (ONNX)** to ensure reliable CPU/GPU runtime stability and Thesis reproducibility without massive hardware dependencies. Output must support large phrases by implementing the **Claim Check** pattern (URI transport) to avoid clogging the event bus.

## Test Infrastructure & Tooling Requirements
**Objective**: Ensure the service is verifiable in isolation and within the event pipeline.

*   **Unit Testing Framework**: `pytest` with `pytest-cov`.
    *   **Configuration**: `pytest.ini` correctly targeting `services/tts/tests`.
    *   **Fixtures**: Mock ONNX runtime session, Mock Kafka Consumer/Producer.
*   **Integration Testing Infrastructure**:
    *   **Docker Compose**: A dedicated test composition (`docker-compose.test.yml` or profile) that spins up:
        *   Zookeeper & Kafka
        *   Schema Registry
        *   MinIO (S3 compatible storage)
        *   TTS Service (Build from source)
    *   **Validation Script**: `tests/e2e/tts_pipeline_smoke.py` configured to connect to the test infrastructure.
*   **Dependencies**:
    *   `pytest`, `pytest-asyncio`, `pytest-cov`, `testcontainers` (optional, for advanced orchestration), `boto3` (for S3 verification).

## Scope
- Create `tts` service module.
- Implement `AudioSynthesisEvent` Avro schema with inline-OR-URI payload support.
- Implement `SynthesizerFactory` pattern to decouple service logic from the Kokoro ONNX model.
- Integrate `onnx-community/Kokoro-82M-v1.0-ONNX` using `onnxruntime` (CPU default).
- Implement explicit tokenization (phonemization) using `phonemizer` (backed by `espeak-ng`) as required by Kokoro.
- Consume `TextTranslatedEvent` -> Produce `AudioSynthesisEvent`.
- **Verification**: Verify audibility, measure RTF (Real-Time Factor), and validate payload transport.
- **Evidence Collection**:
  - QA Script: `tests/e2e/tts_pipeline_smoke.py` (or equivalent) MUST emit test phrases.
  - Evidence Artifacts: Capture logs showing `synthesis_latency_ms` and `rtf`, save to `report-output/qa-evidence/`.

## Assumptions
- `speech-lib.storage.ObjectStorage` is available but OPTIONAL for v0.5.0; service must run without it (inline-only).
- ONNX Runtime and Tokenizers libraries are compatible with the base python image.
- `espeak-ng` system dependency is available in the runtime environment (required by `phonemizer`).
- 500 characters is a reasonable initial hard cap for input text (approx 30s audio).
- Inline Payload Duration Guideline (24kHz, 16-bit Mono = 48,000 bytes/sec):
  - 1 sec ≈ 48,000 bytes (0.046 MiB).
  - 1.25 MiB cap ≈ 27.3 seconds of audio.
  - Payloads exceeding ~27s (or > 1.25MiB) will trigger the Claim Check path or warning.
  - **Storage Fallback**: If `DISABLE_STORAGE=true` is set (or MinIO unavailable), payloads > 1.25 MiB will be DROPPED with a specific warning log (Log-and-Drop policy) to prevent service crash. Small payloads continue to be served inline.
- **Key Ownership & Lifecycle**:
  - TTS owns the creation of keys using a canonical format: `tts/{correlation_id}.wav`.
  - Retention is managed by MinIO bucket configuration (lifecycle policy), not by the service code. Target: 24h retention.

## Contract Decisions

### Schema Contract
- **Producer**: `tts` service.
- **Consumer**: `gateway` (pass-through) -> Web Client (final consumer).
- **Source of Truth**: `shared/schemas/avro/AudioSynthesisEvent.avsc`
- **Critical Fields**:
  - `audio_bytes`: `bytes` (nullable) - Inline audio data (typically WAV).
  - `audio_uri`: `string` (nullable) - Internal object key (e.g., `tts/<uuid>.wav`) for retrieval via Gateway/Pre-signer. NOT a public URL.
  - `duration_ms`: `long` - Duration of audio in milliseconds.
  - `sample_rate_hz`: `int` - Sample rate (e.g. 24000).
- **Invariant**: The `AudioSynthesisPayload` MUST contain **EXACTLY ONE** of `audio_bytes` OR `audio_uri` (XOR). Implementers must enforce this during validation.
- **Compatibility**: Additive evolution (new fields are optional/unions) subject to Registry `BACKWARD` enforcement.
- **Evolution**: New fields added as `union {null, type}` with default null.

### Kafka Bindings
- **Input Topic**: `speech.translation.text`
- **Output Topic**: `speech.tts.audio` (Pinned)
- **Schema Registry Subject**: `speech.tts.audio-value` (Strategy: `TopicNameStrategy`)

### Speaker Context Contract
- **Representation**: Service MUST propagate `speaker_reference_bytes` (or `speaker_id` URI) from input to output as pass-through metadata (even if unused by v0.5.0 Kokoro backend).
- **Origin**: `TextTranslatedEvent`.
- **Reasoning**: Ensures end-to-end context is preserved for future voice cloning backends (Epic 1.7+ / v0.6.0).

### Observability Contract
- **Trace Propagation**: Service MUST extract and propagate W3C `traceparent` from input headers to output headers.
- **Logging**:
  - MUST log `correlation_id` in every log entry.
  - MUST log `audio_size_bytes` and `transport_mode` (inline vs uri) on synthesis completion.
  - MUST log warning if `audio_size > MAX_INLINE_BYTES` and storage is disabled.
  - MUST log `synthesis_latency_ms` and computed `rtf` (Real-Time Factor).
- **Metrics**:
  - Explicit metrics (Prometheus counters) are OPTIONAL for v0.5.0; focus is on structured logging for observability.

### Data Retention & Privacy
- **Claim Check Implementation**: Adopted early in v0.5.0 (ahead of Epic 1.8 platform-wide rollout) to solve immediate Kafka payload size constraints for TTS.
- **Audio URI Lifecycle**: Managed via object store key reference and bucket lifecycle policy.
- **Retention**: Time-bounded, configurable via MinIO bucket policy (default target: 24 hours). Service does NOT implement deletion logic.
- **URI Type**: Internal object key (preferred) for intra-system transport.
  - **Preferred path**: TTS emits internal object key; Gateway (edge) generates ephemeral presigned URL at read time for the client.
- **Log Privacy**: Presigned URLs must NEVER be logged relative to `audio_uri` or any other field. Log the internal object key instead.

### Input Behavior Contract
- **Text Length**: Hard Reject (> 500 chars).
- **Behavior**: If `text` length > 500, log specific warning "Text exceeds 500 char contract" and drop event (do not crash, do not synthesize).
  - **Note**: A Dead Letter Queue (DLQ) is NOT required for v0.5.0; Log-and-Drop is the approved failure mode for MVP.

## Milestones

### M1: Schema Definition & Shared Contract
**Goal**: Define the output event structure that supports both small (inline) and large (URI) audio payloads.
**Deliverables**:
- Schema file created at `shared/schemas/avro/AudioSynthesisEvent.avsc`.
- Schema registered with Subject `speech.tts.audio-value` (Compatibility: BACKWARD).
  - Fields: `correlation_id` (required), `audio_bytes` (optional), `audio_uri` (optional), `audio_format` (default 'wav'), `content_type` (default 'audio/wav'), `sample_rate_hz`, `text_snippet`, `speaker_reference_bytes` (optional, pass-through).
- Updated `speech-lib` with generated classes.

### M2: TTS Service Scaffold & Pluggable Factory
**Goal**: Create the service structure that isolates the model dependency.
**Deliverables**:
- Service module `services/tts` with Dockerfile (GPU-ready structure).
- **Test Configuration**: `pyproject.toml` updated with `pytest` dependencies; `pytest.ini` created.
- `SynthesizerFactory` implementation decoupling logic from engine.
- Configuration for `TTS_MODEL_ENGINE` (default: "kokoro_onnx").

### M3: Kokoro ONNX Integration & Tokenization
**Goal**: Implement the concrete synthesizer using the specified model and correct text pre-processing.
**Deliverables**:
- `KokoroSynthesizer` implementation loaded via `onnxruntime`.
- Tokenizer integration using `phonemizer` with `espeak-ng` backend.
  - Runtime dependency: `apt-get install espeak-ng`.
  - Python dependency: `phonemizer`.
- Unit tests verifying pipeline with mock ONNX session.
- **GPU Readiness**: Service scaffolded to support `onnxruntime-gpu` in future (driver versions not enforced in v0.5.0).

### M4: Event Loop & Payload Management (Claim Check)
**Goal**: Connect Kafka input/output and handle payload size and storage constraints.
**Deliverables**:
- Consumer loop for `speech.translation.text`.
  - Logic to extract `speaker_reference_bytes` (pass-through).
- Payload logic implementing the **Claim Check Pattern**:
  - **Inline**: < 1.25 MiB (emit `audio_bytes`).
  - **URI**: > 1.25 MiB (upload to S3 using key `tts/{correlation_id}.wav`, emit `audio_uri` as key).
  - **Fallback**: If > 1.25 MiB and `DISABLE_STORAGE=true` (or upload fails), log "Payload too large for inline and storage disabled" and DROP.
- **Integration Test Harness**: Update `docker-compose.yml` (or create override) to support `tts` service + `minio` + `kafka` integration testing.

### M5: Version Management & Release
**Goal**: Prepare artifacts for Release v0.5.0.
**Deliverables**:
- Version bump to `0.5.0` in package files.
- CHANGELOG updated.

## Verification & Acceptance
- **Contract Verification**:
  - Verify schema registers with Schema Registry (BACKWARD mode).
  - Verify >500 char input is dropped (not crashed).
  - Verify Logs contain `correlation_id` and do NOT contain full presigned URLs.
- **Functional Verification**:
  - Send "Hello World" (with dummy speaker bytes) -> Verify valid WAV output (inline) AND `speaker_reference_bytes` present in output event.
  - Send Mock Large Text (simulated size > 1.25 MiB) with Storage -> Verify `audio_uri` (present, format `tts/...`) and `audio_bytes` (null).
  - Send Mock Large Text (simulated size > 1.25 MiB) with `DISABLE_STORAGE=true` -> Verify event dropped with explicit warning (Log-and-Drop).
- **Performance Verification**:
  - Measure RTF (Real-Time Factor) on target hardware.
  - Outcome: RTF is measured and recorded in logs.
  - **QA Evidence**: Run 5 standard test phrases (Short <5s, Medium ~15s, Long ~25s), capture logs with `rtf` field, verify `synthesis_latency_ms` < Duration.

## Risks
- **Model Download Time**: Kokoro model download might timeout on first container start.
  - *Mitigation*: Use a build-stage download or volume mount for model cache.
- **Tokenization Complexity**: Some ONNX voice models require complex phoneme mapping in Python.
  - *Mitigation*: Use `misaki` or `phonemizer` compatible with Kokoro, pinned in `requirements.txt`.

## Rollback Plan
- If Kokoro ONNX proves unstable or too slow on CPU, rollback strategy is:
  1. Revert to previous release (v0.4.0) OR disable TTS service feature flag.
  2. DO NOT switch to a non-compliant "system speech" engine for Release v0.5.0.
  3. "Mock" engine (SynthesizerFactory) is permitted ONLY for non-production demos or testing, not as a Production Fallback.
- Note: Architecture Findings 011 specifically approved Kokoro ONNX, so persistence on this path is preferred.
