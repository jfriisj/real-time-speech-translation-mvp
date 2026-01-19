# Plan 003: Text-to-Text Translation (Translation Service)

**Plan ID**: 003
**Target Release**: v0.2.0 (Core Services)
**Epic**: 1.3 Text-to-Text Translation (Translation Service)
**Status**: Proposed
**Date**: 2026-01-15
**Dependencies**: Plan 001 (Shared Infra), Plan 002 (ASR Service)

## 1. Value Statement and Business Objective
**As a** User,
**I want** recognized text to be translated into my target language,
**So that** I can understand the content.

**Measure of Success**:
- Translation Service consumes `TextRecognizedEvent` from `speech.asr.text`.
- Translation Service produces `TextTranslatedEvent` to `speech.translation.text`.
- Check: `correlation_id` is preserved.
- Check: Produced payload contains valid translated text (`payload.text`) in the target language.

## 2. Context & Roadmap Alignment
This plan implements the second core microservice of the v0.2.0 "Walking Skeleton", enabling the end-to-end flow from Audio -> Text -> Translated Text. It relies on the contracts established in v0.1.0 and populated by the ASR service (Epic 1.2).

**Roadmap Reference**:
- **Release v0.2.0**: Core Services
- **Epic 1.3**: Text-to-Text Translation

**Architecture Guidance**:
- **Consumes**: `TextRecognizedEvent` from topic `speech.asr.text`.
- **Produces**: `TextTranslatedEvent` to topic `speech.translation.text`.
- **Schema Strategy**: `TopicNameStrategy` (default).
- **Semantics**: At-least-once (idempotency out of scope for MVP).
- **Failure Handling**: Log and drop (no error events for MVP).

## 3. Assumptions & Constraints
- **Assumption**: A simple offline translation model (e.g. `Helsinki-NLP/opus-mt-en-es` or similar lightweight model) or a deterministic mock is sufficient for MVP connectivity proof.
- **Decision (MVP)**: To minimize model weight/download issues during the "Walking Skeleton" phase, we will implement a **Deterministic Mock Interface** first. This ensures we prove the event flow (Kafka->App->Kafka) without fighting PyTorch/heavy dependencies immediately. Real model integration can happen in a follow-up task or as a config switch.
    - *Why?* The goal is structural proof (Epic 1.3) and traceability (Epic 1.4).
- **Decision (Config)**: The target language MUST be configurable via environment variable `TARGET_LANGUAGE` (default: `"es"`).
- **Decision (Failure Handling)**: "Log and drop" means the service logs the error and **commits the offset** (advances the consumer group). This prevents poison-pill messages from causing infinite retry loops in the MVP.
- **Constraint**: Must use the shared `speech-lib` for Avro/Kafka.
- **Constraint**: Must run on CPU in the standard development environment.
- **Constraint**: Payload must preserve `correlation_id`.
- **Constraint**: Input `TextRecognizedEvent` must have `payload.language` populated. If missing, log warning and default to `"en"`.

## 4. Implementation Plan

### Milestone 1: Service Initialization
**Objective**: Create service structure, dependencies, and Docker packaging.
1.  **Directory**: Create `services/translation/`.
2.  **Dependencies**: `pyproject.toml` with `speech-lib`, `confluent-kafka`. (Optional: `transformers`/`torch` if we do real model, but starting with mock structure is safer).
3.  **Dockerfile**: Similar to ASR service, Python 3.11/3.12.

### Milestone 2: Translation Core (The "Business Logic")
**Objective**: Implement the translator interface.
1.  **Interface**: Define a `Translator` protocol/class.
2.  **Implementation**: Create `MockTranslator` that simply appends `[ES]` prefix or reverses string (deterministic) to prove transformation happened.
    - *Note*: If time permits/requirements demand, a `HuggingFaceTranslator` can be added, but Mock is the MVP priority for structural proof.
3.  **Unit Tests**: Verify the logic transforms input -> output and handles empty strings.

### Milestone 3: Kafka Consumer/Producer Loop
**Objective**: Connect to the event bus.
1.  **Consumer**: Listen to `speech.asr.text` (Group ID: `translation-service`).
2.  **Handler**:
    - Deserialize `TextRecognizedEvent`.
    - Validate `payload.language` is present (default to "en" if missing/None).
    - Extract `text` and `correlation_id`.
    - Invoke `Translator`.
3.  **Producer**:
    - Construct `TextTranslatedEvent`.
    - Set `correlation_id` from input.
    - Set `payload.text` (the translated result).
    - Set `payload.source_language` (from input).
    - Set `payload.target_language` (from `TARGET_LANGUAGE` env var).
    - Publish to `speech.translation.text`.
4.  **Error Handling**: Log error details and **commit offset** to drop event and proceed. Do not crash consumer loop.

### Milestone 4: Infrastructure & Integration
**Objective**: Deploy via Compose.
1.  **Compose**: Add `translation-service` to `docker-compose.yml`.
    - Envs: `KAFKA_BOOTSTRAP_SERVERS`, `SCHEMA_REGISTRY_URL`, `TARGET_LANGUAGE=es`.
2.  **Healthcheck**: Ensure it starts after Kafka/Schema Registry.

### Milestone 5: Version Management
**Objective**: Tag and release.
1.  **Version Update**: Set version to `0.2.0` (matching release target) in `services/translation/pyproject.toml`.
2.  **CHANGELOG**: Create `services/translation/CHANGELOG.md`.

## 5. Verification Strategy (QA Handoff)
- **Unit Tests**:
    - Test `MockTranslator` logic.
    - Test Kafka consumer handler (mocking the actual consumer) to verify `correlation_id` copy.
- **Integration Tests (Smoke)**:
    - **Marked**: `@pytest.mark.integration`.
    - **Scenario**:
        1. Produce `TextRecognizedEvent` (valid sample) to `speech.asr.text`.
        2. Assert `TextTranslatedEvent` appears on `speech.translation.text`.
        3. Validate `payload.text` matches expected mock transformation.
        4. Validate `correlation_id` matches.

## 6. Risks
- **Topic Drift**: If ASR output topic changes, Translation input breaks. *Mitigation*: Hardcoded topic constants in `speech-lib` or strict adherence to plan architecture.
- **Model Bloat (if real model used)**: Downloading translation models can be heavy. *Mitigation*: Use Mock/Stub by default for MVP connectivity.

## 7. Open Questions
- None. Analysis 003 resolved configuration (env var) and failure semantics (commit-on-drop).

