# Critique: Plan 001 — Shared Infrastructure & Contract Definition

**Artifact path**: agent-output/planning/001-shared-infrastructure-plan.md  
**Related analysis**: agent-output/analysis/001-shared-infrastructure-analysis.md  
**Related architecture findings**: agent-output/architecture/001-shared-infrastructure-architecture-findings.md  
**Related roadmap**: agent-output/roadmap/product-roadmap.md  
**Related system architecture**: agent-output/architecture/system-architecture.md  

**Date**: 2026-01-15  
**Status**: Revision 2  

> Note: The mode instructions reference `.github/chatmodes/planner.chatmode.md` as a required checklist input, but that file was not present in this workspace at review time. This critique follows the Critic rubric in the current chatmode instructions (Value Statement, alignment, scope, risks, clarity/completeness).

## Changelog

| Date | Handoff / Trigger | Summary |
|------|-------------------|---------|
| 2026-01-15 | User request: critique completed plan | Initial critique for clarity, completeness, scope, risks, and alignment |
| 2026-01-15 | Roadmap + plan updates | Updated critique to reflect resolved naming/sizing drift; focused remaining findings on clarity, evidence of delivery, and verifiable exit criteria |

## Value Statement Assessment (Required)

**Present and well-formed**: The plan includes a clear user story with a concrete objective: unify event bus + strict Avro schemas + traceability/security foundations.

**Value delivery check**:
- **Direct value**: Yes — Kafka/SR bring-up + golden schemas + shared contract artifact are direct enablers for Epic 1.2/1.3.
- **Measurability**: Partial — correlation ID is explicitly required, but explicit “Done” criteria and observable proof points per milestone could be sharper.

**Verdict on value statement**: ACCEPTABLE (clear and aligned with roadmap Epic 1.1).

## Overview

This plan is directionally strong: it explicitly incorporates the architecture “must change” items (Contract Canon, topic taxonomy, subject naming strategy, message-size policy, library boundary). It also demonstrates reasonable scope discipline for a hard MVP.

The main remaining gaps are clarity around how Avro validation will actually be evidenced, and the absence of an explicit “delivered artifacts / proof” section despite the plan being marked **DELIVERED**.

## Architectural Alignment

**Overall fit**: Strong.
- Matches the architecture’s “standardize contracts (Option A)” decision.
- Constrains the shared artifact boundary (explicitly forbids business logic / retries / routing / orchestration).
- Includes required envelope fields and Schema Registry compatibility intent.

**Key alignment concern**:
- The plan introduces producer hookup semantics (`publish_event`, `consume_events`) that can drift into “platform SDK” behavior over time. The plan tries to constrain it, but the API shape still invites feature creep.

## Scope Assessment

**Scope is mostly MVP-appropriate**, but watch for these scope creep vectors:
- “Correlation Context Manager” is not clearly bounded to MVP needs; it risks becoming an implicit tracing framework.
- “Validation: validate JSON examples against Avro schemas” is underspecified (tooling unclear) and can expand into contract testing infrastructure.

**Out-of-scope is implied but not explicit**:
- No auth, ACLs, TLS, multi-broker scaling, external network exposure — these are consistent with MVP, but explicit “Out of scope” bullets would reduce ambiguity.

## Technical Debt & Long-Term Risks

- **Schema governance risk (medium)**: Compatibility is mentioned, but the plan doesn’t define how subjects are versioned/managed over time (especially across multiple topics).
- **SDK creep risk (medium-high)**: Even with “Forbidden scope” text, wrappers tend to accumulate operational policies (retries/backoff/logging/metrics). This is a common failure mode for shared libraries in microservice ecosystems.
- **Delivery evidence gap (medium)**: A delivered plan without explicit artifact links and proof points makes audits and downstream onboarding harder.

## Findings

### Critical

**1) Naming drift between roadmap and plan** (RESOLVED)
- **Description**: Previously, roadmap AC listed `AudioProcessingEvent` while plan used `AudioInputEvent`.
- **Resolution evidence**: Roadmap Epic 1.1 AC now uses `AudioInputEvent`, and the plan’s Contract Canon pins the same.
- **Impact**: Reduced integration churn risk for Epic 1.2/1.3.

