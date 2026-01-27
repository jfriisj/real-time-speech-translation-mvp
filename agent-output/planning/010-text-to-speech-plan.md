# Plan 010: Text-to-Speech (TTS) Service (Kokoro ONNX)

**Plan ID**: 010
**Target Release**: v0.5.0
**Epic Alignment**: Epic 1.7 Text-to-Speech (TTS) (Stable Outcome)
**Architecture**: [Findings 013](agent-output/architecture/013-tts-kokoro-onnx-architecture-findings.md) (APPROVED_WITH_CHANGES), [Findings 014](agent-output/architecture/014-tts-plan-rev16-architecture-findings.md) (APPROVED_WITH_CHANGES)
**Process Improvement**: Includes mandatory "Measurement Method" (PI-009).
**Status**: Architecture Approved - Ready for Implementation (Rev 20)

## Changelog

| Date | Event | Summary |
|------|-------|---------|
| 2026-01-25 | Initial Draft | Created plan for Epic 1.7 based on Architecture Findings 011. |
| 2026-01-25 | Revision 1-9 | Iterative refinement of schema, synthesizer pivot to Kokoro ONNX, and storage boundaries. |
| 2026-01-26 | Revision 10-13 | Alignment with Analysis 010 (Integration/Real Inference), Storage Refactor, and Voice/Speed control details. |
| 2026-01-26 | Revision 14 | ADDED "Value Validation Recovery" phase to generate missing UAT evidence. |
| 2026-01-26 | Revision 15 | REVISED "Value Validation" to remove script specifics; clarified CPU/GPU roadmap alignment. |
| 2026-01-26 | Revision 16 | REVISED based on Critique & Analysis. Removed remaining implementation/QA "HOW" (script names, dep lists). Fixed Operational Constraints defects. |
| 2026-01-26 | Revision 17 | REVISED based on Findings 014. Pin CPU-only default, add 500-char input bound, clarify ServiceLatency metric. |
| 2026-01-26 | Revision 18 | REVISED based on UAT Feedback. Relaxed blocking performance/quality gates for local CPU environment; shifted focus to functional correctness and metric observability. |
| 2026-01-26 | Revision 19 | REVISED based on Roadmap and Critique. Re-aligned Value Statement to be verifiable (Intelligible vs Natural) given the CPU-only constraint. Pinned input-bound behavior. |
| 2026-01-26 | Revision 20 | REVISED based on Analysis 010. Added explicit evidence artifacts for Intelligibility, MinIO Retention, and GPU follow-up. Refined integration failure steps. |

## Value Statement and Business Objective
As a User, I want to receive intelligible spoken audio for translated text, So that I can consume the translation without reading.

**Measure of Success**:
- **Functional Completeness**: Service consumes `TextTranslatedEvent` and emits `AudioSynthesisEvent` (Inline or URI).
- **Observability Compliance**: Service accurately logs `synthesis_latency_ms` and `RTF` for all requests.
- **Stability**: Service handles load without crashing, respecting the 500-char limit.
- **(Deferred)**: Strict quantative targets (RTF < 1.0, Latency < 2s) and subjective "naturalness" are moved to post-release benchmarking on target hardware (GPU).

### Success Metric Measurement Method
**Metric 1: Functional Output**
- **Validation**: Confirm `AudioSynthesisEvent` is produced for valid inputs.
- **Criteria**: Event structure matches schema, payload is present (bytes or URI) and is a valid WAV file.

**Metric 2: Real-Time Factor (RTF) & Latency**
- **Target**: Measure and Log Only.
- **Rationale**: Local CPU environment variability precludes strict enforcement as a release gate.
- **Dataset**: `tests/data/metrics/tts_phrases.json`.

**Metric 3: Payload Cap Compliance**
- **Validation**: Confirm events use `audio_uri` when payload size exceeds configured broker limit.

**Metric 4: Audio Quality Check**
- **Method**: Verifiable synthesis + Human Confirmation.
- **Criteria**: System produces non-zero audio bytes that are valid WAV format. Logged human verification ("intelligible") for 5 samples on reference hardware.

## Roadmap Alignment
**Plan Status**: Aligned with Epic 1.7 (Stable Outcome - CPU Focus).
**Roadmap Deviation Notes**:
- **Outcome**: Plan focuses on "Reliable Runtime (CPU)" per roadmap, but defers "Natural" subjective quality checks to a GPU-enabled environment.
- **Version**: Aligned with v0.5.0 target.
**Model Selection**: `onnx-community/Kokoro-82M-v1.0-ONNX` (per Updated Roadmap).
**Architecture Requirement**: This plan enforces a **Pluggable Synthesizer Architecture** (Factory Pattern) to satisfy the roadmap's extensibility requirement.
**CPU/GPU Strategy**:
- **Requirement**: The service implementation is designed to support both execution providers, but runtime packaging varies.
- **v0.5.0 Deliverable**: **CPU-Only Image**. The service artifact will be built and validated with `onnxruntime` (CPU). GPU support is deferred to v0.6.0 deployment profile.

