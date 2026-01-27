# Plan 010: Text-to-Speech (TTS) Service (Kokoro ONNX)

**ID**: 010 (Rev 26)
**Target Release**: v0.5.0
**Epic**: Epic 1.7 (TTS)
**Status**: Approved
**Plan Owner**: Planner Agent
**Date**: 2026-01-27
**Analysis Ref**: agent-output/analysis/010-text-to-speech-plan-analysis.md
**Architecture Ref**: agent-output/architecture/017-text-to-speech-plan-architecture-findings.md

## Value Statement and Business Objective
As a User, I want to hear the translated text spoken naturally, So that I can consume the translation hands-free.

**Strategic Constraint**: The service must use **Kokoro-82M (ONNX)** to ensure reliable CPU/GPU runtime stability and Thesis reproducibility without massive hardware dependencies. Output must support large phrases by implementing the **Claim Check** pattern (URI transport) to avoid clogging the event bus.

## Scope
- Create `tts` service module.
- Implement `AudioSynthesisEvent` Avro schema with inline-OR-URI payload support.
- Implement `SynthesizerFactory` pattern to decouple service logic from the Kokoro ONNX model.
- Integrate `onnx-community/Kokoro-82M-v1.0-ONNX` using `onnxruntime` (CPU default).
- Implement explicit tokenization (phonemization) support (e.g. `misaki` or `phonemizer`) as required by the model.
- Consume `TextTranslatedEvent` -> Produce `AudioSynthesisEvent`.
- **Validation**: Verify audibility, measure RTF (Real-Time Factor), and validate payload transport.

## Assumptions
- `speech-lib.storage.ObjectStorage` is available but OPTIONAL for v0.5.0; service must run without it (inline-only).
- ONNX Runtime and Tokenizers libraries are compatible with the base python image.
- 500 characters is a reasonable initial hard cap for input text (approx 30s audio).
- Inline Payload Duration Guideline (24kHz, 16-bit Mono):
  - 1 sec ≈ 48,000 bytes (0.046 MiB).
  - 1.25 MiB cap ≈ 27.3 seconds of audio.
  - Payloads exceeding ~27s will likely trigger the Claim Check path or warning.

## Contract Decisions

### Schema Contract
- **Producer**: `tts` service.
- **Consumer**: `gateway` (pass-through) -> Web Client (final consumer).
- **Compatibility**: Additive evolution (new fields are optional/unions) subject to Registry `BACKWARD` enforcement.
- **Evolution**: New fields added as `union {null, type}` with default null.

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

### Data Retention & Privacy
- **Audio URI Lifecycle**: Managed via object store key reference.
- **Retention**: Time-bounded, configurable via environment (default target: 24 hours).
- **URI Type**: Internal object key (preferred) OR Presigned URL.
  - **Preferred path**: TTS emits internal object key; Gateway generates ephemeral presigned URL at read time.
  - **Fallback path**: TTS emits presigned URL; Gateway MUST support re-issuing/refreshing if expired.
- **Log Privacy**: Presigned URLs must NEVER be logged relative to `audio_uri`. Log the object key instead.

### Input Behavior Contract
- **Text Length**: Hard Reject (> 500 chars).
- **Behavior**: If `text` length > 500, log specific warning "Text exceeds 500 char contract" and drop event (do not crash, do not synthesize).

## Milestones

### M1: Schema Definition & Shared Contract
**Goal**: Define the output event structure that supports both small (inline) and large (URI) audio payloads.
**Deliverables**:
- `speech.tts.audio-value.avsc` schema registered (Compatibility: BACKWARD).
  - Fields: `correlation_id` (required), `audio_bytes` (optional), `audio_uri` (optional), `audio_format` (default 'wav'), `content_type` (default 'audio/wav'), `sample_rate`, `text_snippet`, `speaker_reference_bytes` (optional, pass-through).
- Updated `speech-lib` with generated classes.

### M2: TTS Service Scaffold & Pluggable Factory
**Goal**: Create the service structure that isolates the model dependency.
**Deliverables**:
- Service module `services/tts` with Dockerfile (GPU-ready structure).
- `SynthesizerFactory` implementation decoupling logic from engine.
- Configuration for `TTS_MODEL_ENGINE` (default: "kokoro_onnx").

### M3: Kokoro ONNX Integration & Tokenization
**Goal**: Implement the concrete synthesizer using the specified model and correct text pre-processing.
**Deliverables**:
- `KokoroSynthesizer` implementation loaded via `onnxruntime`.
- Tokenizer integration (`misaki` or `phonemizer`) matching model requirements.
- Unit tests verifying pipeline with mock ONNX session.

### M4: Event Loop & Payload Management (Claim Check)
**Goal**: Connect Kafka input/output and handle payload size and storage constraints.
**Deliverables**:
- Consumer loop for `speech.translation.text`.
  - Logic to extract `speaker_reference_bytes` (pass-through).
- Payload logic implementing the **Claim Check Pattern**:
  - **Inline**: < 1.25 MiB (emit `audio_bytes`).
  - **URI**: > 1.25 MiB (upload to S3, emit `audio_uri`).
  - **Fallback**: If > 1.25 MiB and `DISABLE_STORAGE=true`, log warning and drop.
- Enforcement of **Input Behavior Contract** (drop > 500 chars) and **Observability Contract**.

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
  - Send Mock Large Text (simulated size > 1.25 MiB) with Storage -> Verify `audio_uri` (present) and `audio_bytes` (null).
  - Send Mock Large Text with `DISABLE_STORAGE=true` -> Verify event dropped with warning.
- **Performance Verification**:
  - Measure RTF (Real-Time Factor) on target hardware.
  - Outcome: RTF is measured and recorded.

## Risks
- **Model Download Time**: Kokoro model download might timeout on first container start.
  - *Mitigation*: Use a build-stage download or volume mount for model cache.
- **Tokenization Complexity**: Some ONNX voice models require complex phoneme mapping in Python.
  - *Mitigation*: Use `misaki` or `phonemizer` compatible with Kokoro, pinned in `requirements.txt`.

## Rollback Plan
- If Kokoro ONNX proves unstable or too slow on CPU, revert `TTS_MODEL_ENGINE` to a simple system-speech fallback or revert to mock for v0.5.0 functional demo.
- Note: Architecture Findings 011 specifically approved Kokoro ONNX, so persistence on this path is preferred.