**2) Incorrect/ambiguous message-size statement** (RESOLVED)
- **Description**: Previously included a misleading duration estimate.
- **Resolution evidence**: Plan now states byte/MiB limits explicitly and avoids duration claims.

### Medium

**3) Schema validation approach is underspecified** (OPEN)
- **Description**: “Use `jq` or a script to validate JSON examples against these schemas” is unclear for Avro.
- **Impact**: Reviewers/implementers may interpret this as sufficient validation when it is not; may lead to wasted effort.
- **Recommendation**: Specify the intended validation mechanism at a plan level (e.g., “validate by encoding/decoding with an Avro library/tooling”), without prescribing exact commands.

**4) Plan marked DELIVERED but lacks explicit delivery evidence** (OPEN)
- **Description**: The plan status is **DELIVERED**, but the document reads purely as a forward-looking plan and does not list what was produced (file paths, versions, smoke-test evidence).
- **Impact**: Makes it hard for Epic 1.2/1.3 implementers to locate the contract artifact, confirm invariants (compatibility mode, subject naming), and reproduce the smoke test quickly.
- **Recommendation**: Add a short “Delivered Artifacts / Evidence” section with links to:
	- `docker-compose.yml` location
	- schema directory location
	- `speech-lib` package path + version
	- smoke test location + expected output summary

**5) Shared library dependency choice is ambiguous** (OPEN)
- **Description**: The plan suggests “Pydantic/Dataclasses” but also calls for minimal dependencies.
- **Impact**: Can trigger churn: if Pydantic is chosen later, it adds weight and versioning considerations; if dataclasses are chosen, the testing strategy text becomes inconsistent.
- **Recommendation**: Decide and state one: “dataclasses only” (likely best for minimal dependencies) or “Pydantic is allowed” (with explicit justification and version pinning strategy).

**6) Completion criteria per milestone are not explicit** (OPEN)
- **Description**: Steps are listed, but “Done means” is not consistently stated as verifiable artifacts and checks.
- **Impact**: Teams can disagree on whether the epic is finished (especially around security verification and Schema Registry configuration).
- **Recommendation**: Add explicit exit criteria per milestone (e.g., “compose up succeeds; SR compatibility set; schemas register; smoke test passes; oversized audio rejected”).

### Low

**7) Analysis doc is now stale relative to the plan** (OPEN)
- **Description**: The analysis document frames the work as blocked by missing “must-do fixes list,” but the plan already resolves this by embedding concrete controls.
- **Impact**: Confuses future readers about whether remediation is defined or still blocked.
- **Recommendation**: Update the analysis artifact status section to reflect that the blockers are resolved by folding controls into the plan (or mark it as historical).

**8) “Security test: non-localhost IP fails” is vague in local dev** (OPEN)
- **Description**: The test is phrased conditionally and may not be meaningfully testable on all dev setups.
- **Impact**: Leaves a security AC partially subjective.
- **Recommendation**: Clarify what constitutes evidence (e.g., “Docker port bindings show 127.0.0.1 only” is usually sufficient for MVP).

## Questions

1. What is the intended audio encoding for the MVP ingress event (raw PCM, WAV container, compressed format)? If undecided, should the plan avoid encoding-specific language and remain byte-limit only?
2. Do you want the shared library to expose “wrappers” (producer/consumer objects) or only pure functions/helpers for serialization + envelope population? This decision affects SDK creep risk.
3. What is the minimum acceptable “schema governance” for MVP beyond compatibility mode (e.g., explicit subject naming + versioning convention documentation)?

## Risk Assessment

- **Overall risk**: Medium-low.
- **Primary driver**: lack of explicit delivered artifact evidence + underspecified Avro validation approach.
- **Mitigation leverage**: High.

## Recommendations (Plan-level, non-implementation)

- Add explicit milestone exit criteria and clarify schema validation approach.
- Tighten the shared library public API statement to minimize SDK creep.
- Add a “Delivered artifacts / evidence” section so this plan remains useful post-delivery.
