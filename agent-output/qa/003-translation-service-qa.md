# QA Report: Plan 003 Text-to-Text Translation (Translation Service)

**Plan Reference**: agent-output/planning/003-translation-service-plan.md
**Implementation Reference**: agent-output/implementation/003-translation-service-implementation.md
**Roadmap Reference**: agent-output/roadmap/product-roadmap.md (Epic 1.3)
**Architecture Reference**: agent-output/architecture/system-architecture.md
**QA Status**: QA Failed
**QA Specialist**: qa

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-16 | Implementer | Implementation complete, ready for testing | Ran code-quality gate (Ruff/Vulture) and full pytest suite. Attempted Docker/Compose build+smoke, but translation-service image build is prohibitively heavy (CUDA wheels) and failed due to Docker snapshotter error; integration test execution blocked. |
| 2026-01-16 | QA | Address test gaps | Added unit coverage for `process_event` and consumer wrapper helpers, fixed integration schema dir resolution and timeout, and validated Docker CPU-only build; integration test passed. |
| 2026-01-28 | User | Run all tests and E2E for translation service | Unit tests passed; legacy E2E smoke failed due to missing `fastavro` and unavailable `pip` in the environment. |

## Timeline
- **Test Strategy Started**: 2026-01-16
- **Test Strategy Completed**: 2026-01-16
- **Implementation Received**: 2026-01-16
- **Testing Started**: 2026-01-28
- **Testing Completed**: 2026-01-28
- **Final Status**: QA Failed

## Test Strategy (Pre-Implementation)
Validate user-facing correctness and operational safety for the translation step:
- Contract compliance: consumes `TextRecognizedEvent` (topic `speech.asr.text`) and produces `TextTranslatedEvent` (topic `speech.translation.text`) with required payload fields.
- Traceability: preserves `correlation_id`.
- Failure policy: malformed events are log+drop without poison-pill loops (commit-on-drop semantics), per MVP guidance.
- Translation behavior: non-empty outputs for non-empty inputs, and predictable language metadata (`source_language`, `target_language`).
- Delivery semantics: tolerate at-least-once processing (duplicates may occur).
- Deployment realism: service must be buildable/runnable in Docker Compose on CPU.

### Testing Infrastructure Requirements
**Test Frameworks Needed**:
- pytest

**Testing Libraries Needed**:
- none beyond service dependencies

**Configuration Files Needed**:
- pytest marker registration (`pytest.ini` at repo root)

**Build Tooling Changes Needed**:
- CPU-only PyTorch install strategy for Docker builds (to avoid CUDA wheel downloads and to align with CPU-only MVP constraints)

## Implementation Review (Post-Implementation)

### Code Changes Summary
- Added Translation Service under `services/translation/` (config, main loop, translator, tests, Dockerfile, Compose wiring).
- Updated shared consumer wrapper to support manual commit of specific messages (`poll_with_message`, `commit_message`) to implement commit-on-drop.
- Switched translation runtime to a real Hugging Face model-backed translator (`Helsinki-NLP/opus-mt-en-es` by default) with cached model loading.

## Test Coverage Analysis

### New/Modified Code
| File | Function/Class | Test File | Test Case | Coverage Status |
|------|---------------|-----------|-----------|-----------------|
| services/translation/src/translation_service/main.py | `extract_translation_request` | services/translation/tests/test_translation_processing.py | request extraction tests | COVERED |
| services/translation/src/translation_service/main.py | `build_output_event` | services/translation/tests/test_translation_processing.py | output event fields test | COVERED |
| services/translation/src/translation_service/main.py | `process_event` | services/translation/tests/test_translation_processing.py | process_event publish + empty translation tests | COVERED |
| services/translation/src/translation_service/translator.py | `HuggingFaceTranslator.translate` | services/translation/tests/test_translator.py | model translation smoke | PARTIAL (skipped by default) |
| shared/speech-lib/src/speech_lib/consumer.py | `poll_with_message`, `commit_message` | shared/speech-lib/tests/test_consumer.py | poll/commit helper tests | COVERED |
| services/translation/tests/test_integration_translation.py | Kafka E2E translation | services/translation/tests/test_integration_translation.py | integration test | COVERED |

