# Plan 002: Audio-to-Text Ingestion (ASR Service)

**Plan ID**: 002
**Target Release**: v0.2.0 (Core Services)
**Epic**: 1.2 Audio-to-Text Ingestion (ASR Service)
**Status**: Revised (2026-01-15, Revision 2)
**Date**: 2026-01-15
**Dependencies**: Plan 001 (Shared Infrastructure)

## 1. Value Statement and Business Objective
**As a** User,
**I want** my speech audio to be captured and converted to text events,
**So that** the system has raw material to translate.

**Measure of Success**:
- ASR Service successfully consumes an `AudioInputEvent` containing valid `audio_bytes`.
- ASR Service correctly transcribes the audio using a local model.
- ASR Service produces a valid `TextRecognizedEvent` to the canonical output topic `speech.asr.text`, including `text`, `language`, and `confidence`.
- `correlation_id` is preserved from input to output.

## 2. Context & Roadmap Alignment
This plan implements the first operational microservice of Release v0.2.0 ("Core Services"). It validates the "Shared Contracts" foundation by proving that a service can consume and produce compliant Avro events using the shared library.

**Roadmap Reference**:
- **Release v0.2.0**: Core Services
- **Epic 1.2**: Audio-to-Text Ingestion

**Architecture Guidance**:
- **Topics**: Consume from `speech.audio.ingress`. Produce to `speech.asr.text`.
- **Schema Strategy**: Use `TopicNameStrategy` (default in shared lib).
- **Tech Stack**: `shared/speech-lib` for Kafka/Avro. `transformers` + `openai/whisper-tiny` for ASR.

**Delivery Semantics (MVP)**:
- **At-least-once** processing is assumed. Duplicate outputs are acceptable for MVP and must be tolerated downstream; `correlation_id` enables traceability.

## 3. Assumptions & Constraints
- **Assumption**: `openai/whisper-tiny` is sufficient for MVP accuracy; we can swap for `base`/`small` later via config.
- **Constraint (Payload Size)**: **Strictly enforce 1.5 MiB payload limit.** Payloads > 1.5 MiB MUST be rejected with an error log (and dropped) for this MVP. Reference/URI support is deferred.
- **Constraint (Runtime)**: **Must use Python 3.11 or 3.12** for the container image to ensure mature PyTorch/Transformers support. Do NOT use Python 3.14 yet.
- **Constraint (Hardware)**: Must run on CPU for the CI/local environment.

## 4. Implementation Plan

### Milestone 0: Pre-Implementation Validation
**Objective**: Validate feasibility and determinism guardrails before coding.
1. **CPU Latency Benchmark**: Measure `openai/whisper-tiny` inference wall time on representative CPU hardware using a near-cap `wav` sample (≤1.5 MiB). Define pass/fail criteria aligned to MVP expectations.
2. **Model Caching Decision**: Choose a deterministic model distribution strategy (build-time download baked into the image OR pre-populated HF cache volume). Document the choice and reference in compose.
3. **Format Enforcement Location**: Confirm wav-only enforcement is applied at the service boundary (consumer) with log+drop for non-wav; no best-effort decode in MVP.

### Milestone 1: Service Initialization
**Objective**: Create the service structure and ensure it can start up and load the model.
1.  **Directory Setup**: Create `services/asr/` with `Dockerfile`, `src/`, `tests/`.
2.  **Dependency Definition**: Create `services/asr/pyproject.toml` (or `requirements.txt`).
    - **Base Python**: 3.11 or 3.12.
    - **Dependencies**: `torch` (CPU version), `transformers`, `librosa` (optional, verify if needed by generic pipeline), `soundfile`, `speech-lib`.
3.  **Model Loading**: Implement `src/transcriber.py` to load `openai/whisper-tiny` using Hugging Face `pipeline`.
    - **Note**: Ensure the model is cached or downloaded during the build/startup to avoid repetitive downloads in CI.

