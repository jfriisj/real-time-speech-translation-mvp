---
ID: 029
Origin: 029
UUID: 8b4c1a2f
Status: Planned
---

# Analysis 029: Testing Infrastructure Unknowns (Host Python, pytest availability, and failing startup tests)

## Changelog
| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | User → Analyst | Deep investigation requested | Collected evidence on local test toolchain gaps (pip/pytest), identified a deterministic full-suite failure in `services/tts/tests/test_startup.py`, and documented the minimum telemetry/evidence needed to close remaining uncertainty. |
| 2026-01-28 | Analyst → Planner | Converted to Plan 029 | Marked this analysis as Planned and handed off to a concrete implementation plan to standardize on `uv` + venv for QA reproducibility. |

## Value Statement and Business Objective
**As** an operator/contributor,
**I need** the current testing infrastructure gaps and “it works on my machine” failures converted into verified causes,
**so that** QA/UAT can run a reproducible, dependency-complete validation pass for Plan 028 (and adjacent work) without being blocked by host environment variance.

## Objective
1) Identify why test execution is currently non-reproducible across environments.
2) Distinguish “missing toolchain” failures from “code regressions”.
3) Specify the smallest set of prerequisites and evidence artifacts needed to make QA runs deterministic.

## Scope
**In scope**:
- Host Python packaging constraints (pip missing / externally-managed environment).
- Repository test dependency specification (`tests/requirements.txt`) vs actual required tooling.
- Unit test failures that block full-suite runs (notably `services/tts/tests/test_startup.py`).
- Minimum integration prerequisites for smoke validation (Kafka/Schema Registry/MinIO availability).

**Out of scope**:
- Implementing fixes in production code.
- Refactoring test suites.

## Methodology
Evidence-first:
- **Verified**: confirmed by file contents or executed commands.
- **High-confidence inference**: strong linkage but missing a single discriminating datapoint.
- **Hypothesis**: plausible explanation with explicit disconfirming test and missing telemetry.

## Findings

### Verified

#### V0 — `uv` is installed and usable on the host
Evidence:
- `uv --version` returns `uv 0.9.24`.

Impact:
- The repo can standardize on a `uv`-managed workflow for test environment creation and dependency installation without requiring host `pip`.

#### V1 — Host Python lacks `pip` (cannot rely on system-wide installs)
Evidence:
- `python --version` reports Python 3.14.2.
- `python -m pip --version` fails with: `No module named pip`.

Impact:
- Any QA/runbook instruction that assumes `pip` is present on the host will fail.
- A repo-local virtual environment is a practical prerequisite for running Python tests on this host.

#### V2 — `tests/requirements.txt` does not declare pytest
Evidence:
- Current `tests/requirements.txt` contains:
  - `./shared/speech-lib`
  - `confluent-kafka>=2.3.0`
  - `numpy>=1.26.0`
  - `websockets>=12.0`
- It does **not** list `pytest`.

Impact:
- Following “install test dependencies” via `tests/requirements.txt` does not guarantee a runnable unit-test framework.
- QA execution can become environment-dependent (works only if pytest is already present by coincidence in the venv or in a different runner).

Additional note:
- A `uv`-based install step can still consume `tests/requirements.txt` (pip-compatible), but will still require `pytest` to be explicitly installed unless added to that file.

#### V3 — A repo-local venv can run the targeted Plan 028 unit tests successfully
Evidence:
- `.venv/bin/python -m pytest --version` works (pytest 9.0.2).
- Targeted Plan 028 unit tests run successfully with explicit `PYTHONPATH`:
  - `PYTHONPATH=shared/speech-lib/src:services/vad/src .venv/bin/python -m pytest shared/speech-lib/tests/test_consumer_config.py services/vad/tests/test_processing.py`
  - Result: 8 passed.

Impact:
- The Plan 028 unit-level verification is runnable and stable when executed inside a controlled virtual environment.

#### V4 — Full-suite failures exist that are unrelated to Plan 028’s consumer tuning helper
Evidence:
- `services/tts/tests/test_startup.py` expects private helpers in `tts_service.startup` (`_parse_kafka_bootstrap`, `_sanitize_url`, and direct access to `socket`/`urlopen`).
- Current `services/tts/src/tts_service/startup.py` only re-exports symbols from `speech_lib.startup` and does not expose those helpers.

Impact:
- Any “run all tests” gate will fail until test expectations and module surface are reconciled.
- This failure mode is orthogonal to Plan 028’s Kafka consumer tuning changes and can incorrectly appear as “Plan 028 broke the suite”.

### High-Confidence Inferences

#### I1 — QA reproducibility depends on specifying *two* layers: test deps and test framework
Why:
- The repo currently specifies runtime-ish dependencies for tests, but does not include the test runner itself.
- Host Python cannot install packages system-wide due to missing pip.

Confidence: Medium–High.

### Hypotheses (with disconfirming tests)

#### H1 — Multiple test execution paths exist and yield inconsistent results
Examples observed in-workspace:
- A tool-driven test runner can execute tests even when host `pytest` is missing.
- Shell-based test execution requires `.venv` + pytest installed.

Confidence: Medium.

Fastest disconfirming test:
- Define a single canonical invocation (venv-based) and verify it can run both targeted and broad suites consistently on a clean host.

Missing telemetry/evidence:
- A short “QA runner spec” (command + environment variables + dependency install steps) recorded in a single artifact per plan.

## System Weaknesses (Architecture/Process)
- Test prerequisites are under-specified (runner/framework not listed alongside dependencies).
- Full-suite failures in unrelated areas (TTS startup tests) can block unrelated plan QA, creating false coupling between work packages.
- Host environment variance is high (Python 3.14 without pip), making “works locally” ambiguous without a pinned runner.

## Instrumentation / Evidence Gaps
Normal (always-on, low-volume) for QA governance:
- Record per-plan test runner command(s) and environment prerequisites (venv path, PYTHONPATH entries, required services).

Debug (opt-in) for infra bring-up validation:
- Compose service health snapshot at time of smoke execution (container status + ports reachable).

## Analysis Recommendations (next investigative steps)
1) Decide which test runner is authoritative for QA (tool-driven runner vs venv-based `python -m pytest`), and record the exact invocation as an evidence artifact for Plan 028.
2) Determine whether `tests/requirements.txt` is intended to be “runtime deps only” or “full test stack”; validate by comparing to how CI runs tests (if CI exists).
3) Trace ownership of `services/tts/tests/test_startup.py` expectations:
   - Confirm whether the intent is to test shared `speech_lib.startup` helpers or service-level re-exports.
   - Identify the most recent change that removed/renamed `_parse_kafka_bootstrap` / `_sanitize_url` exposure.

## Appendix: uv-based QA runner sketch (for validation)
This appendix is included only to support reproducibility discussions; it is not a decision.

- Create venv: `uv venv .venv`
- Install deps: `uv pip install -r tests/requirements.txt`
- Ensure test framework present: `uv pip install pytest`
- Run: `.venv/bin/python -m pytest ...`

## Open Questions
1) Should the repository define a dedicated test requirements file (including `pytest`) separate from runtime/service dependencies?
2) What is the canonical QA execution environment: host venv, containerized tests, or a dedicated CI runner?
3) For TTS startup tests: is the contract “service module exposes helpers” or “shared-lib owns helpers and is tested directly”? (Needs decision to avoid drift.)
