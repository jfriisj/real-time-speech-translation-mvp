# Test Runner Workflow (uv-first)

This repo standardizes on a **uv-first** workflow for reproducible, dependency-complete test execution. The workflow is **test-only** and does not change runtime/service configuration.

## Preferred workflow (uv required)

1. Create a local virtual environment:

- `uv venv .venv`

2. Install test dependencies:

- `uv pip install -r tests/requirements.txt`

3. Run tests using the repo-local Python:

- `.venv/bin/python -m pytest`

## Test-only `PYTHONPATH` contract

Service-level unit tests may require module imports from the shared library and the service under test. Use a **test-only** `PYTHONPATH` when invoking tests:

- Shared lib: `shared/speech-lib/src`
- Service under test: `services/<service>/src`

**Example (TTS tests):**

- `PYTHONPATH=shared/speech-lib/src:services/tts/src .venv/bin/python -m pytest services/tts/tests`

> This contract is for tests only. Runtime services must rely on package/module resolution provided by their own deployment environments.

## Fallback workflow (only if uv is unavailable)

If `uv` is not available in a given environment, the supported fallback is a standard venv + pip inside the venv:

1. `python -m venv .venv`
2. `.venv/bin/pip install -r tests/requirements.txt`
3. `.venv/bin/python -m pytest`

If a CI runner is used, prefer installing `uv` in the image and use the uv-first path for deterministic installs.
