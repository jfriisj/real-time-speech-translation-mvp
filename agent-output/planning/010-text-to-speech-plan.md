# Plan 010: Text-to-Speech (TTS) Service (Kokoro ONNX)

**ID**: 010 (Rev 35)
**Target Release**: v0.5.0
**Epic**: Epic 1.7 (TTS)
**Status**: Approved (Detailed Design)
**Plan Owner**: Planner Agent
**Date**: 2026-01-27
**Analysis Ref**: agent-output/analysis/010-text-to-speech-plan-analysis.md, agent-output/analysis/012-text-to-speech-claim-check-analysis.md
**Architecture Ref**: agent-output/architecture/019-text-to-speech-plan-architecture-findings.md, agent-output/architecture/020-claim-check-scope-shift-architecture-findings.md, agent-output/architecture/021-text-to-speech-plan-rev33-architecture-findings.md
**Security Ref**: agent-output/security/010-text-to-speech-security-pre-implementation.md

## Value Statement and Business Objective
**User Story**: As a User, I want to hear the translated text spoken naturally, So that I can consume the translation hands-free.

**Business Objective**: Deliver a stable (ONNX-based) and scalable TTS capability that completes the "Source Audio -> Translated Audio" loop ("Speech-to-Speech").
**Key Requirement**: Support large audio synthesis (> 1.25MiB) by fully implementing the **Claim Check Pattern** (using MinIO/S3), ensuring the system does not crash or clog Kafka when synthesizing longer phrases (Validation of Epic 1.8 core concepts within v0.5.0).

## Test Infrastructure & Tooling Requirements
**Objective**: Ensure the service is verifiable in isolation and within the event pipeline.

*   **Unit Testing Framework**: `pytest` with `pytest-cov`.
    *   **Configuration**: `pytest.ini` correctly targeting `services/tts/tests`.
    *   **Fixtures**: Mock ONNX runtime session, Mock Kafka Consumer/Producer.
*   **Integration Testing Infrastructure**:
    *   **Docker Compose**: Ensure `docker-compose.yml` (and test overrides) actively provides:
        *   Zookeeper & Kafka
        *   Schema Registry
        *   MinIO (S3 compatible storage) - **REQUIRED** for Claim Check validation.
        *   TTS Service (Build from source)
        *   **MinIO Initialization**: `minio-init` service MUST run to create the `tts-audio` bucket and apply the `minio-lifecycle.json` policy (24h TTL).
    *   **Validation Script**: `tests/e2e/tts_pipeline_smoke.py` configured to connect to the test infrastructure.
*   **Dependencies**:
    *   `pytest`, `pytest-asyncio`, `pytest-cov`, `testcontainers` (optional, for advanced orchestration), `boto3` (for S3 verification).

## Scope
- Create `tts` service module.
- Implement `AudioSynthesisEvent` Avro schema with inline-OR-URI payload support.
- Implement `SynthesizerFactory` pattern to decouple service logic from the Kokoro ONNX model.
- Integrate `onnx-community/Kokoro-82M-v1.0-ONNX` using `onnxruntime` (CPU default).
- Implement explicit tokenization (phonemizer) using `espeak-ng`.
- **Infrastructure Integration**: Utilize the shared `ObjectStorage` utility and MinIO service (delivered in shared infra) to offload large payloads.
- **Verification**: Verify audibility, measure RTF (Real-Time Factor), and validate **Claim Check transport** for large files.
- **Evidence Collection**:
  - QA Script: `tests/e2e/tts_pipeline_smoke.py` MUST verify both inline and URI paths.

## Assumptions
- `speech-lib.storage.ObjectStorage` and MinIO container are **AVAILABLE and REQUIRED** for full compliance (large payloads).
- **Operable without Storage**: Service MUST start and process inline payloads even when storage is disabled/unavailable; only oversized outputs are dropped.
- ONNX Runtime and Tokenizers libraries are compatible with the base python image.
- `espeak-ng` system dependency is available in the runtime environment (required by `phonemizer`).
- 500 characters is a reasonable initial hard cap for input text (approx 30s audio).
- **Payload Policy**:
  - **< 1.25 MiB**: Send inline (`audio_bytes`).
  - **> 1.25 MiB**: Send URI (`audio_uri`) via MinIO.
  - **Fallback**: If MinIO is unreachable AND payload > 1.25 MiB => Drop with Error (Log-and-Drop). Do NOT crash.
- **Key Ownership & Lifecycle**:
  - TTS creates keys using a canonical format: `tts/{correlation_id}.wav`.
  - **Collision Risk (Accepted Debt)**: If a `correlation_id` is reused (retry/replay), the object will be overwritten ("Last Write Wins"). This is accepted for v0.5.0 MVP to keep logic simple.
  - Retention is managed by MinIO bucket configuration (lifecycle policy). Target: 24h retention.

