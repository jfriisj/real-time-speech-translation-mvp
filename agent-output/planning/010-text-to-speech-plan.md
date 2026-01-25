# Plan 010: Text-to-Speech (TTS) Service (IndexTTS-2)

**Plan ID**: 010
**Target Release**: v0.5.0
**Epic Alignment**: Epic 1.7 Text-to-Speech (TTS) with IndexTTS-2
**Architecture**: [Findings 011](agent-output/architecture/011-tts-indextts-2-architecture-findings.md) (APPROVED_WITH_CHANGES)
**Process Improvement**: Includes mandatory "Measurement Method" (PI-009).
**Status**: Revised (Addressing Critique 010 Rev 5 - Added Retention, Observability, Risks, Rollout)

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

## Value Statement and Business Objective
As a User, I want to hear the translated text spoken naturally, so that I can consume the translation hands-free.

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

## Objective
Implement the `tts-service` using `IndexTeam/IndexTTS-2` to synthesize speech from `TextTranslatedEvent`. Support "Dual-Mode Transport" (Inline vs URI) and propagate Speaker Context from Ingress to TTS across the pipeline.

## Architectural Contracts (Must be implemented)

### 1. Speaker Context Propagation
- **Strategy**: Inline "Reference Clip" (Bytes).
- **Origin**: Ingress (or VAD).
- **Pass-through Requirement**: All intermediate services (ASR, Translation) **MUST** propagate `speaker_reference_bytes` and `speaker_id` unchanged in their output events if present in input.
- **Privacy**: Ephemeral processing only. DO NOT persist reference clips beyond the session scope.

### 2. Transport & Failure Semantics
- **Dual-Mode**: Service MUST support switching to Object Store URI when payload exceeds safe inline limit.
- **URI Failure Policy (Producer Side)**: If `audio_uri` generation fails, the service **MUST** log the error and fall back to the default internal voice (or drop if critical), but **MUST NOT crash-loop**.
- **URI Failure Policy (Consumer Side)**: Downstream consumers attempting to fetch `audio_uri` **MUST** handle 404/Timeout errors by logging the failure with `correlation_id` and treating the event as a playback failure (or skipping). DO NOT retry indefinitely.
- **Correlation**: Producer MUST key output messages by `correlation_id`.

### 3. Schema Evolution & Compatibility
- **Compatibility Mode**: All schema updates MUST respect `BACKWARD` (or `BACKWARD_TRANSITIVE`) compatibility in Schema Registry.
- **Optionality**: All new fields (`speaker_reference_bytes`, `speaker_id`, `audio_uri`, etc.) MUST be defined as **Union with Null** (optional).
- **Impact**: Existing consumers MUST be able to read new events without crashing (ignoring new fields).

### 4. Data Retention & Lifecycle
- **Scope**: Applied to objects stored in the `tts-audio` bucket (audio_uri payloads).
- **Policy**: **Ephemeral (24 Hours)**.
- **Mechanism**: MinIO Bucket Lifecycle Rule (Expiration).
- **Rationale**: Audio is transient for immediate playback. Long-term storage is out of scope for MVP.
- **Privacy Impact**: Voice references and synthesized output are automatically purged.

### 5. Observability Contract
- **Log Level**: INFO
- **Mandatory Fields**:
    - `correlation_id`: Must be present in every log entry.
    - `input_char_count`: Length of input text.
    - `synthesis_latency_ms`: Time taken for model inference.
    - `payload_mode`: "INLINE" or "URI".
    - `payload_size_bytes`: Size of the generated audio.
- **Metrics**:
    - `tts_latency_seconds_bucket` (Histogram).
    - `tts_errors_total` (Counter, labelled by error_type).

## Context
- **Roadmap**: Epic 1.7 (Speech-to-Speech loop completion).
- **Architecture**:
    - **Transport**: Option D2 (Dual-mode).
    - **Voice Cloning Strategy**: [Findings 006 Option A] Inline Reference Clip via Event Envelope.

## Assumptions
- MinIO infrastructure is available in the stack.
- Broker message size limits are static configuration.

## Constraints
- **WAV Only**: Output format MUST be `wav`.
- **Shared Library Scope**: `speech-lib` MUST NOT contain network/storage client logic.
- **Unit Test Isolation**: Unit tests MUST NOT require valid AWS/MinIO credentials or active Kafka brokers. External I/O must be mocked (e.g., via `unittest.mock` or `conftest.py` injection).

## Testing Strategy
### Unit Testing
- **Framework**: `pytest` with `pytest-cov`.
- **Coverage Target**: >70% line coverage for business logic.
- **Mocking Strategy**: Use `conftest.py` to inject mock modules for heavy or unavailable dependencies (e.g., `boto3`, `prometheus_client`) to allow testing logic without installing full prod dependencies or requiring credentials.
- **Key Modules**:
  - `storage.py`: Test bucket operations and fallback logic (mocked).
  - `synthesizer.py`: Test audio generation logic and numeric handling (e.g., NumPy array truthiness).
  - `audio_helpers.py`: Test WAV conversion and duration calculation.

### Integration Testing (QA Phase)
- **Scope**: Validate interaction with MinIO and Kafka.
- **Tools**: `docker-compose` or `testcontainers`.
- **Scenarios**:
  - Verify MinIO upload and URI generation for large payloads.
  - Verify Kafka consumer reads from `text-translated` and producer writes to `tts-output`.

