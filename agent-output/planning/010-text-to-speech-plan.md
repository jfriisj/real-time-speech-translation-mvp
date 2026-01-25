# Plan 010: Text-to-Speech (TTS) Service (Kokoro ONNX)

**Plan ID**: 010
**Target Release**: v0.5.0
**Epic Alignment**: Epic 1.7 Text-to-Speech (TTS) (Stable Outcome)
**Architecture**: [Findings 011](agent-output/architecture/011-tts-indextts-2-architecture-findings.md) (APPROVED_WITH_CHANGES)
**Process Improvement**: Includes mandatory "Measurement Method" (PI-009).
**Status**: Implementation In Progress (Rev 9 - Updated Checklists)

## Changelog

| Date | Event | Summary |
|------|-------|---------|
| 2026-01-25 | Initial Draft | Created plan for Epic 1.7 based on Architecture Findings 011. |
| 2026-01-25 | Revision 1 | Removed implementation signatures/MinIO logic from shared-lib. Aligned with v0.5.0. |
| 2026-01-25 | Revision 2 | Pinned speaker context strategy (Findings 006), removed threshold details, added consumer fields. |
| 2026-01-25 | Revision 3 | Added explicit pass-through contract, pinned URI failure semantics, moved testing strategy to QA. |
| 2026-01-25 | Revision 4 | Added Schema Compatibility & Consumer Failure contracts per Analysis. Documented dataset provenance. |
| 2026-01-25 | Revision 5 | Added Data Retention, Observability Contract, Risks, and Rollout Strategy. |
| 2026-01-25 | Revision 6 | Added explicit Testing Infrastructure requirements (pytest, conftest mocks) based on implementation findings. |
| 2026-01-25 | Revision 7 | Pivoted synthesizer to `onnx-community/Kokoro-82M-v1.0-ONNX` for runtime stability while enforcing a pluggable architecture for future model swaps (IndexTTS/Qwen). |
| 2026-01-25 | Revision 8 | Incorporated Findings 013: layered boundary, schema safety for model_name, pinned factory contract/providers, max-text caps, and asset caching. |
| 2026-01-25 | Revision 9 | Marked implementation steps `[x]` as scaffolding and schema updates are complete. |

## Value Statement and Business Objective
As a User, I want to hear the translated text spoken naturally, So that I can consume the translation hands-free.

**Measure of Success**:
- **Real-Time Factor (RTF)** < 1.0 (Synthesis time < Audio Duration).
- **Latency P50** < 2000ms (Total time from `TextTranslatedEvent` to `AudioSynthesisEvent`).

### Success Metric Measurement Method
**Metric 1: Real-Time Factor (RTF)**
- **Formula**: `RTF` = `Synthesis Computation Time (ms)` / `Output Audio Duration (ms)`.
- **Target**: RTF < 1.0.
- **Dataset**: `tests/data/metrics/tts_phrases.json`.
    - **Provenance**: Manually curated set of 15 phrases (5 Short, 5 Medium, 5 Long) in English and Spanish. Designed to test phoneme variety and duration scaling.
    - **Content**: 5x <3s, 5x ~10s, 5x >30s phrases.
- **Guardrail**: If RTF > 1.0 on reference hardware, optimization is required.

**Metric 2: Latency P50**
- **Formula**: `end_time` (event produced) - `start_time` (event consumed).
- **Measurement**: Logs from the TTS service.

**Metric 3: Payload Cap Compliance**
- **Validation**: Confirm events use `audio_uri` when payload size exceeds configured broker limit.

**Metric 4: Audio Quality Check**
- **Method**: Manual playback of 5 generated samples.
- **Criteria**: "Intellegible with no artifacts/clicking".

## Roadmap Alignment
**Plan Status**: Aligned with Epic 1.7 (Stable Outcome).
**Model Selection**: `onnx-community/Kokoro-82M-v1.0-ONNX` (per Updated Roadmap).
**Architecture Requirement**: This plan enforces a **Pluggable Synthesizer Architecture** (Factory Pattern) to satisfy the roadmap's extensibility requirement for future model swaps (IndexTTS/Qwen).

## Objective
Implement the `tts-service` using `onnx-community/Kokoro-82M-v1.0-ONNX` to synthesize speech from `TextTranslatedEvent`. Support "Dual-Mode Transport" (Inline vs URI) and propagate Speaker Context from Ingress to TTS across the pipeline. Ensure the synthesizer implementation is pluggable to support future model migration.

## Architectural Contracts (Must be implemented)