## Objective
Implement the `tts-service` using `Kokoro-82M` (ONNX) to synthesize speech. Support "Dual-Mode Transport" (Inline vs URI) and propagate Speaker Context. Ensure the synthesizer implementation is pluggable.

## Architectural Contracts (Must be implemented)

### 1. Speaker Context Propagation
- **Strategy**: Inline "Reference Clip" (Bytes) & Speaker ID.
- **Synthesizer Behavior**: Use `speaker_id` to map to Style Vectors. `speaker_reference_bytes` passed for future cloning but ignored by the default Kokoro ONNX implementation.
- **Origin**: The **Ingress Gateway** is the single source of truth for originating Speaker Context.
- **Pass-through Requirement**: All intermediate services **MUST** propagate speaker context fields unchanged.
- **Privacy**: Ephemeral processing only. DO NOT persist reference clips beyond the session scope.

### 2. Transport & Failure Semantics
- **Dual-Mode**: Service MUST support switching to Object Store URI when payload exceeds safe inline limit (configurable threshold).
- **URI Failure Policy (Producer Side)**: If `audio_uri` generation fails, log error and fall back (e.g. drop or inline if small enough), but **MUST NOT crash-loop**.
- **URI Failure Policy (Consumer Side)**: Downstream consumers **MUST** handle 404/Timeout errors gracefully (log & skip).
- **Correlation**: Producer MUST key output messages by `correlation_id`.

### 3. Schema Evolution & Compatibility
- **Compatibility Mode**: `BACKWARD` (or `BACKWARD_TRANSITIVE`).
- **Optionality**: New fields (`speaker_reference_bytes`, `speaker_id`, `audio_uri`, `model_name`) MUST be optional (Union with Null).

### 4. Data Retention & Lifecycle
- **Scope**: `tts-audio` bucket objects.
- **Policy**: **Ephemeral (24 Hours)** via MinIO Lifecycle Rule.
- **Asset Caching**: Model weights and voice files MUST be cached in a deterministic path.

### 5. Observability Contract
- **Log Level**: INFO.
- **Mandatory Fields**: `correlation_id`, `model_name`, `synthesis_latency_ms`, `payload_mode`.
- **Redaction**: Logs **MUST NOT** include raw audio bytes or reference bytes.

### 6. Operational Constraints
- **Input Guards**:
    - **Max Text Length**: Service MUST enforce a hard limit of **500 characters** per input event. Exceeding events MUST be **Rejected (Soft Failure)** with a logged warning.
    - **Output Duration**: Implicitly capped by text length.
- **Execution Environment**: Service container targets **CPU Runtime** (`onnxruntime`) for v0.5.0.
- **Provider Configuration**: Code structure MUST allow for future injection of `CUDAExecutionProvider` via configuration, even if the request is ignored by the CPU-only build.
- **Speed Control (v0.5.0)**: Service MUST support a configuration-driven speed control knob (e.g., `TTS_SPEED`) that measurably alters output duration.
- **Measurement Environment**: Latency/RTF metrics are baselined on the default CPU profile.

## Context
- **Roadmap**: Epic 1.7 (Speech-to-Speech loop completion).
- **Architecture**: Option D2 (Dual-mode), Style Vector Mapping.

## Assumptions
- MinIO infrastructure is available in the stack.
- The base container image supports the necessary runtime environment (Python/ONNX).

## Constraints
- **WAV Only**: Output format MUST be `wav`.
- **Unit Test Isolation**: External I/O (inference, storage, network) MUST be mockable.
- **Model Agnostic Pipeline**: Core service orchestration MUST NOT import model-specific libraries directly.
- **Shared Library Usage**: Common storage/network adapters should reside in `speech-lib`.

## Testability Constraints
*Specific test cases reside in `agent-output/qa/`. This section defines non-negotiable testability requirements plan-side.*
- **Unit Testing**: Business logic MUST be testable with 100% isolation from external systems (MinIO, Kafka, Inference).
- **Inference Mocking**: The synthesizer factory MUST support a "Mock" or "No-Op" backend for fast unit tests.
- **Configuration**: All "tuning" knobs (Speed, Payload Thresholds, Input Limits) MUST be injectable via Environment Variables.

## Plan Steps

### 1. Shared Infrastructure & Contract Updates
**Objective**: Update schemas to support Dual-Mode transport and Speaker Context propagation.
- [x] Update `shared/schemas/avro/` `AudioSynthesisEvent` (Fields: `audio_bytes`/`audio_uri`, metadata, `model_name`).
- [x] Update upstream schemas to add optional speaker context fields.
- [x] Regenerate shared library bindings.

### 2. Infrastructure Services (MinIO)
**Objective**: Ensure Object Store availability and governance.
- [x] Provision MinIO service with `tts-audio` bucket.
- [x] Configure access credentials.
- [ ] **Verify Lifecycle**: Ensure 24h retention policy is active and **capture evidence** (CLI/UI snapshot) in `agent-output/validation/retention-proof.md`.

