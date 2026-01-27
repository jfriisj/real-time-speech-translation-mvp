# Architecture Findings 016: Plan 010 (Epic 1.7 TTS) — Re-Review

**Related Plan (if any)**: agent-output/planning/010-text-to-speech-plan.md (Rev 22)
**Verdict**: APPROVED

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-27 | Planner | Architecture re-review | Confirms Plan 010 (Rev 22) has incorporated all required architectural changes: optional storage dependency, explicit byte thresholds (1.25 MiB), complete schema metadata, and security guardrails. |

## Context

Plan 010 was originally conditionally approved with changes requested (Findings 015). The revisions address strict payload invariant handling and decoupling from the future Epic 1.8.

## Findings

### Addressed Requirements
- **Storage Dependency**: Plan now explicitly states `ObjectStorage` is OPTIONAL and defines "log and drop" behavior when disabled for large payloads.
- **Payload Thresholds**: `MAX_INLINE_BYTES = 1,310,720` (1.25 MiB) is now an explicit constant providing a safety margin below the 1.5 MiB architecture cap.
- **Schema Metadata**: `AudioSynthesisEvent` schema now includes `audio_format`, `content_type`, and `correlation_id`.
- **Runtime Enforcements**: Plan mandates "exactly one of `audio_bytes` or `audio_uri`" assertion and "Do NOT log full presigned URLs".

## Integration Requirements
- Proceed with implementation as scoped in Rev 22.

## Consequences
- The TTS service implementation will be robust against Kafka configuration limits and safe for immediate deployment even without S3/MinIO infrastructure.

## Handoff

## Handoff to Implementer

**From**: Architect
**Artifact**: agent-output/architecture/016-text-to-speech-plan-architecture-findings.md
**Status**: APPROVED
**Key Context**: Use `agent-output/planning/010-text-to-speech-plan.md` (Rev 22).

**Recommended Action**: Execute plan.