### 1. Speaker Context Propagation
- **Strategy**: Inline "Reference Clip" (Bytes) & Speaker ID.
- **Implementation**: The Kokoro backend will primarily use `speaker_id` to map to pre-defined Style Vectors (e.g., `af_bella`). `speaker_reference_bytes` passed for future cloning but ignored by the default Kokoro ONNX implementation.
- **Origin**: Ingress (or VAD).
- **Pass-through Requirement**: All intermediate services (ASR, Translation) **MUST** propagate `speaker_reference_bytes` and `speaker_id` unchanged.
- **Privacy**: Ephemeral processing only. DO NOT persist reference clips beyond the session scope.

### 2. Transport & Failure Semantics
- **Dual-Mode**: Service MUST support switching to Object Store URI when payload exceeds safe inline limit.
- **URI Failure Policy (Producer Side)**: If `audio_uri` generation fails, the service **MUST** log the error and fall back to the default internal voice (or drop if critical), but **MUST NOT crash-loop**.
- **URI Failure Policy (Consumer Side)**: Downstream consumers attempting to fetch `audio_uri` **MUST** handle 404/Timeout errors by logging the failure with `correlation_id` and treating the event as a playback failure (or skipping). DO NOT retry indefinitely.
- **Correlation**: Producer MUST key output messages by `correlation_id`.

### 3. Schema Evolution & Compatibility
- **Compatibility Mode**: All schema updates MUST respect `BACKWARD` (or `BACKWARD_TRANSITIVE`) compatibility in Schema Registry.
- **Optionality**: All new fields (`speaker_reference_bytes`, `speaker_id`, `audio_uri`, `model_name`) MUST be defined as **Union with Null** (optional).
- **Impact**: Existing consumers MUST be able to read new events without crashing (ignoring new fields).

### 4. Data Retention & Lifecycle
- **Scope**: Applied to objects stored in the `tts-audio` bucket (audio_uri payloads).
- **Policy**: **Ephemeral (24 Hours)**.
- **Mechanism**: MinIO Bucket Lifecycle Rule (Expiration).
- **Asset Caching**: Model weights and voice files MUST be cached in a deterministic path (e.g., `/app/model_cache`) to ensure measurable cold-starts.

### 5. Observability Contract
- **Log Level**: INFO
- **Mandatory Fields**:
    - `correlation_id`: Must be present in every log entry.
    - `model_name`: Log the active synthesizer model (e.g., "Kokoro-82M-ONNX").
    - `synthesis_latency_ms`: Time taken for model inference.
    - `payload_mode`: "INLINE" or "URI".

### 6. Operational Constraints
- **Layering**: Service MUST be structured into strict layers: Orchestration (Kafka), Synthesizer Backend (ONNX), Storage Adapter. No business logic in Orchestration.
- **Input Cap**: Input text MUST be truncated or rejected if > 500 characters to prevent runaway processing/latency.
- **Providers**: Explicitly configure `onnxruntime` for CPU or GPU via `ONNX_PROVIDER` env var (default: `CPUExecutionProvider`).

## Context
- **Roadmap**: Epic 1.7 (Speech-to-Speech loop completion).
- **Architecture**:
    - **Transport**: Option D2 (Dual-mode).
    - **Voice Strategy**: Style Vector Mapping (via `speaker_id`).

## Assumptions
- MinIO infrastructure is available in the stack.
- `onnxruntime` (or `onnxruntime-gpu`) is compatible with the base container image.

## Constraints
- **WAV Only**: Output format MUST be `wav` (24kHz for Kokoro).
- **Shared Library Scope**: `speech-lib` MUST NOT contain network/storage client logic.
- **Unit Test Isolation**: Mock `onnxruntime`, `boto3`, and other external I/O.
- **Model Agnostic Pipeline**: The core service code (`main.py`, `consumer.py`) MUST NOT import model-specific libraries directly. Use a Factory/Interface abstraction.

## Testing Strategy
### Unit Testing
- **Framework**: `pytest` with `pytest-cov`.
- **Coverage Target**: >70% line coverage for business logic.
- **Mocking Strategy**: Use `conftest.py` to inject mock modules for `onnxruntime`, `boto3`, `prometheus_client`.
- **Key Modules**:
  - `synthesizer_factory.py`: Test correct backend loading based on config.
  - `synthesizer_kokoro.py`: Test phoneme conversion logic (mocking the actual inference).

### Integration Testing (QA Phase)
- **Scope**: Validate interaction with MinIO and Kafka using Docker Compose.

## Plan Steps