## Plan Steps

### 1. Shared Infrastructure & Contract Updates
**Objective**: Update schemas to support Dual-Mode transport and Speaker Context propagation.
- [ ] Update `shared/schemas/avro/` to create `AudioSynthesisEvent.avsc`:
    - **Fields**: `correlation_id`, `timestamp_ms`.
    - **Audio Payload**: `audio_bytes` (union/null) OR `audio_uri` (union/null). Semantics: Exactly one MUST be populated.
    - **Audio Metadata**: `duration_ms`, `sample_rate_hz`, `audio_format` (default "wav").
    - **Consumer Context**: `content_type` (e.g., "audio/wav"), `speaker_id` (optional).
- [ ] Update upstream schemas (`AudioInputEvent`, `TextRecognizedEvent`, `TextTranslatedEvent`) or Envelope:
    - **Change**: Add `speaker_reference_bytes` and `speaker_id` fields as **Optional (Union with Null)**.
    - **Semantics**: Define these as "Pass-through" fields for intermediate services.
- [ ] Update `speech-lib`:
    - Regenerate Python classes.
    - Export `TOPIC_TTS_OUTPUT` constant.

### 2. Infrastructure Services (MinIO)
**Objective**: Ensure Object Store availability.
- [ ] Provision MinIO service with default buckets (e.g., `tts-audio`).
- [ ] Configure access credentials via environment variables.

### 3. TTS Service Implementation
**Objective**: Create the synthesis microservice.
- [ ] Initialize `services/tts/` module.
- [ ] **Setup Testing Infrastructure**:
    - Configure `pytest.ini` and `tests/conftest.py`.
    - Implement module mocking (sys.modules injection) for `boto3` and `prometheus_client`.
- [ ] Implement `TTS Model Integration`:
    - Load `IndexTeam/IndexTTS-2` (Hugging Face).
    - Ensure thread-safe synthesis.
- [ ] Implement `Speaker Context Logic`:
    - **Requirement**: Extract `speaker_reference_bytes` from input event.
    - **Fallback**: If reference is missing/invalid, use default voice.
- [ ] Implement `Dual-Mode Producer`:
    - Key constraint: **Key messages by `correlation_id`**.
    - **Requirement**: Compare output size against safe inline threshold.
   Risks & Mitigations
- **Risk: High Latency with Voice Cloning**: Voice cloning inference is significantly slower than standard TTS.
    - **Mitigation**: Enforce aggressive timeouts and strict payload caps (~10s max synthesis). Fallback to standard voice if latency exceeds SLA.
- **Risk: MinIO Reliability**: Essential for large payloads; downtime breaks long-form synthesis.
    - **Mitigation**: "Dual-Mode with Fallback". If upload fails, log error and drop (or fallback to inline if close to limit - though complex). For MVP: Log & Drop, ensure consumers handle retrieval failures gracefully.
- **Risk: Schema Incompatibility**: New optional fields breaking strict consumers.
    - **Mitigation**: Strict validation of `union/null` types. E2E tests validating backward compatibility.
- **Risk: Model Resource Consumption**: IndexTTS-2 is heavy on CPU.
    - **Mitigation**: Limit concurrency (single worker for MVP). Define resource limits in `docker-compose`.

## Rollout & Rollback Strategy
### Rollout
1.  **Infrastructure**: Deploy MinIO with Lifecycle Rules (24h).
2.  **Schema**: Register new forward-compatible schema (Optional fields).
3.  **Services**: Deploy `tts-service`. Restart ASR/Translation services (safe due to optional fields).
4.  **Traffic**: Enable full pipeline.

### Rollback
- **Trigger**: P95 Synthesis Latency > 5s or Error Rate > 5%.
- **Action**: Corrective forward-fix preferred (disable cloning flag).
- **Full Revert**: Revert `tts-service` image. ASR/Translation can remain on new version (extra fields ignored by old consumer) or be reverted if necessary.
- **Data**: No rollback needed for ephemeral MinIO data; buckets can be purged.

##  - **Requirement**: If below threshold, emit inline (`audio_bytes`).
    - **Requirement**: If above threshold, upload to Object Store (Service-owned logic) and emit URI (`audio_uri`).
    - **Failure Handling**: Implement "Log and Fallback" policy for MinIO failures.
- [ ] Implement `Consumer`:
    - Subscribe to `speech.translation.text`.
    - Handle standard decoding and error states.
- [ ] **Measurement**: Log RTF and Latency metrics.

### 4. Integration & Deployment
**Objective**: Wire up the full Speech-to-Speech loop.
- [ ] Update `docker-compose.yml`.
- [ ] **Pass-through Update**: Update ASR and Translation service consumers/producers to propagate `speaker_reference_bytes` and `speaker_id` if present.

### 5. Version Management
**Objective**: Prepare valid release artifacts.
- [ ] Update `package.json` to `v0.5.0-rc`.
- [ ] Update `CHANGELOG.md` reflecting Epic 1.7 delivery.
- [ ] Create/Update Release Notes for v0.5.0.

## Validation (Acceptance Criteria)
- [ ] TTS Service is running and healthy.
- [ ] Events are correctly keyed by `correlation_id`.
- [ ] Small payloads are delivered inline.
- [ ] Large payloads > 1.5MB are delivered via MinIO URI.
- [ ] Speaker Context (if provided) is consumed without error.
- [ ] ASR/Translation services propagate speaker context unchanged.
