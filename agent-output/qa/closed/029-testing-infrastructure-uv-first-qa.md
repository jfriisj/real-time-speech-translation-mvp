---
ID: 029
Origin: 029
UUID: 8b4c1a2f
Status: Committed for Release v0.5.0
---

# QA Report: Plan 029: Test Infrastructure Hardening (uv-first, reproducible QA)

**Plan Reference**: agent-output/planning/closed/029-testing-infrastructure-uv-first-plan.md
**Implementation Reference**: agent-output/implementation/closed/029-testing-infrastructure-uv-first-implementation.md
**QA Status**: QA Complete
**QA Specialist**: qa

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|----------------|---------|---------|
| 2026-01-28 | Implementer | Implementation ready for QA testing | Documented the uv-first runbook, dependency alignment, and startup contract so QA can validate the canonical workflow. |
| 2026-01-28 | QA | Confirm uv-first workflow | Recreated the uv-managed `.venv`, installed dependencies through `uv pip`, and executed the startup + consumer config tests plus the full pytest suite to prove the documented commands work. |
| 2026-01-28 | DevOps | Record commitment | QA evidence artifact closed as part of Stage 1 release processing for v0.5.0. |

## Timeline
- **Test Strategy Started**: 2026-01-28 15:50 UTC
- **Test Strategy Completed**: 2026-01-28 16:05 UTC
- **Implementation Received**: 2026-01-28 15:30 UTC (per implementation doc)
- **Testing Started**: 2026-01-28 16:10 UTC
- **Testing Completed**: 2026-01-28 16:30 UTC
- **Final Status**: QA Complete

## Test Strategy (Pre-Implementation)
QA will confirm that the uv-first workflow and the associated documentation faithfully produce a deterministic test environment on a clean host and that the wider suite is unblocked by the shared startup and consumer helpers. This plan has two visible failure modes: missing dependencies (pytest, huggingface-hub, soundfile, librosa) and startup tests running against stale service exports. The new `docs/test-runner.md` runbook plus the shared consumer config/telemetry updates are the artifacts QA must exercise to ensure the developer/QA story is reproducible.

### Testing Infrastructure Requirements
**Test Frameworks Needed**:
- pytest (workspace default; version >=9.0 to match tests/pipeline)

**Testing Libraries Needed**:
- uv (verified as available: `uv --version` reported 0.9.24 and was used for every workflow step below)
- huggingface-hub, soundfile, librosa (declared in `tests/requirements.txt`)
- soundfile’s native dependencies (ensure `libsndfile` is available on the host)

**Configuration Files Needed**:
- docs/test-runner.md (authoritative uv-first workflow + fallback contract)
- tests/requirements.txt (source of truth for test dependencies, now including pytest + extras)
- pytest.ini (import-mode=importlib to avoid name collisions and respect the canonical `PYTHONPATH` contract)

**Build Tooling Changes Needed**:
- None; QA uses the same repo-local Python created by `uv venv .venv` and `uv pip install`, demonstrating the uv-first story runs end-to-end.

**Dependencies to Install**:
```bash
uv venv .venv --clear
uv pip install -r tests/requirements.txt
```
The uv-first workflow suffices for this repo; the documented fallback remains optional for environments where uv cannot be installed.

### Required Unit Tests
- Run `PYTHONPATH=shared/speech-lib/src:services/tts/src .venv/bin/python -m pytest services/tts/tests/test_startup.py` to confirm the TTS startup helpers now rely on `speech_lib.startup` and resolve without missing exports.
- Run `PYTHONPATH=shared/speech-lib/src .venv/bin/python -m pytest shared/speech-lib/tests/test_consumer_config.py` to ensure the new consumer tuning helper validates defaults and bounds.
- Run `PYTHONPATH=shared/speech-lib/src:services/vad/src .venv/bin/python -m pytest shared/speech-lib/tests/test_consumer_config.py services/vad/tests/test_processing.py` (or similar consumer config-sensitive tests) to prove the service wiring accepts the new configuration fields.

### Required Integration Tests
- Run the full suite via `PYTHONPATH=shared/speech-lib/src:services/asr/src:services/translation/src:services/tts/src:services/vad/src:services/gateway/src .venv/bin/python -m pytest` and verify the prior good run (85 passed, 3 skipped) reproduces successfully with the documented setup.
- Re-running the suite via the fallback (non-uv) path is optional; uv is present on the host, so all commands below used uv-managed tooling to prove the canonical workflow works.

### Acceptance Criteria
- The preferred uv-first path boots a .venv, installs dependencies (pytest, huggingface-hub, soundfile, librosa), and exposes `pytest` without relying on host `pip`.
- The documented `PYTHONPATH` contract (shared lib + service under test) lets `services/tts/tests/test_startup.py` and the full suite resolve their imports via `speech_lib.startup` without `ModuleNotFoundError`.
- The documented workflow (`docs/test-runner.md`) remains discoverable (linked from README) and matches the commands QA executes.
- Full-suite pytest run completes with the expected pass/skip counts, and the consumer config helper tests still pass after the dependency installs.

- Added `docs/test-runner.md` to describe the uv-first workflow plus the fallback, and surfaced the document via the README so QA knows where to start.
- Updated `tests/requirements.txt` with pytest, huggingface-hub, soundfile, and librosa so `uv pip install` installs a runnable stack.
- Adjusted all service startup tests (including TTS) to reference `speech_lib.startup`, matching the new contract and unblocking the full suite.
- Introduced `shared/speech-lib/src/speech_lib/consumer_config.py` (with unit tests) to centralize Kafka consumer tuning validation and telemetry.
- Added `pytest.ini` import-mode tweaks, lazy-loaded transformers in the ASR transcriber, and fixed the shared fake consumer tests so they match `poll(timeout=...)` signatures used in the suite.
- Verified the documented workflow end-to-end with uv-managed commands (see Test Execution Results below) so the canonical path really works on a clean host.

## Test Coverage Analysis
- To be completed after QA executes the targeted unit and full-suite tests. Reference the implementation doc for the latest run counts until QA supersedes them.

## Test Execution Results
### Unit Tests
- **Command**: `PYTHONPATH=shared/speech-lib/src:services/tts/src .venv/bin/python -m pytest services/tts/tests/test_startup.py`
	- **Status**: PASS (5/5)
	- **Output Summary**: Startup helpers under `speech_lib.startup` resolved via the uv-first environment.
- **Command**: `PYTHONPATH=shared/speech-lib/src:services/vad/src .venv/bin/python -m pytest shared/speech-lib/tests/test_consumer_config.py services/vad/tests/test_processing.py`
	- **Status**: PASS (8/8)
	- **Output Summary**: Shared consumer tuning validation plus VAD wiring succeed with the new config fields.

### Integration Tests
- **Command**: `PYTHONPATH=shared/speech-lib/src:services/asr/src:services/translation/src:services/tts/src:services/vad/src:services/gateway/src .venv/bin/python -m pytest`
	- **Status**: PASS (85 passed, 3 skipped)
	- **Output Summary**: Full suite processed with the documented `PYTHONPATH` contract and uv-managed environment; repeated the previously observed pass/skip counts.

### Notes
- Every command above used the uv-managed `.venv` and `uv pip` installs, confirming that uv is available and sufficient for the canonical workflow; no fallback steps were required on this host.