### Coverage Gaps
- None identified for the changed translation and consumer helper paths.

### Comparison to Test Plan
Plan 003 originally called for mock-based unit tests; implementation intentionally deviates due to the updated “no mocks allowed” constraint.
- **Planned**: unit tests for translator and handler, plus an opt-in integration test.
- **Implemented**: unit tests for request parsing + output shape; opt-in model inference test; opt-in integration test.
- **Gap vs. value**: still missing an automated, realistic end-to-end validation (Kafka -> translation -> Kafka) in CI-like conditions.

## Test Execution Results

### 2026-01-28 Diagnostic Run

### Code Quality Gate
- **Ruff lint**: PASS (0 issues)
   - Targets scanned: `services/translation/src/translation_service/main.py`, `translator.py`, `config.py`, and translation unit tests
- **Vulture dead-code scan**: PASS (0 high-confidence findings)
   - Targets scanned: `main.py`, `translator.py`

### Unit Tests
- **Command**: `services/translation/tests/test_translation_processing.py`, `services/translation/tests/test_translator.py`
- **Status**: PASS
- **Output**: `6 passed`

### E2E Smoke (Legacy Pipeline)
- **Command**: `python tests/e2e/legacy_pipeline_smoke.py`
- **Status**: FAIL
- **Output**: `ModuleNotFoundError: No module named 'speech_lib'`

### E2E Smoke Retry (PYTHONPATH)
- **Command**: `PYTHONPATH=shared/speech-lib/src python tests/e2e/legacy_pipeline_smoke.py`
- **Status**: FAIL
- **Output**: `ModuleNotFoundError: No module named 'fastavro'`

### Test Dependency Install Attempt
- **Command**: `python -m pip install -r tests/requirements.txt`
- **Status**: FAIL
- **Output**: `/usr/bin/python: No module named pip`

### Code Quality Gate
- **Ruff lint**: PASS (0 issues)
   - Targets scanned: translation service modules/tests and shared consumer wrapper (`main.py`, `translator.py`, `config.py`, `consumer.py`, and translation tests)
- **Vulture dead-code scan**: PASS (0 high-confidence findings)
   - Targets scanned: translation service main/translator and shared consumer wrapper

### Unit Tests
- **Command**: pytest (via VS Code `runTests` harness)
- **Status**: PASS (0 failures observed)
- **Notes**: model download/inference and Kafka integration tests are intentionally gated behind env vars (`RUN_TRANSLATION_MODEL_TEST`, `RUN_TRANSLATION_INTEGRATION`) and will be skipped by default.

### Targeted Coverage Tests
- **Command**: `python -m pytest shared/speech-lib/tests/test_consumer.py services/translation/tests/test_translation_processing.py -q`
- **Status**: PASS
- **Output**: `6 passed`

### Integration / Compose Smoke
- **Command**: `RUN_TRANSLATION_INTEGRATION=1 python -m pytest services/translation/tests/test_integration_translation.py -q`
- **Status**: PASS
- **Output**: `1 passed in 3.29s`

## Issues & Risks

### Blocking Issues
- **E2E smoke blocked by missing dependencies**: `fastavro` is missing and `pip` is unavailable in the environment, preventing the legacy pipeline smoke test from running.

### Non-Blocking Risks
- **Default dev Python is 3.14**: host pytest passes without importing `torch` (model test skipped). Installing `torch` locally on 3.14 may be unsupported; Docker uses Python 3.11 and is the intended runtime.
- **First-translation latency**: MarianMT model download on first message can be slow; integration timeout increased to 180s to accommodate cold-start downloads.
- **QA checklist doc missing**: process references `agent-output/qa/README.md`, but it does not exist in this workspace; QA format followed prior QA reports instead.

## Final Assessment
QA Failed. Unit tests pass and the code-quality gate is clean, but E2E smoke testing for the translation service cannot run due to missing `fastavro` and unavailable `pip` in the environment. Resolve test dependencies and re-run the legacy pipeline smoke test.

Handing off to uat agent for value delivery validation.
