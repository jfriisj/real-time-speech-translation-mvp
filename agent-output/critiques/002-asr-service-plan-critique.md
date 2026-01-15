# Critique: Plan 002 — Audio-to-Text Ingestion (ASR Service)

**Artifact**: agent-output/planning/002-asr-service-plan.md
**Related Analysis**: agent-output/analysis/003-asr-ingestion-unknowns-analysis.md
**Related Architecture Findings**: agent-output/architecture/005-asr-service-architecture-findings.md
**Related Roadmap**: agent-output/roadmap/product-roadmap.md (Release v0.2.0, Epic 1.2)
**Date**: 2026-01-15
**Status**: Revision 3 — APPROVED

> Process note: The critic-mode instruction references `.github/chatmodes/planner.chatmode.md`, but that file is not present in this workspace; critique proceeded using repo-local plan/analysis/architecture artifacts.

## Changelog
| Date | Trigger | Summary |
|------|---------|---------|
| 2026-01-15 | Plan 002 Revision 2 | Re-reviewed after plan updates; resolved prior alignment issues (topics, wav-only, failure signaling, at-least-once) and approved with Milestone 0 as a hard gate for latency/caching validation. |

## Value Statement Assessment
- **Present**: YES.
- **Aligned to Roadmap**: YES.
- **Measures of Success**: Clear and now reference canonical topics.

## Overview
Plan 002 is clear on the service’s role, core constraints (CPU-only, 1.5 MiB cap), and test stratification. The plan now aligns to the architecture master’s pinned contract surface (canonical topics, wav-only policy, log+drop failure handling, and at-least-once semantics) and introduces an explicit pre-implementation validation gate (Milestone 0) to manage remaining feasibility/determinism risk.

## Architectural Alignment
- **Contract schemas**: Aligned (field names match the canonical Avro schemas).
- **Topics**: Aligned (uses `speech.audio.ingress` / `speech.asr.text`).
- **Failure signaling**: Aligned (MVP behavior is log + drop; no new error-event schemas introduced).
- **Audio format handling**: Aligned (wav-only for MVP; non-wav is dropped).
- **Delivery semantics**: Aligned (at-least-once acknowledged; duplicates tolerated).

## Scope Assessment
- **In scope (good)**: Consumer → transcribe → producer; containerize; basic logging and drop semantics; offline vs integration tests.
- **Scope creep risk**: Multi-format audio decode and error-event emission both expand contract surface area and dependencies.

## Technical Debt / Delivery Risks
- **Feasibility risk (latency)**: Managed by Milestone 0 benchmark gate (still requires execution, but plan is explicit about validating and defining pass/fail criteria).
- **Determinism risk (model fetch)**: Managed by Milestone 0 caching decision requirement.
- **Integration risk (topic drift)**: Resolved by canonical topic usage throughout plan and test scenarios.

## Findings

### Critical

1. **Topic taxonomy mismatch**
	- **Status**: RESOLVED
	- **Description**: Plan now uses canonical topics (`speech.audio.ingress` → `speech.asr.text`) consistently.
	- **Impact**: Interop with v0.1.0 shared infrastructure contract is preserved.
	- **Recommendation**: None.

2. **Audio format policy conflicts with MVP guardrail**
	- **Status**: RESOLVED
	- **Description**: Plan now states wav-only for MVP and requires log + drop for non-wav.
	- **Impact**: Prevents multi-format scope creep and reduces operational uncertainty.
	- **Recommendation**: None.

3. **Ambiguous failure signaling (“logs/events”)**
	- **Status**: RESOLVED
	- **Description**: Plan describes log + drop failure handling for MVP and does not introduce error-event schemas.
	- **Impact**: Avoids unplanned contract surface expansion.
	- **Recommendation**: None.

### Medium

4. **Feasibility unknown: CPU latency not validated**
	- **Status**: RESOLVED (as a planning concern)
	- **Description**: Plan adds Milestone 0 CPU latency benchmark with explicit requirement to define pass/fail criteria before coding.
	- **Impact**: Reduces risk of late discovery of infeasible CPU performance.
	- **Recommendation**: Ensure Milestone 0 is treated as a hard gate before implementation begins.

5. **Determinism gap: model caching strategy not explicit**
	- **Status**: RESOLVED (as a planning concern)
	- **Description**: Plan adds Milestone 0 model caching decision and requires documenting the chosen strategy in compose.
	- **Impact**: Establishes deterministic startup expectations.
	- **Recommendation**: Ensure the plan’s “choose one strategy” results in a single documented approach (avoid supporting both in MVP).

6. **At-least-once semantics not acknowledged**
	- **Status**: RESOLVED
	- **Description**: Plan explicitly documents at-least-once semantics and accepts duplicates for MVP.
	- **Impact**: Prevents demo/test assumptions that cause intermittent failures.
	- **Recommendation**: None.

### Low

7. **Plan-to-shared-lib naming may confuse implementers**
	- **Status**: RESOLVED
	- **Description**: Plan now references “the shared library’s consumer/producer wrapper” rather than hard-coding class names.
	- **Impact**: Reduces unnecessary coupling between plan text and library internals.
	- **Recommendation**: None.

## Questions
1. What is the maximum acceptable end-to-end ASR latency for MVP, and how will it be measured (wall time per event, or event timestamps)?
2. Is the demo input expected to be pre-chunked (short clips), or should the producer allow near-cap payloads regularly?
3. Which model distribution strategy is acceptable for your environment constraints (offline/CI/no-download policies)?

## Verdict
**APPROVED**. The plan is clear, aligned with the architecture master, and complete enough to implement. Remaining uncertainty (CPU latency and model distribution) is appropriately handled as an explicit pre-implementation gate (Milestone 0).