### 3. TTS Service Implementation
**Objective**: Create the synthesis microservice with ONNX backend.
- [x] Initialize module structure.
- [ ] **Resolve Runtime Dependencies**: Ensure Python environment and dependencies (`onnxruntime`, etc.) are compatible with the target CPU profile. (Downgrade Python version if necessary for ONNX wheel compatibility).
- [x] **Setup Test Infrastructure**: Configure mocking support for inference and storage.
- [x] **Implement Pluggable Architecture**: Define `Synthesizer` interface and Factory.
- [ ] **Implement Kokoro ONNX Backend**:
    - [x] Scaffold Synthesizer class.
    - [ ] **Data Pipeline (Real Inference)**: Integrate phonemizer and ONNX inference. **Wire `TTS_SPEED` config explicitly** to model input.
    - [ ] **Voice Mapping**: Implement `speaker_id` to Style Vector mapping with discovery and fallback logic.
    - [ ] **Observability**: Expose latency and model name metrics.
- [x] Implement Dual-Mode Producer (Upload decision logic).
- [x] Implement Consumer loop.

### 4. Integration & Deployment
**Objective**: Wire up the full Speech-to-Speech loop.
- [x] **Force URI Mode Validation**: Verify system handles payloads exceeding the inline cap by successfully uploading to MinIO and producing a valid `audio_uri` (`EXPECT_PAYLOAD_MODE=URI`).
    - **Failure Testing**: Verify behavior when `audio_uri` fetch fails (404/Timeout) is graceful/logged.

### 5. Codebase Cleanup & Refactoring
**Objective**: Remove deprecated code and promote reusable components.
- [ ] **Promote Storage Adapter**: Move local storage logic to `shared/speech-lib` (required for shared dependencies).
- [ ] **Remove Deprecated Synthesizer**: Delete legacy/mock synthesizer code in favor of the Pluggable Architecture.

### 6. Version Management
**Objective**: Prepare valid release artifacts.
- [ ] Update version strings to `0.5.0`.
- [ ] Update CHANGELOG.
- [ ] **Log Future Work**: Create a tracking document (`agent-output/planning/future/011-gpu-validation.md`) for the deferred GPU validation.

### 7. Value Validation & Evidence Collection (Recovered Phase)
**Objective**: Generate specific artifacts required to pass UAT (Availability permitting).
- [ ] **Establish Validation Tooling**: Create tooling/measurements capable of generating synthetic audio samples.
    - **Outcome 1 (Quality)**: Generate 5 WAV files from standard phrases. **Human Verification**: Record "Intelligible (Yes/No)" for each in `agent-output/validation/quality_report.md`.
    - **Outcome 2 (Performance)**: Report P50/P95 latency and RTF (n=10 loop) in `agent-output/validation/performance_report.md` (Baseline only).
    - **Outcome 3 (Control)**: measurable evidence that `TTS_SPEED` alters duration (>= 10% shift) (If supported by env).
- [ ] **Execute Validation**: Run the tooling in the CPU-supported environment and check in the resulting artifacts (if successful).

## Validation (Acceptance Criteria)
- [ ] **Real Inference**: TTS Service generates intelligible audio using Kokoro ONNX model (Functional verification; human listening deferred).
- [ ] **Evidence Artifacts**: `agent-output/validation/` contains sample WAVs (optional) and a performance report (baselined metrics).
- [ ] **Dual-Mode Transport**: Confirmed routing of large payloads via MinIO `audio_uri` and small via `audio_bytes`.
- [ ] **Observability**: Logs confirm `correlation_id`, `model_name`, and `synthesis_latency_ms`.
- [ ] **Failure Resilience**: Service withstands missing voice mappings (fallback) and storage errors (logging).
- [x] Pluggable interface allows swapping model config.
- [ ] **Audio Control**: `TTS_SPEED` configuration produces measurable duration change.

## Risks & Mitigations
- **Risk: Unverified Voice Mapping**: Kokoro's `voices.bin` structure may not directly map to `speaker_id`s as assumed.
    - **Mitigation**: Step 3 includes a discovery and fallback implementation task.
- **Risk: Speed Control Observability**: On-toggled speed control may not produce the expected duration delta.
    - **Mitigation**: Explicitly validated in Step 7 (Outcome 3).
- **Risk: Dual-Mode Failure Blindspot**: Happy-path testing may hide failure mode bugs.
    - **Mitigation**: Step 4 includes mandatory failure testing (404/Timeout).
- **Risk: MinIO Reliability**: Essential for large payloads.
    - **Mitigation**: "Dual-Mode with Fallback".
- **Risk: Integration Gaps**: Docker Compose networking may block URI fetch.
    - **Mitigation**: Explicit Integration Task in Step 4.

## Rollout & Rollback Strategy
### Rollout
1.  **Infrastructure**: Deploy MinIO with Lifecycle Rules.
2.  **Schema**: Register new forward-compatible schema.
3.  **Services**: Deploy `tts-service`. Restart dependencies.

### Rollback
- **Trigger**: P95 Synthesis Latency > 5s or Error Rate > 5%.
- **Action**: Corrective forward-fix preferred.
- **Full Revert**: Revert `tts-service` image.
