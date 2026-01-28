---
ID: 029
Origin: 029
UUID: 8b4c1a2f
Status: Committed for Release v0.5.0
---

# Plan 029: Test Infrastructure Hardening (uv-first, reproducible QA)

## Plan Header
- **Target Release: v0.5.0**
- **Epic Alignment**: Epic 1.9.1 (Service Startup Resilience Hardening)
- **Supports**: Plan 028 QA execution and future CI determinism
- **Inputs**: `agent-output/analysis/closed/029-testing-and-ci-infrastructure-unknowns-analysis.md`
- **Critique (Resolved)**: `agent-output/critiques/closed/029-testing-infrastructure-uv-first-plan-critique.md`

## Roadmap Alignment
This plan exists to remove test-toolchain variance that currently blocks QA signoff and masks real regressions.

- **Primary dependency**: Enables repeatable QA execution for Plan 028 on externally-managed Python hosts.
- **Why Epic 1.9.1**: The immediate blocker is the TTS startup test contract drift (startup helper ownership/API surface), which is part of “Service Startup Resilience Hardening” concerns.
- **Why v0.5.0**: This is required to confidently validate v0.5.0 changes (including Plan 028) with a reproducible, dependency-complete workflow.

## Changelog
| Date | Change | Rationale |
|------|--------|-----------|
| 2026-01-28 | Initial plan | Convert Analysis 029 into an implementable work package that removes host-environment variance from QA by standardizing on `uv` + venv and aligning test dependency declarations. |
| 2026-01-28 | Revise for critique | Clarify roadmap placement, remove plan-level testing strategy, add uv fallback requirements, and define evidence/contract recording locations. |
| 2026-01-28 | Status: In Progress | Implementation started for Plan 029. |
| 2026-01-28 | Code review approved | Code review completed; ready for QA. |
| 2026-01-28 | UAT approved | UV-first QA evidence validated with documented commands and readiness for release. |
| 2026-01-28 | Committed for Release v0.5.0 | Stage 1 DevOps commit records the plan is ready for v0.5.0 packaging. |

## Value Statement and Business Objective
As an operator/contributor, I want a reproducible, dependency-complete test runner workflow that does not depend on host `pip` availability, so that QA and future CI can validate changes consistently and quickly.

## Objective
1. Make Python test execution deterministic on hosts where Python is externally-managed and `pip` may be missing.
2. Remove ambiguity between “missing tooling” failures and “real code regressions”.
3. Ensure Plan 028 (and adjacent work) has a documented, repeatable QA execution baseline.

## Scope
**In scope**:
- Standardize repo-local test environment creation and dependency installation using `uv`.
- Align test dependency declarations so the test framework (`pytest`) is always present when test deps are installed.
- Document a canonical test invocation contract (including required `PYTHONPATH` entries for local service module imports).
- Reconcile the full-suite blocker where `services/tts/tests/test_startup.py` expects helpers that `tts_service.startup` no longer exposes.

**Out of scope**:
- Adding new integration tests or expanding feature scope of any service.
- Refactoring the overall service packaging/layout beyond what is necessary for test execution.
- Designing or overhauling CI pipelines (this plan may add minimal CI prerequisites only if needed to ensure the same workflow runs in CI).

## Deliverables
- A single, documented “uv-first” workflow for creating a `.venv`, installing test dependencies, and running unit tests.
- Test dependency specs updated so `pytest` is installed as part of the standard test dependency install.
- A documented canonical `PYTHONPATH` contract (which service packages must be on-path for unit tests that import service modules), explicitly scoped to tests.
- `services/tts/tests/test_startup.py` updated to match the intended startup helper ownership and API surface (tests target the correct owning module).
- A Plan 029 QA evidence artifact capturing the exact commands/outcomes used to validate the workflow.

## Work Plan

### Milestone 1: Define the canonical test runner contract
**Objective**: Decide and document the authoritative workflow so all engineers and QA run tests the same way.

