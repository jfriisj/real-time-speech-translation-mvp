# Architecture Findings 021: Plan 010 (TTS) — Rev 33 Architectural Fit

**Related Plan (if any)**: agent-output/planning/010-text-to-speech-plan.md
**Related Architecture Master**: agent-output/architecture/system-architecture.md
**Verdict**: APPROVED_WITH_CHANGES

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | Planner/Implementer | Pre-implementation architecture review | Plan fits the platform’s Claim Check and SR governance, but MUST clarify edge retrieval semantics, configuration completeness, and “operable-without-storage” wording to avoid integration drift. |

## Context

- **What is being assessed**: Plan 010 Rev 33 for Epic 1.7 (TTS) targeting v0.5.0, including early Claim Check enablement (MinIO/S3) for `AudioSynthesisEvent`.
- **Affected modules/boundaries**:
  - Kafka topics: `speech.translation.text` (input), `speech.tts.audio` (output)
  - Schema Registry governance: `TopicNameStrategy`, subjects `*-value`, BACKWARD compatibility
  - Object storage boundary (MinIO/S3) as Claim Check pilot
  - Gateway edge responsibility (client-serving / presigning)

## Findings

### Architectural Fit (What’s Good)
- **Matches master Claim Check guardrails**: The plan enforces XOR semantics (`audio_bytes` OR `audio_uri`) and explicitly avoids logging presigned URLs.
- **Matches SR/topic governance**: Output topic + subject (`speech.tts.audio` / `speech.tts.audio-value`) aligns with `TopicNameStrategy` in the architecture master.
- **Retention governance present**: The plan now calls out a 24h lifecycle policy and explicitly references lifecycle enforcement via MinIO (preferred vs per-service deletion logic).
- **Observability is aligned**: Correlation ID + `transport_mode` + latency/RTF logging is consistent with the platform’s “measurable walking skeleton” priority.

### Must Change (Blocking before implementation)
1) **Define client retrieval semantics for `audio_uri` (edge contract)**
- The plan currently says “gateway (pass-through) -> web client” but does not define *how* the client obtains audio when `audio_uri` is an internal key.
- Architecture master requirement: presigning belongs at the edge (Gateway) and URIs must degrade gracefully.
- Required plan delta:
  - Specify one explicit, supported retrieval strategy for v0.5.0:
    - **Preferred**: TTS emits internal object key; Gateway provides a read endpoint that presigns and/or proxies the object (and MAY cache presigned URLs).
    - Alternative: TTS emits presigned URL (discouraged; expands security surface and couples TTS to edge concerns).
  - Add acceptance criteria that prove the chosen retrieval strategy works end-to-end.

2) **Make the “operable without object storage” guarantee explicit**
- Architecture master guardrail: “system MUST remain operable with object storage disabled (baseline inline path remains valid where size permits)”.
- The plan currently states MinIO/ObjectStorage are “AVAILABLE and REQUIRED for full compliance”, which is acceptable, but it MUST not be read as “hard dependency for startup / for all payloads”.
- Required plan delta:
  - Add a single sentence under assumptions: “Service MUST start and process inline payloads even when storage is disabled/unavailable; only oversized outputs are dropped.”

3) **Configuration table is incomplete relative to the architecture master’s security/TTL guardrails**
- The plan’s env var table omits several knobs that materially affect correctness/security and are already part of the platform’s object-store usage pattern.
- Required plan delta (minimum): include and normatively define:
  - `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_SECURE`
  - `MINIO_PUBLIC_ENDPOINT` (explicitly optional; only for local developer access)
  - `MINIO_PRESIGN_EXPIRY_SECONDS` (must be time-bounded; default allowed)
- Also clarify environment-specific defaults: inside compose (`http://minio:9000`) vs host access (`http://127.0.0.1:9000`).

4) **Remove ambiguity around `TTS_AUDIO_URI_MODE` values**
- The plan lists `internal` vs `external`/`presigned`, but does not define normative behavior for the non-internal values.
- Required plan delta:
  - Either (A) restrict v0.5.0 to `internal` only (recommended), or (B) precisely define accepted values and their security constraints (no logging, TTL bounded, edge ownership still preferred).

### Risks (Non-blocking, but must be tracked)
- **Shared-lib creep**: `ObjectStorage` must remain a thin utility; avoid turning `speech-lib` into a platform SDK with business logic.
- **Key naming collisions**: `tts/{correlation_id}.wav` assumes correlation IDs are globally unique per request. If replays or retries reuse IDs, objects may be overwritten.
- **Expired/missing URIs**: Consumers must treat URI fetch failures as non-fatal and surface clear errors (plan should mention this at least for Gateway/client UX).

### Alternatives Considered
- **Inline-only output + strict max duration**: Simplest but violates the architecture master’s “cannot violate Kafka invariants” requirement under realistic TTS durations; rejected.
- **Always-URI output**: Operationally robust for size, but introduces unnecessary storage dependency for small payloads and broadens failure modes; not preferred for MVP+.

## Integration Requirements

- **Gateway edge contract**: Document and implement a single retrieval method for `audio_uri` (presign/proxy) and validate it in E2E.
- **Schema discipline**: Keep additive evolution only; enforce XOR semantics centrally (producer validates before publish; consumer validates before use).
- **Security**: Presigned URLs (if ever used) must be time-bounded and never logged; internal endpoints by default.

## Consequences

- With the required changes, Plan 010 remains consistent with the system architecture’s Claim Check pilot decision (v0.5.0) and preserves the platform’s scalability and security guardrails.
- Without the required changes, implementation is likely to drift at the Gateway/client boundary and ship an ambiguous `audio_uri` contract that breaks downstream integration or leaks security assumptions.

## Handoff

## Handoff to Planner/Implementer

**From**: Architect
**Artifact**: agent-output/architecture/021-text-to-speech-plan-rev33-architecture-findings.md
**Status**: APPROVED_WITH_CHANGES
**Key Context**:
- Plan 010 aligns with Claim Check + SR governance, but the edge retrieval contract and configuration/security knobs must be made explicit before implementation.

**Recommended Action**: Apply the “Must Change” deltas to Plan 010 Rev 33, then re-request a quick re-review focused solely on the Gateway/client retrieval semantics and config table completeness.