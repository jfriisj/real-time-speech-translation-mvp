# Analysis 005: Traceability Probe Governance & Reporting

## Value Statement and Business Objective
**As** the release/governance steward for the Walking Skeleton,
**I need** clarity about which release owns the traceability probe, how its results are presented, and where its dependencies live,
**So that** implementation can start with an unambiguous roadmap, QA/UAT can sign-off on a reproducible report, and dependency drift is minimized.

## Context & Target Questions
- **Plan under review**: [agent-output/planning/004-traceability-and-latency-plan.md](agent-output/planning/004-traceability-and-latency-plan.md) (Epic 1.4, traceability)
- **Current roadmap**: [agent-output/roadmap/product-roadmap.md](agent-output/roadmap/product-roadmap.md) shows Release v0.2.0 (core services) and v0.3.0 (Expand & Speak); Epic 1.4 remains under v0.2.0 Planned.
- **Existing analysis**: [Analysis 004](agent-output/analysis/004-traceability-and-latency-analysis.md) surfaced the same release mismatch, timestamp semantics, and consumer isolation needs.
- **Specific questions** (per critique):
  1. Who owns/approves Milestone 0 (adding v0.2.1 to the roadmap) and what acceptance signal is required?
  2. What run-summary format should QA/UAT accept (counts, percentiles, failure categories)?
  3. Where do the probe’s dependencies live (tests/requirements vs shared tools) to ensure reproducibility?

## Methodology
- Reviewed the roadmap and release docs to confirm v0.2.1 is absent; noted release entries in `agent-output/releases/` (v0.1.0, v0.2.0) and release process (MA). No v0.2.1 doc exists yet.
- Scanned critiques, QA/UAT artifacts (agent-output/qa/ and uat) for common reporting formats (JSON summary, integration result bullet) to identify current acceptance patterns.
- Inspected repository structure for dev dependency guidance (`pyproject.toml`, `requirements-dev.txt` if present, `tests/requirements.txt`) and existing tools inside `tests/e2e/` or `shared` to recommend placement.

## Findings
### Fact: No formal release entry or owner yet for v0.2.1
- Release docs exist for v0.1.0 and v0.2.0 under `agent-output/releases/`. The release process (see release critique instructions) expects a release doc per semantic version.
- Roadmap currently lacks any section describing v0.2.1; the request to add one sits within Plan 004 Milestone 0 but no owner or approver is called out.
- `agent-output/release` gating typically involves QA, UAT, and Product Owner sign-off; the roadmap owner (roadmap agent) could take the lead on adding the entry.

### Fact: QA/UAT summary conventions are lightweight bullet + evidence references
- QA reports (e.g., `agent-output/qa/003-translation-service-qa.md`) and UAT reports capture results via tables (dates, agents, summary) and a textual Value Delivery section referencing tests.
- Release docs expect `Publication Verification Checklist`, `Key Deliverables`, and `Post-Release Status` entries.
- No artifact currently describes how to format measurement run data (counts, percentiles, failure categories).

### Fact: The repository favors `pyproject.toml` for service dependencies; helper scripts often live under `tests/` with their own `requirements-dev.txt` or `tests/requirements.txt`.
- `services/translation/pyproject.toml` defines service dependencies; `tests/` currently lacks its own manifest.
- Shared tooling (like `shared/speech-lib`) is packaged via `pyproject.tml` and consumed by services.
- Without guidance, maintainers may scatter `confluent-kafka`/`numpy` installations across envs.

## Recommendations
1. **Release governance**: Treat Milestone 0 as a decision gate with a named owner (e.g., Roadmap Agent or Product Owner). Require that the owner either approves a new roadmap entry plus release doc (agent-output/releases/v0.2.1.md) or explicitly directs the plan to stay under v0.2.0. Document the acceptance signal (roadmap PR merged and release doc approved) before implementation begins.
2. **Run reporting format**: Standardize on a small JSON or Markdown summary (counts, number of broken chains by category, percentiles, warmup/measurement periods, timestamps). Provide a template inside `docs/benchmarks/001-mvp-latency-baseline.md` so QA/UAT can compare future runs.
3. **Dependency management**: Put probe dependencies in `tests/requirements.txt` (or add a `tests-dev` extras section in `pyproject.toml` if consistent with repo policy). Document the command to install those deps before running the probe (e.g., `pip install -r tests/requirements.txt`). This keeps dependencies for tooling separate from services and aligns with existing structure where each service defines its own environment.

## Open Questions
1. Should the roadmap owner treat v0.2.1 as a formal release or simply as a traceability milestone inside v0.2.0 (with no new release doc)?
2. What failure categories should be reported when a `correlation_id` chain doesn’t complete (timeout, missing ASR event, missing translation event, schema error)?
3. Would a reusable script (e.g., `measure_latency.py`) be better installed as part of `shared/speech-lib` (for reuse) or kept under `tests/e2e` with its own dependencies? If the latter, how do QA/UAT agents consistently run it?