**Tasks**:
1. Select the canonical workflow shape (uv-managed venv + dependency install + pytest execution) and define which repo files are the sources of truth for dependencies.
2. Document the canonical workflow in a durable developer runbook location (prefer `docs/` plus a short README pointer).
3. Document the canonical test-only `PYTHONPATH` contract needed for service-level unit tests (at minimum: shared lib and the service under test).
4. Define the environment contract for `uv` availability:
    - **Preferred**: `uv` is required in dev/QA and CI images.
    - **Fallback** (only if needed): provide a supported alternative using `python -m venv` + `pip` inside the venv.

**Acceptance Criteria**:
- A clean host can run targeted unit tests without requiring host `pip` (using the documented preferred path, and the fallback path only if explicitly enabled).
- The workflow is documented in a stable repo location that is discoverable from the README.
- The workflow explicitly separates “test-only environment wiring” from runtime/service configuration.

**Dependencies**:
- `uv` available in dev/QA environments (verified for the current host in Analysis 029).
- If CI is in scope for validation, CI runners/images must either include `uv` or support the documented fallback path.

### Milestone 2: Align test dependency declarations
**Objective**: Ensure “install test deps” always installs a runnable test framework.

**Tasks**:
1. Decide whether to:
   - add `pytest` to `tests/requirements.txt`, or
   - introduce a separate `tests/requirements-dev.txt` (or similar) that includes `pytest` and is used by QA/CI.
2. Update documentation to reference the chosen file(s) and keep the dependency story single-path.

**Acceptance Criteria**:
- Following the documented install steps results in `pytest` being available inside `.venv`.
- The install path is consistent across local QA and any CI runner (if present).

### Milestone 3: Unblock full-suite execution (TTS startup tests)
**Objective**: Prevent unrelated test failures from blocking Plan 028 QA and future CI runs.

**Tasks**:
1. Decide the ownership contract for startup helper internals:
   - Option A: test `speech_lib.startup` directly and keep `tts_service.startup` as a re-export shim, or
   - Option B: expose the expected helper surface from `tts_service.startup` explicitly.
2. Record the decision in this plan under a “Contract Decision” subsection (so it remains visible and auditable).
3. Update `services/tts/tests/test_startup.py` (and/or its target module) to match the decided contract.

**Acceptance Criteria**:
- The TTS startup unit tests no longer fail due to missing symbols.
- The chosen ownership model is documented (to prevent future drift).

**Contract Decision (final)**:
- Chosen option: **A** — test `speech_lib.startup` directly; keep `tts_service.startup` as a thin re-export shim.
- Rationale: Reduces drift and duplicate “private helper” surfaces across services; keeps ownership of startup parsing/sanitization behavior in the shared, reusable layer.
- Contract statement: Unit tests that validate startup parsing/sanitization must target `speech_lib.startup`; service packages may re-export public startup entrypoints but do not own private helper APIs.

### Milestone 4: Validation and evidence capture
**Objective**: Ensure the new workflow is proven with minimal, high-signal checks.

**Validation Signals (high-level)**:
- Targeted unit tests for Plan 028 run successfully via the canonical uv-first workflow.
- A broader unit test run (where applicable) progresses beyond the previously known TTS startup failures.

**Artifacts**:
- Create and populate a dedicated evidence artifact: `agent-output/qa/029-testing-infrastructure-uv-first-qa.md`.
- Cross-link the evidence summary from the Plan 028 QA document (`agent-output/qa/028-kafka-consumer-group-recovery-hardening-qa.md`) only as needed.

## Risks and Mitigations
- **Risk**: Multiple dependency install paths (“pip vs uv”) persist and cause drift.
  - **Mitigation**: Make `uv` the documented default; keep a single canonical command path.
- **Risk**: `uv` is not available in some QA/CI environments.
  - **Mitigation**: Either require `uv` in those environments (preferred) or explicitly document/support a fallback path.
- **Risk**: Adding `pytest` to the wrong requirements file affects non-test consumers.
  - **Mitigation**: Choose a dedicated “dev/test” requirements file if ambiguity exists; document usage clearly.
- **Risk**: Startup helper ownership remains unclear and tests drift again.
  - **Mitigation**: Document the contract decision and keep tests aligned to the chosen surface.

## Version Management and Release Artifacts
If this plan results in user-visible workflow changes (developer/QA experience), add a short entry under v0.5.0 in `CHANGELOG.md` noting “uv-first reproducible test runner workflow” (no runtime behavior change).
