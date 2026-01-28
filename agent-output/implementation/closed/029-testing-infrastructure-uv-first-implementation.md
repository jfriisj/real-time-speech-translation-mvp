---
ID: 029
Origin: 029
UUID: 8b4c1a2f
Status: Committed for Release v0.5.0
---

# Implementation 029: Test Infrastructure Hardening (uv-first, reproducible QA)

## Plan Reference
- Plan: `agent-output/planning/closed/029-testing-infrastructure-uv-first-plan.md`

## Date
- 2026-01-28

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-28 | Begin implementation | Initialized implementation document for Plan 029. |
| 2026-01-28 | Stage 1 commit | Marked implementation as committed for v0.5.0 release readiness. |

## Implementation Summary

Implemented the uv-first test runner runbook, ensured pytest is part of test dependencies, and aligned TTS startup tests with the shared `speech_lib.startup` contract. Updated the README to point to the runbook and finalized the Plan 029 contract decision label cleanup. QA evidence capture remains pending and must be recorded by QA in the dedicated QA artifact.

## Milestones Completed

- [x] Milestone 1: Canonical test runner contract documented
- [x] Milestone 2: Test dependency declarations aligned
- [x] Milestone 3: TTS startup tests unblocked
- [ ] Milestone 4: Validation evidence captured

## Files Modified

| Path | Description | Lines |
|------|-------------|-------|
| tests/requirements.txt | Added pytest + unit-test deps (huggingface-hub, soundfile, librosa) | +4 |
| services/tts/tests/test_startup.py | Targeted shared startup module per contract | -1/+1 |
| services/asr/tests/test_startup.py | Targeted shared startup module per contract | -1/+1 |
| services/gateway/tests/test_startup.py | Targeted shared startup module per contract | -1/+1 |
| services/translation/tests/test_startup.py | Targeted shared startup module per contract | -1/+1 |
| services/vad/tests/test_startup.py | Targeted shared startup module per contract | -1/+1 |
| README.md | Added test runner link | +4 |
| agent-output/planning/closed/029-testing-infrastructure-uv-first-plan.md | Status set to In Progress; contract decision label cleanup | +2/-1 |
| services/asr/src/asr_service/transcriber.py | Lazy import of transformers for optional pipeline factory | +8/-1 |
| pytest.ini | Use importlib import mode to avoid test name collisions | +1 |
| shared/speech-lib/tests/test_consumer.py | Align fake consumer poll signature with timeout keyword | -1/+1 |

## Files Created

| Path | Purpose |
|------|---------|
| docs/test-runner.md | Canonical uv-first test runner workflow and fallback | 

## Code Quality Validation

- [ ] Lint/format checks run
- [x] Unit tests run
- [ ] Integration/E2E tests run (if applicable)
- [ ] Compatibility notes recorded

## Value Statement Validation

**Original**: As an operator/contributor, I want a reproducible, dependency-complete test runner workflow that does not depend on host `pip` availability, so that QA and future CI can validate changes consistently and quickly.

**Implementation delivers**: Provides a documented, uv-first test workflow and ensures test dependencies include pytest, reducing host variability for QA and CI validation. TTS startup tests now align with the shared startup contract to avoid suite-blocking mismatches.

## TDD Compliance

| Function/Class | Test File | Test Written First? | Failure Verified? | Failure Reason | Pass After Impl? |
|----------------|-----------|---------------------|-------------------|----------------|------------------|
| None (no new functions/classes) | N/A | N/A | N/A | N/A | N/A |

## Test Coverage

- Unit: Not yet executed in this implementation pass.
- Integration: Not yet executed in this implementation pass.

## Test Execution Results

| Date | Command | Result | Notes |
|------|---------|--------|-------|
| 2026-01-28 | `PYTHONPATH=shared/speech-lib/src:services/tts/src .venv/bin/python -m pytest services/tts/tests/test_startup.py` | Pass (5/5) | uv venv recreated with `uv venv .venv --clear` and deps installed from `tests/requirements.txt`. |
| 2026-01-28 | `PYTHONPATH=shared/speech-lib/src:services/tts/src .venv/bin/python -m pytest services/tts/tests` | Fail (collection) | Missing deps: `huggingface_hub`, then `soundfile`. |
| 2026-01-28 | `PYTHONPATH=shared/speech-lib/src:services/tts/src .venv/bin/python -m pytest services/tts/tests` | Pass (22/22) | Added `huggingface-hub` + `soundfile` to test requirements and reinstalled.
| 2026-01-28 | `PYTHONPATH=shared/speech-lib/src:services/asr/src:services/translation/src:services/tts/src:services/vad/src:services/gateway/src .venv/bin/python -m pytest` | Fail (collection) | Missing deps (`librosa`), startup tests imported service modules without startup re-exports, test module name collisions, and fake consumer poll signature mismatch. |
| 2026-01-28 | `PYTHONPATH=shared/speech-lib/src:services/asr/src:services/translation/src:services/tts/src:services/vad/src:services/gateway/src .venv/bin/python -m pytest` | Pass (85/88, 3 skipped) | Added `librosa` to test deps, aligned startup tests to `speech_lib.startup`, set pytest import mode to importlib, and fixed fake consumer poll signature.

## Outstanding Items

- Record QA evidence in `agent-output/qa/029-testing-infrastructure-uv-first-qa.md` (QA-owned artifact).
- Determine whether CI images must include `uv` or rely on the documented fallback path.
- QA/UAT prompt files were not found at `/home/jonfriis/.config/Code/User/prompts/`; proceed once available or confirm alternate location.

## Next Steps

- Run validation checks and capture evidence in `agent-output/qa/029-testing-infrastructure-uv-first-qa.md`
- Hand off to QA for verification