### 1. Shared Infrastructure & Contract Updates
**Objective**: Update schemas to support Dual-Mode transport and Speaker Context propagation.
- [x] Update `shared/schemas/avro/` to create `AudioSynthesisEvent.avsc`:
    - **Fields**: `correlation_id`, `timestamp_ms`, `model_name`.
    - **Audio Payload**: `audio_bytes` / `audio_uri` (Mutually Exclusive Logic).
    - **Audio Metadata**: `duration_ms`, `sample_rate_hz`, `audio_format` (default "wav").
- [x] Update upstream schemas (`AudioInputEvent`, `TextRecognizedEvent`, `TextTranslatedEvent`) to add optional `speaker_reference_bytes` and `speaker_id`.
- [x] Update `speech-lib`: Regenerate Python classes.

### 2. Infrastructure Services (MinIO)
**Objective**: Ensure Object Store availability.
- [x] Provision MinIO service with default buckets (e.g., `tts-audio`).
- [x] Configure access credentials.

### 3. TTS Service Implementation
**Objective**: Create the synthesis microservice with ONNX backend.
- [x] Initialize `services/tts/` module.
- [x] **Dependency Management**:
    - Update `pyproject.toml` to include: `onnxruntime` (or gpu variant contextually), `misaki` (for phonemes), `soundfile`.
    - **Remove**: `indextts` dependency.
- [x] **Setup Testing Infrastructure**:
    - Configure `tests/conftest.py` to mock `onnxruntime.InferenceSession` and `misaki` tokenization.
- [x] **Implement Pluggable Synthesizer Architecture**:
    - Define `Synthesizer` abstract base class:
        - Signature: `synthesize(text, speaker_ref, speaker_id) -> (audio_bytes, sample_rate, duration_ms)`.
    - Implement `SynthesizerFactory` that reads `TTS_MODEL_NAME` env var.
- [x] **Implement Kokoro ONNX Backend**:
    - Implement `KokoroSynthesizer` class.
    - **Voice Mapping**: Create a mapping of `speaker_id` -> `voices/*.bin` style vectors.
    - **Pipeline**: Text -> `misaki` Phonemes -> Tokenizer -> `onnxruntime` Inference -> Audio.
    - **Model Handling**: Auto-download `onnx-community/Kokoro-82M-v1.0-ONNX` model and voice assets on startup to `/app/model_cache`.
- [x] Implement `Dual-Mode Producer` (MinIO Upload + Kafka Produce).
- [x] Implement `Consumer` loop. Measurement logging.

### 4. Integration & Deployment
**Objective**: Wire up the full Speech-to-Speech loop.
- [x] Update `docker-compose.yml`.
- [x] **Pass-through Update**: Update ASR and Translation service consumers/producers to propagate `speaker_reference_bytes` and `speaker_id`.

### 5. Version Management
**Objective**: Prepare valid release artifacts.
- [ ] Update `services/tts/pyproject.toml` version to `0.5.0`.
- [ ] Update `CHANGELOG.md` reflecting Epic 1.7 delivery.

## Validation (Acceptance Criteria)
- [ ] TTS Service is running and healthy using Kokoro ONNX model.
- [ ] Pluggable interface allows swapping model config (verified via code review/unit test).
- [ ] Events are correctly keyed by `correlation_id`.
- [ ] Large payloads > 1.5MB are delivered via MinIO URI.
- [ ] Synthesis RTF is measured and logged.

## Risks & Mitigations
- **Risk: Model Resource Consumption**: Although ONNX is lighter, long-form synthesis can still spike CPU.
    - **Mitigation**: Limit concurrency (single worker for MVP) and enforce max text length caps.
- **Risk: MinIO Reliability**: Essential for large payloads; downtime breaks long-form synthesis.
    - **Mitigation**: "Dual-Mode with Fallback". If upload fails, log error and drop.
- **Risk: Voice Mapping Gaps**: If `speaker_id` is unknown, synthesis might fail.
    - **Mitigation**: Implement robust fallback to a default voice style (e.g., `af_bella`) if the ID is missing or unmapped.

## Rollout & Rollback Strategy
### Rollout
1.  **Infrastructure**: Deploy MinIO with Lifecycle Rules (24h).
2.  **Schema**: Register new forward-compatible schema (Optional fields).
3.  **Services**: Deploy `tts-service`. Restart ASR/Translation services.
4.  **Traffic**: Enable full pipeline.

### Rollback
- **Trigger**: P95 Synthesis Latency > 5s or Error Rate > 5%.
- **Action**: Corrective forward-fix preferred.
- **Full Revert**: Revert `tts-service` image.
