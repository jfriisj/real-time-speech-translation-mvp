# Critique: Plan 003 — Text-to-Text Translation (Translation Service)

**Artifact**: agent-output/planning/003-translation-service-plan.md
**Related Analysis**: agent-output/analysis/003-translation-service-analysis.md
**Related Architecture Findings**: agent-output/architecture/003-translation-service-architecture-findings.md
**Related Roadmap**: agent-output/roadmap/product-roadmap.md (Release v0.2.0, Epic 1.3)
**Date**: 2026-01-15
**Status**: Revision 2 — APPROVED

> Process note: Critic-mode instructions reference `.github/chatmodes/planner.chatmode.md`, but that file is not present in this workspace; critique proceeded using repo-local plan/architecture/roadmap artifacts.

## Changelog
| Date | Trigger | Summary |
|------|---------|---------|
| 2026-01-15 | Plan 003 completed | Reviewed for clarity/completeness/scope/risks/alignment; identified minor gaps around acceptance criteria, config surface, and failure-handling specifics. |
| 2026-01-15 | Plan 003 updated via Analysis 003 | Re-reviewed after plan updates; resolved prior gaps (explicit `TARGET_LANGUAGE`, commit-on-drop semantics, missing input language default) and approved. |

## Value Statement Assessment
- **Present**: YES.
- **Aligned to Roadmap**: YES (matches Epic 1.3 user story and acceptance criteria intent).
- **Measures of Success**: Present and testable (topic bindings + correlation_id + payload text).

## Overview
Plan 003 is structurally sound and appropriately MVP-scoped. It aligns with the architecture’s contract-first approach by consuming `TextRecognizedEvent` from `speech.asr.text` and producing `TextTranslatedEvent` to `speech.translation.text`, preserving `correlation_id`. The plan also wisely de-risks model operational complexity via a deterministic mock translator.

The remaining issues were primarily about **clarity and completeness of operational constraints** (config surface, language-pair handling, and failure semantics). These were addressed by Analysis 003 and folded back into Plan 003.

## Architectural Alignment
- **Contract schemas**: Aligned (post-architecture review, the plan uses `TextTranslatedEvent.payload.text`, `source_language`, `target_language`).
- **Topics**: Aligned (canonical topic taxonomy matches architecture master).
- **Delivery semantics**: Aligned (at-least-once acknowledged; duplicates tolerated).
- **Failure signaling**: Aligned (plan now defines “log + drop” as log error and commit offset).
- **Shared contract artifact**: Aligned (uses `speech-lib` for Avro/Kafka; does not propose cross-service imports beyond shared contract).

## Scope Assessment
- **In scope (good)**:
  - Consumer → translate → producer loop.
  - Containerized service + Compose integration.
  - Unit tests for translator and handler; smoke/integration validation.
- **Intentional deferrals (good, but should be called out as explicit non-goals)**:
  - Real model integration (Hugging Face) optional.
  - Idempotency/deduplication.
  - Error events/DLQ.

## Technical Debt / Delivery Risks
- **Language-pair ambiguity** (Resolved): Plan defines `TARGET_LANGUAGE` (default `"es"`) and documents how output `payload.target_language` is populated.
- **Operational semantics under failure** (Resolved): Plan defines drop behavior as committing the offset to avoid poison-pill loops.
- **Versioning mismatch risk** (Low): The plan targets v0.2.0 and suggests setting service version to 0.2.0. If other services follow different versioning, this can introduce release-note confusion. (Not an architecture blocker, but worth clarifying.)

## Findings

### Critical
None.

### Medium

1. **Target language configuration is underspecified**
	- **Status**: RESOLVED
	- **Description**: Plan requires setting `payload.target_language` but doesn’t define the expected configuration interface (env var, default, allowed values) or how it impacts the mock translator.
	- **Impact**: Ambiguity in demo behavior; harder QA reproducibility.
	- **Recommendation**: Define a single MVP config input (e.g., one env var with default) and document expected behavior when missing/invalid.

2. **Failure-handling semantics are too high-level for Kafka reality**
	- **Status**: RESOLVED
	- **Description**: “Log and drop malformed events or processing errors” is aligned with MVP policy, but it’s unclear how the consumer offset behavior should work when an event fails translation/deserialization.
	- **Impact**: Risk of infinite reprocessing (poison-pill loop) or silent data loss depending on consumer commit strategy.
	- **Recommendation**: Add a brief note clarifying the intended behavior at failure: whether the service commits offsets after logging (true “drop”) and any constraints around retries.

### Low

3. **Plan doesn’t explicitly restate the required output fields from schema**
	- **Status**: PARTIALLY ADDRESSED
	- **Description**: The plan now references required output fields in Milestone 3, but the “Measure of Success” and QA section could more explicitly enumerate required output metadata (`source_language`, `target_language`) to prevent regression.
	- **Impact**: Small; mostly prevents implementer/QA misinterpretation.
	- **Recommendation**: Optional: add explicit checks for `payload.source_language` and `payload.target_language` in the integration test scenario to match the schema requirements.

4. **Template process gap**
	- **Status**: OPEN
	- **Description**: The suggested template path `agent-output/templates/000-template-architecture-findings.md` does not exist in this repo.
	- **Impact**: Slows future architecture reviews and increases formatting drift.
	- **Recommendation**: Add/standardize a template location in a process-improvement doc (not required to implement the translation service).

## Questions
1. Should the integration test explicitly assert `payload.source_language` and `payload.target_language` (recommended for schema regression prevention)?
2. Is `TARGET_LANGUAGE` expected to stay fixed to a single language pair for the MVP demo, or do you want to demonstrate switching it between deployments?

## Verdict
**APPROVED**. The plan is now clear, MVP-scoped, and aligned with the architecture master. Prior gaps identified in Analysis 003 (target-language configuration and commit-on-drop semantics) are resolved in the plan; remaining suggestions are optional QA tightening.