## Contract Decisions

### Gateway/Edge Retrieval Contract (Claim Check)
- **Problem**: `audio_uri` is an internal object key (e.g., `tts/<uuid>.wav`), but web clients need a reachable URL.
- **Solution defined**:
  - **TTS Responsibility**: Emits the internal object key (`audio_uri`). Do NOT emit presigned URLs (security risk, coupling).
  - **Gateway Responsibility**: The Gateway (or edge service) is responsible for converting the internal key to a client-accessible URL (e.g., by generating a short-lived presigned URL or proxying) at read time.
  - **Gateway Policy (TTL)**: Gateway-generated presigned URLs MUST be short-lived (e.g., 15 minutes) and NEVER persisted or logged.
  - **Constraint**: `TTS_AUDIO_URI_MODE` MUST default to `internal` for v0.5.0 to enforce this boundary.

### Configuration & Environment
To ensure consistent behavior across environments, the service MUST expose and document these configuration options:

| Env Var | Default | Description |
| :--- | :--- | :--- |
| `INLINE_PAYLOAD_MAX_BYTES` | `1310720` (1.25 MiB) | Threshold for switching from inline bytes to URI storage. |
| `DISABLE_STORAGE` | `0` (false) | If `1`, disables MinIO usage. Large payloads encountered in this mode will be logged and DROPPED. |
| `FORCE_AUDIO_URI` | `0` (false) | **Test Only**: Forces all payloads to use URI storage regardless of size. Use to verify MinIO integration with small samples. |
| `TTS_AUDIO_URI_MODE` | `internal` | **Restricted**: MUST be `internal` for v0.5.0. Emits `tts/{cor_id}.wav` key. External/presigned modes are reserved for future use. |
| `MINIO_ENDPOINT` | `http://minio:9000` | S3-compatible service URL. Default assumes Docker Compose network. Use `http://127.0.0.1:9000` for host-mode tests. |
| `MINIO_ACCESS_KEY` | `minioadmin` | Access key for authentication. |
| `MINIO_SECRET_KEY` | `minioadmin` | Secret key for authentication. |
| `MINIO_BUCKET` | `tts-audio` | Bucket name (created by infrastructure). |
| `MINIO_SECURE` | `0` (false) | Set to `1` (true) to use HTTPS for MinIO connections. |
| `MINIO_PUBLIC_ENDPOINT` | (Empty) | Optional public-facing endpoint (e.g. `http://localhost:9000`). Used only for local debugging; NOT used for Gateway delivery. |
| `MINIO_PRESIGN_EXPIRY_SECONDS` | `86400` (24h) | **Internal Use**: Max age for any internal testing URLs. NOTE: Gateway applies its own shorter policy for client-facing URLs. |

### Schema Contract
- **Producer**: `tts` service.
- **Consumer**: `gateway` (pass-through) -> Web Client (final consumer).
- **Source of Truth**: `shared/schemas/avro/AudioSynthesisEvent.avsc`
- **Critical Fields**:
  - `audio_bytes`: `bytes` (nullable) - Inline audio data (typically WAV).
  - `audio_uri`: `string` (nullable) - Internal object key (e.g., `tts/<uuid>.wav`) for retrieval via Gateway/Pre-signer. NOT a public URL.
  - `duration_ms`: `long` - Duration of audio in milliseconds.
  - `sample_rate_hz`: `int` - Sample rate (e.g. 24000).
- **Integrity Metadata**:
  - `audio_sha256` / `audio_size_bytes` (Optional): Consumers MAY use these to validate the payload. Mismatch should be treated as a non-fatal integrity warning (or fetch failure) rather than a system crash.
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
- **Infrastructure**: The `minio-init` container MUST run on startup to create the `tts-audio` bucket and apply the 24-hour retention policy (defined in `services/tts/minio-lifecycle.json`).
- **Retention**: Time-bounded (default: 24 hours). Service does NOT implement deletion logic.
- **URI Type**: Internal object key (preferred) for intra-system transport.
  - **Preferred path**: TTS emits internal object key; Gateway (edge) generates ephemeral presigned URL at read time for the client (using `TTS_AUDIO_URI_MODE=internal`).
- **Log Privacy**: Presigned URLs must NEVER be logged relative to `audio_uri` or any other field. Log the internal object key instead.

