# Architecture Findings 003: Audio Payload Policy Unknowns (Analysis 002)

**Date**: 2026-01-15
**Input Analysis**: agent-output/analysis/002-audio-message-size-analysis.md
**Related Architecture Master**: agent-output/architecture/system-architecture.md

**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Trigger | Summary |
|------|---------|---------|
| 2026-01-15 | Analysis 002 | Converted sizing/scope unknowns into explicit architecture requirements and required plan deltas |

## Context
This review focuses on architectural fit and decision closure for the audio-ingress contract and shared artifact behavior:
- `AudioInputEvent` schema shape and its payload limits
- Kafka broker message-size assumptions for local MVP
- The shared contract artifact / `speech-lib` boundary (avoid SDK creep)

These decisions materially affect Epic 1.2+ because all service producers/consumers will implement against this contract.

## Findings

### What Fits
- The analysis correctly identifies the highest-risk integration failure modes: payload-size ambiguity and shared-artifact scope drift.
- The analysis correctly flags the plan inconsistency (reject vs reference/URI), which would otherwise cause schema churn.

### Must Change (Required)

1. **Oversized audio behavior must be single-valued across docs and code**
   - Architecture master decision: `AudioInputEvent` inline audio payload hard cap is **1.5 MiB**, and larger payloads are **rejected in v0.1.0**.
   - Required: all plans/docs MUST remove “reference/URI is required for >1.5 MiB” language for v0.1.0 unless/until a dedicated “reference pattern” epic is introduced.

2. **Kafka broker message-size policy must be treated as a configured invariant**
   - Architecture master decision: local MVP config uses `message.max.bytes=2097152` (2 MiB).
   - Required: implementation verification (compose bring-up / smoke tests) MUST assert the broker and client configs match the invariant to prevent runtime produce failures.

3. **Shared contract artifact boundary must remain narrow**
   - Required allowed scope: schema ownership, envelope definition, generated bindings, serialization/deserialization helpers, correlation helpers, and payload-size enforcement.
   - Required forbidden scope: retries/backoff policy, topic routing decisions, domain validation, workflow orchestration.

### Should Change (Strongly Recommended)

1. **Remove misleading duration estimates from contract guidance**
   - Any “2 MiB equals N minutes” claims are highly sensitive to encoding assumptions and should not be used as architecture guidance.
   - Prefer expressing limits as bytes + providing a separate, explicitly-parameterized calculator later (sample rate, bit depth, channels, compression).

## Architecture Master Updates
The architecture master was updated to eliminate one class of integration ambiguity:
- Added an explicit decision pinning Schema Registry **subject naming strategy** to `TopicNameStrategy` with `topic-value` subjects.

## Consequences
- Downstream epics (1.2+) can implement producers/consumers without guessing payload policy or subject naming.
- Reference/URI support for larger audio is explicitly deferred and must be introduced via a new epic/change entry if needed.
