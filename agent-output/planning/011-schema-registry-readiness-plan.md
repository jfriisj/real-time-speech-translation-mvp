# Plan 011: Schema Registry Readiness & Service Resilience

**Target Release**: v0.4.1 (Patch / Stability)
**Epic Alignment**: Unblocks verification of Epic 1.7 (TTS) and supports Epic 1.8 (Persistence) by ensuring pipeline stability.
**Status**: Proposed

## Changelog
| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-28 | Planner | Create Plan | Initial plan for schema registry readiness fix. |

## 1. Value Statement and Business Objective

**As a** System Operator / Developer,
**I want** the microservices (Translation, TTS, etc.) to wait gracefully for the Schema Registry to become available during startup,
**So that** the entire pipeline comes up reliably without race conditions, preventing "silent failures" where services exit before the registry is ready and causing E2E tests to timeout.

## 2. Context

-   **Problem**: Analysis (`011-schema-registry-readiness-analysis.md`) confirmed `translation-service` crashes immediately if `schema-registry` is not yet available on port 8081. `docker-compose` `depends_on` is insufficient.
-   **Impact**: Downstream `TextTranslatedEvent` is never emitted, causing TTS verification and E2E smoke tests (`tests/e2e/tts_pipeline_smoke.py`) to fail with timeouts.
-   **Architecture**:
    -   `shared-lib`: Contains `SchemaRegistryClient` which currently raises unhandled exceptions on connection failure.
    -   `translation-service`: Calls registration synchronously before the main loop.
    -   Other services (`asr`, `tts`, `gateway`) likely share this vulnerability.

## 3. Deliverables

-   **Docker Compose Healthchecks**: `schema-registry` configured with a robust healthcheck; services configured to wait for it.
-   **Resilient `translation-service`**: Startup logic that explicitly waits for Schema Registry availability (with timeout) before crashing.
-   **Verified E2E**: Successful run of `tests/e2e/tts_pipeline_smoke.py` indicating the pipeline is flowing.

## 4. Contract Decisions

### 4.1 Resilience Contract
-   **Service Boundary Responsibility**: Retry/backoff policies for infrastructure readiness MUST reside in the service application layer (or orchestration), NOT in the shared contract library.
-   **Bounded Waits**: Services MUST NOT wait indefinitely. A hard timeout (default 60s) is required to allow fail-fast behavior if infrastructure is permanently broken.

### 4.2 Observability Contract
-   No changes to tracing/logging schemas.
-   Startup logs must clearly indicate "Waiting for Schema Registry..." vs "Connected".

## 5. Work Packages

### WP1: Add Schema Registry Healthcheck for Local Dev (Infrastructure)
**Objective**: Ensure `schema-registry` container reports healthy only when API is reachable.
**Files**: `docker-compose.yml`
**Tasks**:
1. Add `healthcheck` to `schema-registry` service in `docker-compose.yml`.
   - Command: `curl --fail --silent http://localhost:8081/subjects || exit 1`
   - Interval: 10s, Timeout: 5s, Retries: 5, Start period: 10s.
2. Update `translation-service` (and others via WP3) to depend on `schema-registry` condition `service_healthy`.
   - Change `depends_on` from list to long syntax with `condition: service_healthy`.

### WP2: Implement Bounded Service Startup Wait (Translation Service)
**Objective**: Ensure Translation Service waits for registry readiness within the service logic (for robustness outside Compose).
**Files**: `services/translation/src/translation_service/main.py`
**Tasks**:
1. Keep `SchemaRegistryClient` in `shared-lib` **unchanged** (do not add retry logic there).
2. Create a helper function `wait_for_schema_registry(registry_url: str, timeout: float)` inside `translation_service/main.py` (or a local util).
   - Loop `requests.get(url)` with truncated exponential backoff (1s, 2s, 4s...) until success or timeout (default 60s).
   - Log at INFO: "Waiting for Schema Registry..."
   - Log at ERROR and raise SystemExit/Fatal if timeout reached.
3. Call this helper in `main()` *before* instantiating `SchemaRegistryClient` or calling `register_schemas`.

### WP3: Audit Other Services (Optional / Fast Follow)
**Objective**: Apply the same fix to other services.
**Files**: `services/asr/...`, `services/tts/...`, `services/gateway/...`, `docker-compose.yml`
**Tasks**:
1. Update `docker-compose.yml` for `asr-service`, `tts-service`, `gateway-service` to depend on `schema-registry` condition `service_healthy`.
2. (Optional) Replicate the `wait_for_schema_registry` loop in other services if they prove flaky despite the healthcheck.

### WP4: Verification & E2E Run
**Objective**: Prove the fix.
**Tasks**:
1.  Rebuild `shared-lib` and `translation-service`.
2.  Run `docker compose up -d`.
3.  Verify `translation-service` logs show successful connection (or retries) and NO crash.
4.  Run `tests/e2e/tts_pipeline_smoke.py`.
5.  **Acceptance**: Smoke test passes; Translation Service logs show `Published TextTranslatedEvent`.

## 6. Risks & Mitigations

-   **Risk**: Infinite loop if Schema Registry is permanently down.
    -   *Mitigation*: Implement a hard timeout (e.g., 60-120s) after which the service raises a fatal error and exits (allowing orchestrator restart if configured, or manual intervention).
-   **Risk**: Shared lib update breaks other services.
    -   *Mitigation*: Keep API signature compatible. The retry logic should be internal to the client methods or an explicit opt-in wrapper.

## 7. Version Management
-   **Milestone**: Update Version and Release Artifacts.
-   **Tasks**:
    -   Bump `shared-lib` version (e.g., 0.2.1 -> 0.2.2).
    -   Update `CHANGELOG.md` identifying the stability fix.
