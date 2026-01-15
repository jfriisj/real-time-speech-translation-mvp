# Implementation 002: Audio-to-Text Ingestion (ASR Service)

## Plan Reference
- agent-output/planning/002-asr-service-plan.md

## Date
- 2026-01-15

## Changelog
| Date | Handoff | Summary |
|------|---------|---------|
| 2026-01-15 | Implementer | Implemented ASR service (CPU-only, wav-only), Docker packaging, tests, compose integration, and benchmark tooling. |

## Implementation Summary
Implemented the ASR microservice per Plan 002 with strict payload validation, wav-only decoding, and canonical topic usage (`speech.audio.ingress` → `speech.asr.text`). Added container packaging (Python 3.11 CPU), schema loading via `SCHEMA_DIR`, and a benchmark tool to validate CPU latency. Unit/integration tests cover payload validation and end-to-end Kafka flow, aligning with the architecture’s log+drop failure handling and at-least-once semantics.

## Milestones Completed
- [x] Milestone 0: Pre-Implementation Validation
  - [x] CPU latency benchmark script added; executed in container (45s audio → ~20.47s inference)
  - [x] Model caching strategy: baked into image at build time
  - [x] Format enforcement: wav-only enforced in consumer validation
- [x] Milestone 1: Service Initialization
- [x] Milestone 2: Kafka Consumer Implementation
- [x] Milestone 3: ASR Logic & Producer Implementation
- [x] Milestone 4: Docker & Infrastructure
- [x] Milestone 5: Version Management

## Files Modified
| Path | Description | Lines |
|------|-------------|-------|
| docker-compose.yml | Added `asr-service` container | +22 |
| services/asr/README.md | ASR service setup + config | +18 |

## Files Created
| Path | Purpose |
|------|---------|
| services/asr/pyproject.toml | ASR service packaging + deps + pytest markers |
| services/asr/Dockerfile | CPU-only ASR container with baked model + schemas |
| services/asr/CHANGELOG.md | Service changelog |
| services/asr/src/asr_service/__init__.py | Package init |
| services/asr/src/asr_service/config.py | Runtime settings (env) |
| services/asr/src/asr_service/processing.py | Payload validation + wav decoding |
| services/asr/src/asr_service/transcriber.py | Whisper pipeline wrapper |
| services/asr/src/asr_service/main.py | Kafka consume/transcribe/produce loop |
| services/asr/tests/test_processing.py | Unit tests for validation/decoding |
| services/asr/tests/test_transcriber.py | Unit test for pipeline wrapper |
| services/asr/tests/test_integration_asr.py | Kafka integration test |
| services/asr/tools/benchmark_latency.py | CPU latency benchmark tool |

## Code Quality Validation
- [x] Ruff lint (selected ASR files) — no issues
- [x] Dead-code scan (vulture) — no high-confidence findings
- [x] Unit tests — passed in container (Python 3.11)
- [x] Integration tests — passed in container on compose network

## Value Statement Validation
**Original**: As a User, I want my speech audio to be captured and converted to text events, so that the system has raw material to translate.
**Delivered**: ASR service consumes `AudioInputEvent`, validates wav payloads, transcribes with Whisper, and publishes `TextRecognizedEvent` with preserved `correlation_id`.

## Test Coverage
### Unit Tests
- `services/asr/tests/test_processing.py`
- `services/asr/tests/test_transcriber.py`

### Integration Tests
- `services/asr/tests/test_integration_asr.py` (requires Kafka + Schema Registry)

## Test Execution Results
| Command | Result | Notes |
|---------|--------|-------|
| `docker run --rm --entrypoint python -e BENCH_SECONDS=45 speech-asr-service /app/services/asr/tools/benchmark_latency.py` | PASS | Inference ~20.47s for 45s audio sample |
| `docker run --rm --entrypoint bash speech-asr-service -c "pip install --no-cache-dir pytest && pytest /app/services/asr/tests -m 'not integration'"` | PASS | 6 passed, 1 deselected |
| `docker run --rm --network real-time-speech-translation-mvp_speech_net -e RUN_ASR_INTEGRATION=1 -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 -e SCHEMA_REGISTRY_URL=http://schema-registry:8081 -e SCHEMA_DIR=/app/shared/schemas/avro --entrypoint bash speech-asr-service -c "pip install --no-cache-dir pytest && pytest /app/services/asr/tests -m integration"` | PASS | 1 passed |
| `docker compose ps` | PASS | All services running (asr-service, kafka, schema-registry, zookeeper) |

## Outstanding Items
- None. All plan milestones completed and tests executed.

## Assumptions & Risks
- **Model caching**: Baked into image at build time; assumes build pipeline can download Hugging Face model.
- **Latency**: Benchmark indicates ~20.47s for 45s audio on CPU in container; acceptable for MVP but should be revalidated on target hardware.

## Next Steps
- QA validation → UAT validation.
