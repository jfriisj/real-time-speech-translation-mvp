# Plan 025: Service Startup Resilience (Epic 1.9)

**ID**: 025
**Feature Slug**: service-startup-resilience
**Target Release**: v0.4.1 (Resilience Patch)
**Epic Alignment**: Epic 1.9 (Service Startup Resilience)  
**Status**: Revised

## Changelog
| Date | Agent | Request | Summary |
|------|-------|---------|---------|
| 2026-01-28 | Planner | Create Plan | Initial plan for platform-wide startup resilience (supersedes Plan 011). |
| 2026-01-28 | Planner | Revise Success Metrics | Relaxed strict "10-run" requirement in favor of single-pass verification with unit test coverage, based on UAT feedback. |

## 1. Value Statement and Business Objective

**As an** Operator/Developer,
**I want** all microservices (Gateway, VAD, ASR, Translation, TTS) to explicitly wait for their infrastructure dependencies (Schema Registry, Kafka) during startup,
**So that** the platform initializes predictably without race conditions or crash loops, enabling reliable end-to-end testing and stable development.

**Success Metric**: `docker compose up` from a cold state results in a converged system where the 5 target services (gateway, vad, asr, translation, tts) reach `running` state with zero restarts within 90 seconds.
**Constraint**: Deterministic multi-run verification (10x convergence) is relaxed for v0.4.1 to reduce release friction. Full statistical stability proof is deferred to **Epic 1.9.1 (Resilience hardening)**.

## 2. Context

- **Problem**: Current services attempt to register schemas or connect to Kafka immediately on startup. If infrastructure containers are simpler/slower to start, application services crash (SystemExit or unhandled exception), leading to "CrashLoopBackOff" or silent failures.
- **Architectural Constraints** (from `025` findings):
  - **No Shared-Lib SDK**: Resilience logic must live at the service application boundary, not inside `speech-lib`.
  - **Bounded Waits**: Services must fail-fast (non-zero exit) after a configured timeout (default 60s) rather than hanging indefinitely.
  - **Consistency**: All services must use the same environment variables and log patterns.
- **Scope**:
  - **Services**: `gateway-service`, `vad-service`, `asr-service`, `translation-service`, `tts-service`.
  - **Dependencies**: Schema Registry (HTTP), Kafka (Broker TCP).

## 3. Deliverables

- **Service-Side Readiness Gates**: Gateway, VAD, ASR, Translation, and TTS services wait for Schema Registry and Kafka.
- **Standardized Config Contract**: Consistent `STARTUP_*` environment variables across all services.
- **Verification Script**: Automated tool to confirm container stability after cold start.
- **Updated Infrastructure Config**: `docker-compose.yml` leveraging native healthchecks for improved ordering.

## 4. Assumptions & Open Questions