### Input Behavior Contract
- **Text Length**: Hard Reject (> 500 chars).
- **Behavior**: If `text` length > 500, log specific warning "Text exceeds 500 char contract" and drop event (do not crash, do not synthesize).
- **Storage Failure Behavior**: If `DISABLE_STORAGE=1` (or MinIO is unreachable) and a payload exceeds the inline limit:
  - MUST log Error/Warning: "Payload too large for inline and storage disabled" (or similar).
  - MUST DROP the event.
  - MUST NOT crash the service.
  - **Note**: A Dead Letter Queue (DLQ) is NOT required for v0.5.0; Log-and-Drop is the approved failure mode for MVP.

### Security Controls (Pre-Implementation Gate)
**Objective**: Mitigate risks identified in Security Assessment 010 (Credentials, Supply Chain, Edge Exposure).
- **Secrets Management**:
  - `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` MUST NOT use default values (`minioadmin`) in any environment except `localhost`.
  - Credentials must be injected via environment variables (Docker Secrets or similar in future).
- **Supply Chain Pinning**:
  - **Containers**: MinIO and other base images MUST be pinned to a specific version digest or tag (no `:latest`).
  - **Models**: The loading logic MUST pin the Hugging Face model to a specific `revision` (commit hash or immutable tag) to prevent supply chain drift.
- **Data Protection**:
  - **Logs**: User text (`text_snippet`) and audio content must be minimized in logs.
  - **Edge**: Presigned URLs generated by the Gateway MUST have short TTLs (e.g., <15 minutes) and MUST NEVER be logged.
- **Integrity**:
  - **Claim Check**: The transport should support optional integrity metadata (`audio_sha256`) to detect storage corruption.

## Milestones

### M1: Schema Definition & Shared Contract
**Goal**: Define the output event structure that supports both small (inline) and large (URI) audio payloads, plus integrity metadata.
**Deliverables**:
- Schema file created at `shared/schemas/avro/AudioSynthesisEvent.avsc`.
- Schema registered with Subject `speech.tts.audio-value` (Compatibility: BACKWARD).
  - Fields: `correlation_id` (required), `audio_bytes` (optional), `audio_uri` (optional), `audio_format` (default 'wav'), `content_type` (default 'audio/wav'), `sample_rate_hz`, `text_snippet`, `speaker_reference_bytes` (optional, pass-through).
  - **New Security Fields**: `audio_sha256` (string, optional), `audio_size_bytes` (long, optional) for integrity checks.
- Updated `speech-lib` with generated classes.

### M2: TTS Service Scaffold & Pluggable Factory
**Goal**: Create the service structure that isolates the model dependency.
**Deliverables**:
- Service module `services/tts` with Dockerfile (GPU-ready structure).
- **Test Configuration**: `pyproject.toml` updated with `pytest` dependencies; `pytest.ini` created.
- `SynthesizerFactory` implementation decoupling logic from engine.
- Configuration loading `Settings` from environment (implementing the Table in Contract Decisions).
- Configuration for `TTS_MODEL_ENGINE` (default: "kokoro_onnx").

### M3: Kokoro ONNX Integration & Tokenization
**Goal**: Implement the concrete synthesizer using the specified model and correct text pre-processing.
**Deliverables**:
- `KokoroSynthesizer` implementation loaded via `onnxruntime`.
- **Security**: Logic MUST use a specific `revision` (commit hash) when loading from Hugging Face Hub (do not use `main`/HEAD).
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
- **Integration Test Harness**: Update `docker-compose.yml` to include `minio-init` bootstrap container and mount `minio-lifecycle.json`.

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
  - **Inline Path**: Send "Hello World" -> Verify valid WAV output (inline) AND `speaker_reference_bytes` present.
  - **URI Path**: Send Mock Large Text (or use `FORCE_AUDIO_URI=1`) -> Verify `audio_uri` (present, format `tts/...`) and `audio_bytes` (null).
  - **Storage Disabled**: Set `DISABLE_STORAGE=1` AND force large payload -> Verify event dropped with explicit warning (Log-and-Drop).
- **Observability & QA Evidence**:
  - **Logs**: Validated that `main.py` logs `correlation_id`, `audio_size_bytes`, `transport_mode` (`inline` vs `uri`), `synthesis_latency_ms`, and `rtf`.
  - **Smoke Test**: MUST provide QA evidence that the URI path works (e.g., via `tests/e2e/tts_pipeline_smoke.py`) and that audio can be re-fetched from MinIO.
- **Security Evidence**:
  - **Pinning**: Verify MinIO image in `docker-compose.yml` uses a specific tag (not `latest`). Verify model load uses a specific revision.
  - **Logs**: Verify no sensitive text (or PII) is logged by default. Verify no presigned URLs appear in logs.


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