### Milestone 2: Kafka Consumer Implementation
**Objective**: Service can read `AudioInputEvent` and validate payload.
1.  **Consumer Setup**: Initialize the shared library’s consumer wrapper for topic `speech.audio.ingress`.
2.  **Field Extraction**:
    - Extract `payload.audio_bytes`.
    - Extract `payload.audio_format` (MVP requires `wav`).
    - Extract `payload.sample_rate_hz` (Use for checks).
3.  **Validation Logic**:
    - **Size Check**: If `len(audio_bytes)` > 1.5 MiB, Log Error ("Payload exceeds MVP limit") and DROP the event. Do not crash.
    - **Empty Check**: If bytes empty, Log Warning and DROP.
    - **Format Check (MVP)**: If `audio_format` != `wav`, Log Warning and DROP (no best-effort multi-format decode in MVP).
4.  **Decoding**: Convert `audio_bytes` to numpy array expected by generic ASR pipeline.

### Milestone 3: ASR Logic & Producer Implementation
**Objective**: Transcribe bytes and publish `TextRecognizedEvent`.
1.  **Inference**: Pass audio to `transcriber`. Obtain result.
2.  **Output Construction**: Create `TextRecognizedEvent` object.
    - `correlation_id`: Copy from input event (REQUIRED).
    - `payload.text`: The transcribed string.
    - `payload.language`: The detected language code (e.g. "en"). Default to "en" if detection unavailable.
    - `payload.confidence`: Extract confidence score (float 0.0-1.0). If model doesn't provide it, default to `1.0` or a sentinel value for MVP.
3.  **Producer Setup**: Initialize the shared library’s producer wrapper for topic `speech.asr.text`.
4.  **Publish**: Send the event.

### Milestone 4: Docker & Infrastructure
**Objective**: Run as a containerized service.
1.  **Dockerfile**: Use `python:3.11-slim` or `3.12-slim`.
    - Install system dependencies for audio (e.g., `ffmpeg` or `libsndfile1` if required by `soundfile`/`librosa`).
2.  **Compose Update**: Add `asr-service` to `docker-compose.yml`.
    - Depends on `schema-registry`, `kafka`.
    - ENV vars: `KAFKA_BOOTSTRAP_SERVERS`, `SCHEMA_REGISTRY_URL`, `MODEL_NAME="openai/whisper-tiny"`.
    - Model caching: Reference the chosen strategy from Milestone 0 (baked-in model or mounted HF cache volume) to ensure deterministic startup.

### Milestone 5: Version Management
**Objective**: Tag and release.
1.  **Version Update**: Set version to `0.2.0` in `services/asr/pyproject.toml`.
2.  **CHANGELOG**: Create `services/asr/CHANGELOG.md`.

## 5. Verification Strategy (QA Handoff)
- **Unit Tests (Offline)**:
    - **Strict Isolation**: Mock the `transformers.pipeline` and Kafka consumer.
    - Test `transcriber.py` logic with a *dummy* local wav file (repo asset) to ensure data shaping works without downloading a model.
    - Test Payload Size validation (assert >1.5MB raises/logs/drops).
- **Integration Tests (Smoke / Online)**:
    - **Marked**: Use `@pytest.mark.integration`.
    - **Scenario**:
        1. Start stack (`docker compose up`).
        2. Produce `AudioInputEvent` (valid wav, <1.5MB) to `speech.audio.ingress`.
        3. Assert `TextRecognizedEvent` on `speech.asr.text`.
        4. Validation: Check `text` is non-empty, `confidence` exists, and `correlation_id` matches.

## 6. Risks
- **Model Download Reliability**: Large model downloads at runtime can be slow/flaky. *Mitigation*: Mount a persistent volume for HF Cache in `docker-compose` to survive restarts.
- **Audio Format Policy (MVP)**: Only `wav` is accepted. *Mitigation*: If `audio_format` is not `wav` or bytes are malformed, Log and Drop; do not attempt multi-format decode in MVP.

## 7. Open Questions
- **Resolved**: Payload limit is 1.5 MiB (MVP). Oversized messages are dropped with log.
- **Resolved**: Python version is pinned to 3.11/3.12 for stability.