- **Assumption**: A simple TCP connect check is sufficient for Kafka "readiness" (we don't need to check cluster metadata availability, just reachability).
- **Assumption**: Schema Registry `/subjects` endpoint return 200 OK is sufficient for readiness.
- **Decision**: We will use standard logging (INFO for waiting, ERROR for timeout) to allow existing log scrapers to see status.

## 5. Plan

### Work Package 1: Infrastructure Readiness Gates (Docker Compose)
**Objective**: Optimize local development startup order using Compose native healthchecks.
**Files**: `docker-compose.yml`
**Constraint**: Do NOT add new OS packages (e.g. `curl`, `nc`) to production images just for healthchecks. Use built-in tools or shell primitives if possible.

1.  **Schema Registry Healthcheck**:
    -   Keep existing Schema Registry healthcheck (uses `bash` + `/dev/tcp` check) unless broken. Do NOT force usage of `curl`.
2.  **Kafka Healthcheck**:
    -   Keep Kafka dependency as `condition: service_started` for now (Kafka healthcheck is tricky without `netcat`/`kcat`).
    -   Rely primarily on **Service-Side Gating** (WP2) for Kafka readiness.
3.  **Service Dependencies**:
    -   Update all services (`gateway`, `vad`, `asr`, `translation`, `tts`) to use `depends_on: { schema-registry: { condition: service_healthy }, kafka: { condition: service_started } }`.

### Work Package 2: Standardize Service Startup Logic (Implementation Pattern)
**Objective**: Implement the "Bounded Wait" pattern in strict Python code (portable beyond Compose).
**Pattern Definition**:
-   **Config Contract (Env Vars)**:
    -   `STARTUP_MAX_WAIT_SECONDS` (default=60)
    -   `STARTUP_INITIAL_BACKOFF_SECONDS` (default=1)
    -   `STARTUP_MAX_BACKOFF_SECONDS` (default=5)
    -   `STARTUP_ATTEMPT_TIMEOUT_SECONDS` (default=2)
-   **Method**: Implement bounded checks for HTTP endpoints and TCP ports.
-   **Readiness Phases**:
    1.  Log entry into readiness check phase.
    2.  Check Kafka Broker (TCP Connect).
    3.  Log successful Kafka connection.
    4.  Check Schema Registry (HTTP GET subject list or root).
    5.  Log successful Schema Registry connection.
    6.  Proceed to Main Loop.
-   **Security**:
    -   **URL Sanitization**: Logs MUST NOT output URLs containing credentials (e.g. `http://user:pass@host`). Log only `host:port`.
    -   **Safe Backoff**: Use truncated exponential backoff with **jitter** to prevent synchronized "thundering herd" connection storms.
    -   **Bounded Timeouts**: Each network attempt must have a short per-operation timeout (e.g. 2s connect/read) to prevent hanging the main loop.

**Tasks by Service**:
1.  **Translation Service**:
    -   Implement pattern in `main.py` (before `SchemaRegistryClient` init).
    -   Check Schema Registry URL and Kafka bootstrap servers.
2.  **ASR Service**:
    -   Implement pattern in `main.py`.
3.  **VAD Service**:
    -   Implement pattern in `main.py`.
4.  **Gateway Service**:
    -   Implement pattern in `main.py`.
5.  **TTS Service**:
    -   Implement pattern in `main.py` (ensure this is part of the scaffold).

*Note: Since we cannot use a shared-lib helper, this code will be duplicated/adapted per service. This is an accepted architectural trade-off to avoid coupling.*

### Work Package 3: Verification Script
**Objective**: Verify the fix via reproducible integration script.

1.  Create `tests/infra/verify_startup_resilience.py` (or shell script).
2.  Logic:
    -   Start `docker compose up -d`.
    -   Wait 30s.
    -   Check `docker ps` to ensure no containers are `Restarting` or `Exited`.
    -   Check logs for "Dependency ready" messages.

## 6. Validation & Acceptance Criteria

**Measurement Methods**:
- **Stable System**: `docker ps` confirms the 5 target services have `State=running` and `Restarts=0`.
- **Log Evidence**: Service logs contain text matching the readiness phases (e.g., "Kafka ready", "Schema Registry ready").
- **Jitter Behavior**: Code review or inspection confirms backoff logic calls random number generator.

**Criteria**:
-   [ ] **Configuration Support**: `STARTUP_MAX_WAIT_SECONDS` and backoff env vars are respected; defaults apply if missing.
-   [ ] **Security Compliance**: Startup logs do not contain raw URLs with credentials.
-   [ ] **Convergence**: `docker compose up` results in a Stable System within 90 seconds.
-   [ ] **Fail-Fast**: If dependencies are permanently down/unreachable, services exit with non-zero code after `STARTUP_MAX_WAIT_SECONDS`.
-   [ ] **No Jitter-less Retries**: Backoff logic incorporates randomization.

## 7. Version Management

-   **Version**: v0.4.1
-   **Artifacts**:
    -   `CHANGELOG.md` updated.
    -   No shared-lib version bump required (logic is internal to services).

## 8. Rollback Plan

-   If services fail to start due to strict checks, increase `STARTUP_MAX_WAIT_SECONDS` via `.env`.
-   If bug in wait logic prevents startup, revert to previous `main.py` logic (fail-fast without wait) and rely on Compose restart policy.
