# Plan 022: Artifact Persistence (Claim Check) Platform Rollout

**ID**: 022
**Target Release**: v0.6.0
**Epic**: Epic 1.8 (Artifact Persistence / Observability & Persistence)
**Status**: Revised (Rev 4)
**Plan Owner**: Planner Agent
**Date**: 2026-01-28
**Analysis Ref**: agent-output/analysis/015-artifact-persistence-rollout-research-gaps.md
**Architecture Ref**: agent-output/architecture/023-artifact-persistence-rollout-plan-architecture-findings.md
**Preceded By**: Epic 1.7 (TTS)

## Value Statement and Business Objective
**User Story**: As a Researcher, I want to persist intermediate audio and speech segment artifacts to object storage, So that I can audit the quality of each pipeline stage and prevent Kafka payload size violations.

**Business Objective**: Extend the **Claim Check Pattern** (piloted in TTS) to the entire platform (Gateway, VAD, ASR), ensuring that large audio payloads (>1.25 MiB) are offloaded to MinIO/S3 while maintaining a consistent audit trail.

**Success Metric**:
- **Completeness**: 100% of payloads > 1.25 MiB are offloaded to object storage (or strictly rejected if storage is down).
- **Measurement Method**: Log parsing/aggregation of structured logs containing `transport_mode` (uri vs inline) and `audio_size_bytes` fields.
- **Reliability**: No Kafka `MessageSizeTooLarge` errors in production logs.
- **Auditability**: A researcher can retrieve the input audio, VAD segment, and TTS output for a given `correlation_id` using a consistent key scheme.

## Context & Scope
- **Inputs**: `AudioInputEvent` (Ingress), `SpeechSegmentEvent` (VAD), `AudioSynthesisEvent` (TTS - retrofit), `TextRecognizedEvent` (ASR - optional).
- **Terminology**: The Roadmap Acceptance Criteria text `payload_url` is implemented by the explicit `*_uri` field names (`audio_uri`, `segment_uri`) defined in this plan.
- **Scope**:
  - Update `speech-lib` to enforce non-secret object reference semantics.
  - Rollout Claim Check to **Gateway**, **VAD**, and **ASR** services.
  - Formalize the lifecycle ownership (MinIO policy) for the entire platform.
- **Out of Scope**:
  - Complex tiered storage (Glacier).
  - Presigned URL generation for public access (Deferred to Gateway read-path implementation).

## Contract Decisions (Blocking)

### 4.1 Message / Schema Contracts
- **Evolution**: Additive `BACKWARD` compatible.
- **Semantics**: **XOR** Invariant (Inline Bytes VS Object Reference).
- **Object Reference Field**: `*_uri` (simple string).
  - **Decision**: Use `*_uri` fields (e.g., `audio_uri`, `segment_uri`) as the canonical contract.
  - **Internal Semantics**: The string MUST match the format `s3://{bucket}/{key}`. It MUST NOT be a presigned URL.
  - **Required Metadata**: 
    - Producers MUST populate existing `audio_format` and `sample_rate_hz` fields when using `*_uri`.
    - **Contract**: `audio_format` MUST be **`wav`** (implying PCM16) for all persisted audio artifacts in this MVP to ensure auditability.
    - For `AudioSynthesisEvent`, `content_type` MUST be populated.
    - For events lacking explicit `content_type` (Input/Segment), consumers SHALL assume `audio/wav` for MVP.
- **Payload Cap**:
  - **Threshold**: **1.25 MiB** (App-level safe limit allows headroom for 1.5 MiB Architecture hard cap).
  - **Inline**: Max 1.25 MiB.
  - **Reference**: Mandatory for > 1.25 MiB.

### 4.2 Speaker Context
- N/A for this plan (persistence mechanism only).

### 4.3 Data Retention & Privacy
- **Retention**: 24 hours (default).
- **Enforcement**: Centralized MinIO Lifecycle Policy (`minio-init/lifecycle.json`) applied to all relevant buckets.
  - **Owner**: Platform Infrastructure (`minio-init`).
  - **Buckets**:
    - `audio-ingress` (Gateway)
    - `vad-segments` (VAD)
    - `asr-transcripts` (ASR - future proofing)
    - `tts-audio` (TTS)
  - **Evidence**: `docker-compose` logs show successful policy application; QA verification script confirms objects expire.
- **Privacy**: Keys MUST NOT contain PII.
  - **Canonical Key Scheme**: `{stage}/{correlation_id}.{ext}`
    - Gateway: `s3://audio-ingress/{correlation_id}.wav`
    - VAD: `s3://vad-segments/{correlation_id}/{segment_index}.wav`
    - ASR: `s3://asr-transcripts/{correlation_id}.json` (if text payload > cap)
    - TTS: `s3://tts-audio/{correlation_id}.wav`

