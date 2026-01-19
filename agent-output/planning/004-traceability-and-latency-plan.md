# Plan 004: End-to-End Traceability & Latency

**Plan ID**: 004
**Target Release**: v0.2.1 (Performance Validation)
**Epic**: 1.4 End-to-End Traceability & Latency (Shared / Integration)
**Status**: Proposed
**Date**: 2026-01-19
**Dependencies**: Plan 001 (Infra), Plan 002 (ASR), Plan 003 (Translation)

## 1. Value Statement and Business Objective
**As a** Researcher/Thesis Author,
**I want** to trace a single request from Audio In to Translated Text Out and measure the time,
**So that** I can validate the performance claims of the architecture.

**Measure of Success**:
- A script/tool exists that can run 100 sequential requests.
- Latency is calculated as `Timestamp(TextTranslatedEvent) - Timestamp(AudioInputEvent)`.
- Intermediate latency (ASR completion) is also visible.
- Correlation chain is proven unbroken for >95% of requests.

## 2. Context & Roadmap Alignment
This epic validates the "Walking Skeleton" (v0.2.0) by adding the observability layer required for the thesis. It does not introduce new functional services but adds the "Thesis Probe" machinery.

**Related Analysis**:
- [Analysis 004](agent-output/analysis/004-traceability-and-latency-analysis.md): Technical feasibility and timestamp definitions.
- [Analysis 005](agent-output/analysis/005-traceability-and-latency-governance-analysis.md): Governance, roadmap ownership, and reporting standards.

**Roadmap Note on Versioning**:
- The current roadmap (v0.2.0 released, v0.3.0 planned) does not yet explicitly define **v0.2.1**.
- **Proposal**: This plan establishes **v0.2.1** as a patch/validation release dedicated to performance methodology and measurement tools, without changing service logic.
- **Action**: Milestone 0 includes an explicit Roadmap Update to formalize v0.2.1 (Owner: Product Owner/User via Agent).

**Architecture Guidance**:
- **Non-Invasive**: The probe acts as an external Kafka client (Producer + Consumer). IT DOES NOT require code changes to ASR or Translation services, assuming they correctly propagate `correlation_id` and set `timestamp` (which is enforced by the schema).
- **Metric Definitions**:
    - `T0`: Audio Ingress Timestamp
    - `T1`: ASR Output Timestamp
    - `T2`: Translation Output Timestamp
    - `Latency_ASR` = T1 - T0
    - `Latency_Translation` = T2 - T1
    - `Latency_Total` = T2 - T0

## 3. Assumptions & Constraints
- **assumption (Timestamp Semantics)**: `BaseEvent` sets `timestamp` at initialization (publish-time). Therefore, measured latency represents **Event Publication Delta**, not full wall-clock processing time (it excludes consumer poll latency). This distinction is accepted for MVP thesis claims.
- **assumption**: ASR and Translation services behave correctly regarding `correlation_id` propagation (verified in v0.2.0).
- **constraint (Ingestion)**: Probe MUST inject `AudioInputEvent` (payload <= 1.5 MB) directly to `speech.audio.ingress` to match architectural contracts.
- **constraint (Isolation)**: Probe MUST NOT interfere with production. It must use a unique consumer group ID (e.g., `traceability-probe-<run-id>`) and generally avoid committing offsets unless required for stability.
- **constraint**: Must use `speech-lib` for serialization/deserialization.

## 4. Implementation Plan

### Milestone 0: Roadmap Alignment
**Objective**: Formalize the target release and governance.
**Owner**: Product Owner (via Implementation Agent).
1.  **Roadmap Update**: Add a "Release v0.2.1" entry to `agent-output/roadmap/product-roadmap.md` describing it as "Thesis Validation & Traceability".
    *   **Acceptance Gate**: Explicit PR merge or file update confirming Roadmap includes v0.2.1 section and Epic 1.4 is active.
2.  **Release Doc**: Create `agent-output/releases/v0.2.1.md` in "Draft" status, following the standard template (Publication Verification Checklist, Key Deliverables).
    *   **Acceptance Gate**: File exists and links to Epic 1.4.
3.  **Move Epic 1.4**: Update `product-roadmap.md` to move Epic 1.4 from "v0.2.0" (Planned) to the new "v0.2.1" section.

