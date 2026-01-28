# Analysis 016: Translation Test Infrastructure Unknowns

## Value Statement and Business Objective
**As** the architect/QA liaison for Epic 1.3,
**I need** to resolve the remaining unknowns around running the translation service tests,
**So that** we can finalize Plan 003 with confidence that diagnostics and regression suites are runnable in the target environment.

## Current Context
- The revised [Plan 003](agent-output/planning/003-translation-service-plan.md#L1) now includes a "Test Infrastructure" milestone that calls for a dedicated `translation-tests` container and Docker-based pytest run to avoid relying on the developer host.
- The diagnostic run on 2026-01-28 (referenced in [agent-output/qa/003-translation-service-qa.md](agent-output/qa/003-translation-service-qa.md)) successfully executed the translation unit tests but failed the legacy pipeline E2E smoke twice: first because `speech_lib` was not on `PYTHONPATH`, then because `fastavro` was missing, and finally because the environment has no `pip` binary (`python3 -m pip` also missing).
- Without pip or a packaged set of dependencies, the QA agent cannot finish the E2E smoke, so the translation epic remains in "In Progress" status despite unit tests passing.

## Questions to Answer (with Success Criteria)
1. **What concrete runtime/test container should we build so pytest can install and import `speech-lib`, `fastavro`, `confluent-kafka`, etc., without relying on the host having pip?**
   - Success: A `Dockerfile.test` (or a multi-stage target) is defined that installs `pip`, the necessary Python deps, and runs `pytest` against `services/translation/tests`.
2. **How do we wire this test container into Docker Compose so that Kafka and Schema Registry networks are available during the translation smoke run?**
   - Success: The plan specifies a `translation-tests` service (or `docker-compose.test.yml`) that connects to the same `kafka`, `schema-registry`, and any other relevant networks and exposes the right `KAFKA_BOOTSTRAP_SERVERS`/`SCHEMA_REGISTRY_URL` env vars.
3. **Which pytest plugins/fixtures/configs must be present so the E2E smoke and integration tests consistently rely on Avro schemas, translation topics, and correlation IDs?**
   - Success: Core requirements include `pytest` as the runner, environment gating variables (`RUN_TRANSLATION_INTEGRATION`, `RUN_TRANSLATION_MODEL_TEST`), and reusable fixtures for Kafka consumers/producers and schema registry clients; these are documented in the plan so QA/CI know how to trigger them.

## Methodology
- Re-read the latest [Plan 003](agent-output/planning/003-translation-service-plan.md) to understand the newly added test infrastructure milestone and its expectations.
- Attempted to run `tests/e2e/legacy_pipeline_smoke.py` both normally and with `PYTHONPATH` set, capturing the exact failure messages (missing `speech_lib` and `fastavro`).
- Tried to install dependencies using `pip`/`python -m pip` and observed the environment lacks pip entirely, confirming the need for a controlled container that bundles the tooling.
- Recorded the failures and dependency gaps in `agent-output/qa/003-translation-service-qa.md` and `agent-output/qa/003-translation-service-metrics.json` for traceability.

## Findings (Facts vs. Hypotheses)
1. **Fact:** The host environment has no `pip` binary (`python3 -m pip: No module named pip`), so even if we know which packages are missing (fastavro, speech_lib), we cannot install them there. (`tests/e2e/legacy_pipeline_smoke.py` and the QA report document the exact error.)
2. **Fact:** The translation tests expect `speech_lib` on the import path; the host run failed until we manually set `PYTHONPATH`, suggesting the container must either install the shared lib via editable install or ensure `/shared/speech-lib/src` is in site-packages.
3. **Fact:** The plan’s new milestone now calls for containerized smoke testing, but the plan lacks the exact docker-compose service definition, networking requirements, and dependency list that the QA run uncovered.
4. **Hypothesis:** A `translation-tests` service that shares Kafka and Schema Registry networks, installs `fastavro` and `speech-lib`, and runs `pytest tests/e2e/legacy_pipeline_smoke.py` will satisfy the success criteria; verifying this requires writing the Dockerfile/test target and seeing the smoke test succeed inside Compose.

## Recommendations
1. **Document and implement the `translation-tests` container**:
   - Build from Python 3.11/3.12 base image, install `pip`, run `pip install -r services/translation/requirements.txt` (including `shared/speech-lib` as an editable dependency), and expose a `pytest` entrypoint that sets `PYTHONPATH` appropriately.
2. **Extend Docker Compose with a `translation-tests` service** that:
   - Depends on `kafka` and `schema-registry` services and attaches to their user-defined bridge networks.
   - Sets `KAFKA_BOOTSTRAP_SERVERS`, `SCHEMA_REGISTRY_URL`, and gating env vars (`RUN_TRANSLATION_INTEGRATION=1`).
   - Mounts `shared/schemas` and the translation tests directory so they can register Avro subjects.
3. **Update Plan 003 verification section** to explicitly call out the required pytest fixtures/plugins (Kafka/SR helpers), gating env vars, and exit criteria (smoke test passes with E2E latency/timeouts) so future QA/CI engineers know how to trigger the run.
4. **Capture this investigation in the plan** by referencing the diagnostic failure logs and blocking issues so stakeholders understand why containerized testing is mandatory for the translation epic’s completion.

## Open Questions
1. Should the `translation-tests` service also run the integration tests in addition to the legacy smoke script, or keep them separate to reduce runtime? (Success: Clear policy deciding whether `RUN_TRANSLATION_INTEGRATION=1` is toggled within the same container.)
2. Do we need additional pytest fixtures for Schema Registry readiness (e.g., `wait_for_schema_registry`) in the translation tests container to avoid intermittent startup races? (Success: Documented startup checks/timeout strategy.)
3. Are there CI/CD constraints (timeout, image cache) that influence whether we should run these tests inside Docker Compose vs. a separate CI job? (Success: A decision recorded in the plan or QA work items.)