### 4.4 Observability Contract
- **Trace Propagation**: Services MUST propagate `traceparent` via **Kafka Headers** (not payload fields) to ensure end-to-end traceability of Claim Check operations.
- **Structured Logs**: All producers MUST emit structured logs for claim check operations containing at least: `correlation_id`, `event_name` (e.g., `claim_check_offload`), `transport_mode` (`uri`|`inline`), `payload_size_bytes`, and `threshold_bytes`.
- **Failure Signal**: If storage is required (payload > cap) but unavailable/disabled:
  - **Action**: DROP the event (Do NOT produce oversized message).
  - **Signal**: Log ERROR with `event=claim_check_drop`, `correlation_id`, `reason=storage_unavailable`.
  - **Metric**: `claim_check_failures_total` (counter).

## Work Packages

### WP1: Shared Library Hardening (Claim Check Core)
**Objective**: Shared library primitives enforce the "Internal Reference" guardrail.
- **Deliverable 1.1**: `ObjectStorage` helper updated to define `s3://bucket/key` formatting logic, strictly adhering to the canonical bucket names (`audio-ingress`, `vad-segments`, `tts-audio`, etc.).
- **Deliverable 1.2**: A reusable `ClaimCheckPayload` primitive (pure logic) available to all services (encapsulates "Inline vs Reference" selection).
  - **Constraint**: Must be a thin primitive. NO orchestration logic (routing, retries) inside the library.
- **Acceptance Criteria**:
  - Tests prove the helper returns `s3://audio-ingress/...` style URIs by default.
  - Helper allows service to detect "storage unavailable" without crashing the process (return specific exception/status).

### WP2: Infrastructure Lifecycle Rollout
**Objective**: Centralize retention policy for all stages.
- **Deliverable 2.1**: Centralized `minio-lifecycle.json` created (replaces service-specific files).
- **Deliverable 2.2**: `minio-init` bootstrap script updated to:
  - Iterate over required buckets: `audio-ingress`, `vad-segments`, `asr-transcripts`, `tts-audio`.
  - Create each bucket and apply the shared `minio-lifecycle.json` policy.
- **Acceptance Criteria**: Starting the environment results in all buckets existing with the correct 24h expiry configuration active.

### WP3: Gateway Service Persistence
**Objective**: Gateway offloads large input audio using the standard pattern.
- **Deliverable 3.1**: Gateway produces `AudioInputEvent` with `audio_uri` (`s3://audio-ingress/...`) when payload > 1.25 MiB.
- **Deliverable 3.2**: Gateway logs and drops event if storage is required but unavailable (deterministic failure).
- **Acceptance Criteria**: Large audio inputs result in stored objects and valid Kafka events with references; no oversized messages produced.

### WP4: VAD Service Persistence
**Objective**: VAD offloads large segments using the standard pattern.
- **Deliverable 4.1**: VAD produces `SpeechSegmentEvent` with `segment_uri` (`s3://vad-segments/...`) for large segments.
- **Acceptance Criteria**: Large segments are offloaded; tracing context is preserved via Headers.

### WP5: ASR Service Persistence (Optional/Future Proofing)
**Objective**: ASR offloads large transcripts (rare, but standardizes the pattern).
- **Deliverable 5.1**: ASR produces `TextRecognizedEvent` with `text_uri` (`s3://asr-transcripts/...`) if transcript size exceeds inline cap.
- **Acceptance Criteria**: Pattern consistent with other services.

### WP6: TTS Service Alignment (Retrofit)
**Objective**: Align TTS pilot with standardized platform pattern.
- **Deliverable 6.1**: TTS service refactored to use the hardened WP1 shared library primitives and canonical bucket `tts-audio`.
- **Deliverable 6.2**: Service-local lifecycle config removed (superseded by WP2).
- **Acceptance Criteria**: TTS continues to function with new shared code; no regression in large payload handling.

## Risks & Mitigations
- **Risk**: ASR transcripts almost never exceed 1MB; implementing this might be YAGNI.
  - **Mitigation**: WP5 is low priority; can use the shared primitive "just in case" to avoid special casing ASR.
- **Risk**: Key collision on retries (Last Write Wins).
  - **Mitigation**: Accepted for MVP.

## Rollout / Rollback
- **Rollout**: Deploy Lib/Infra -> Deploy Services.
- **Rollback**: None (New capability). If storage fails, system degrades to "Small Payloads Only" mode (Log-and-Drop).