### Milestone 1: Traceability Infrastructure
**Objective**: Create the probe tool structure and manage dependencies.
1.  **Directory**: Create `tests/e2e/`.
2.  **Dependencies**: Create or update `tests/requirements.txt`.
    *   **Must include**: `speech-lib` (local path or package), `confluent-kafka` (for consumer/producer), `numpy` (for stats), `pytest` (if using test runner).
    *   **Rationale**: Keeps tool dependencies isolated from production service containers (per Analysis 005).

### Milestone 2: The Traceability Probe (Script)
**Objective**: Implement the `measure_latency.py` tool.
1.  **Producer (T0)**:
    - Acts as the "External Producer" defined in [Analysis 004](agent-output/analysis/004-traceability-and-latency-analysis.md).
    - Generates a synthetic `AudioInputEvent` with a valid WAV payload (<= 1.5 MB).
    - Publishes to `speech.audio.ingress`.
    - Records `T0` (Event Creation Time).
2.  **Consumer (T1, T2)**:
    - Listens to **both** `speech.asr.text` (T1) and `speech.translation.text` (T2).
    - **Configuration**:
        - `group.id`: `traceability-probe` (or random suffix).
        - `auto.offset.reset`: `latest` (start fresh for each run).
        - `enable.auto.commit`: `false` (read-only observation).
3.  **Correlation Logic**:
    - Maintains a `Dict[correlation_id, StartTime]`.
    - On `TextRecognizedEvent`: Record `T1`.
    - On `TextTranslatedEvent`: Record `T2`, calculate Total Latency, print/log, and mark complete.
4.  **Timeout**: Implement a timeout (e.g., 10s) to detect dropped chains.

### Milestone 3: Validation Protocol & Report
**Objective**: Run the "N=100" campaign and generate standard artifacts.
1.  **Loop**: Script accepts `--count 100` and optional `--output <file>`.
2.  **Stats**: At the end of the run, calculate P50, P90, P99 latency.
3.  **Warmup**: Explicitly discard the first 5 requests from stats to account for model loading/cold start.
4.  **Reporting**:
    *   **Stdout**: Print human-readable summary.
    *   **JSON Output**: Generate a JSON summary (e.g., `latency_summary.json`) for machine parsing/CI.
    *   **Schema**:
        ```json
        {
          "meta": { "timestamp": "...", "run_id": "...", "warmup_discarded": 5 },
          "counts": { "total": 100, "success": 98, "failure": 2 },
          "latencies_ms": { "p50": 120, "p90": 200, "p99": 450 },
          "failures": { "timeout": 1, "broken_chain": 1 }
        }
        ```
    *   **Failure Categories**:
        *   `Timeout`: Total time exceeded limit (10s).
        *   `BrokenChain`: Received T1 (ASR) but missing T2 (Translation).

### Milestone 4: Documentation & Versioning
**Objective**: Release v0.2.1.
1.  **Docs**: Create `docs/benchmarks/001-mvp-latency-baseline.md`.
    *   **Content**: Include the JSON output from the first successful official run.
    *   **Context**: Describe the hardware/environment used for the run (e.g., local dev machine, GPU/CPU details).
2.  **Version**: Bump repository state to v0.2.1.
    *   **Scope**: Create git tag `v0.2.1`. Update `README.md` version Badge (if present). No edits to `pyproject.toml` or service manifests required for this patch.
3.  **Release Artifact**: Update `agent-output/releases/v0.2.1.md` to "Released" status and link the benchmark doc.

## 5. Verification Strategy (QA Handoff)
- **Prerequisites**:
    - Run `pip install -r tests/requirements.txt` to install probe dependencies.
- **Unit Tests**: None for the script itself (it *is* a test).
- **Operational Verification**:
    1.  Bring up the stack (`ASR`, `Translation`, `Kafka`, `SR`).
    2.  Run `python tests/e2e/measure_latency.py --count 5`.
    3.  Verify output shows `T0` (Ingress), `T1` (ASR), `T2` (Translation) and correct deltas.
    4.  Verify P50/P90/P99 stats are printed.
    5.  Verify `latency_summary.json` is created and valid.
- **Isolation Check**:
    - Run the probe while running a separate consumer (e.g., `kafka-console-consumer`).
    - Verify the probe does not "steal" messages (due to unique group ID) and does not commit offsets preventing others from reading (if others use different groups).

## 6. Risks
- **Clock Skew**: If services run in containers with drifted clocks vs the host script.
    - *Mitigation*: We rely on the *event* timestamps generated by the services. If the container clocks are off, the metrics are off. Docker usually syncs with host, but we should verify.
- **Cold Starts**: ADDRESSED. Milestone 3 includes a 5-request warmup discard policy.

