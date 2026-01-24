# UAT Report: Plan 009 Voice Activity Detection (VAD) Service

**Plan Reference**: `agent-output/planning/009-voice-activity-detection-plan.md`
**Date**: 2026-01-24
**UAT Agent**: Product Owner (UAT)

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-24 | QA | Validate business value after QA completion claim | UAT Complete - QA complete with WER guardrail validated; value delivered with duration reduction and quality preserved |

## Value Statement Under Test
As a System Architect, I want to filter out silence *before* the heavy ASR service, so that I don't waste GPU/CPU cycles transcribing background noise and latency is improved.

## UAT Scenarios
### Scenario 1: Legacy baseline path still works (Pipeline A)
- **Given**: ASR consumes `speech.audio.ingress` directly
- **When**: Audio is produced to ingress
- **Then**: ASR and Translation emit outputs for the same `correlation_id`
- **Result**: PASS
- **Evidence**: [agent-output/qa/009-voice-activity-detection-qa.md](agent-output/qa/009-voice-activity-detection-qa.md)

### Scenario 2: VAD path produces end-to-end outputs (Pipeline B)
- **Given**: VAD consumes `AudioInputEvent` and emits `SpeechSegmentEvent`
- **When**: Audio is produced to ingress
- **Then**: ASR and Translation emit outputs for the same `correlation_id`
- **Result**: PASS
- **Evidence**: [agent-output/qa/009-voice-activity-detection-qa.md](agent-output/qa/009-voice-activity-detection-qa.md)

### Scenario 3: Success metric (audio duration reduction ≥ 30%)
- **Given**: Sparse-speech dataset per plan methodology
- **When**: VAD segments are produced and durations aggregated
- **Then**: Reduction ≥ 30%
- **Result**: PASS (72.9% reduction)
- **Evidence**: [agent-output/qa/009-voice-activity-detection-qa.md](agent-output/qa/009-voice-activity-detection-qa.md)

### Scenario 4: Transcript-quality guardrail (WER ≤ 5pp)
- **Given**: Baseline and VAD transcripts with reference text
- **When**: WER is computed for both paths
- **Then**: WER degradation ≤ 5pp
- **Result**: PASS (WER delta 0.0)
- **Evidence**: [agent-output/qa/009-vad-metric-summary.json](agent-output/qa/009-vad-metric-summary.json)

## Value Delivery Assessment
Value delivered. The compute-efficiency goal is supported by average 85.1% audio duration reduction on the sparse-speech dataset and the transcript-quality guardrail is met ($\Delta \text{WER}=0.0$), indicating no quality regression while reducing downstream ASR workload.

## QA Integration
**QA Report Reference**: `agent-output/qa/009-voice-activity-detection-qa.md`
**QA Status**: QA Complete
**QA Findings Alignment**: QA confirms success metric and WER guardrail validation completed; UAT aligns with this evidence.

## Technical Compliance
- Plan deliverables: PASS (core pipeline + success metric + WER guardrail validated)
- Test coverage: Unit + integration smoke tests complete; success metric and WER guardrail validated
- Known limitations: Single-node Kafka prevents multi-partition ordering validation

## Objective Alignment Assessment
**Does code meet original plan objective?**: YES
**Evidence**: VAD reduces audio duration by ~85% on sparse-speech dataset and preserves transcription quality (WER delta 0.0), meeting the efficiency and guardrail requirements.
**Drift Detected**: None.

## UAT Status
**Status**: UAT Complete
**Rationale**: Business value requirements (efficiency + quality guardrail) are validated; pipeline delivers intended outcomes.

## Release Decision
**Final Status**: APPROVED FOR RELEASE
**Rationale**: Efficiency and quality guardrail objectives are validated with QA evidence.
**Recommended Version**: Minor bump (v0.4.0)
**Key Changes for Changelog**:
- Added VAD stage with new `SpeechSegmentEvent` contract
- ASR dual-mode input support and Compose wiring

## Next Actions
- Optional: validate ordering across multi-partition Kafka when available
