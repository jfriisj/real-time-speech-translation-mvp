# UAT Report: Plan 010 Text-to-Speech (TTS) Service (Kokoro ONNX)

**Plan Reference**: `agent-output/planning/010-text-to-speech-plan.md`
**Date**: 2026-01-26
**UAT Agent**: Product Owner (UAT)

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-26 | QA | QA Complete, ready for value validation | UAT Failed - core value evidence incomplete (audio quality, speed control, latency/RTF). |

## Value Statement Under Test
As a User, I want to hear the translated text spoken naturally, So that I can consume the translation hands-free.

## UAT Scenarios
### Scenario 1: Synthesized audio output for translated text
- **Given**: A `TextTranslatedEvent` is produced by the translation service.
- **When**: TTS consumes the event and synthesizes audio.
- **Then**: An `AudioSynthesisEvent` is emitted with payload mode inline or URI.
- **Result**: PASS
- **Evidence**: QA smoke tests for inline + URI in [agent-output/qa/010-text-to-speech-qa.md](agent-output/qa/010-text-to-speech-qa.md)

### Scenario 2: Dual-mode payload transport (inline vs URI)
- **Given**: Small and large synthesized payloads.
- **When**: Payload exceeds inline limit.
- **Then**: `audio_uri` is used and is retrievable.
- **Result**: PASS
- **Evidence**: URI smoke test in [agent-output/qa/010-text-to-speech-qa.md](agent-output/qa/010-text-to-speech-qa.md)

### Scenario 3: Natural audio quality and intelligibility
- **Given**: The curated phrase set in tests/data/metrics/tts_phrases.json.
- **When**: Samples are generated and listened to.
- **Then**: Audio is intelligible with no artifacts.
- **Result**: FAIL
- **Evidence**: No human playback evidence or artifact review recorded in [agent-output/qa/010-text-to-speech-qa.md](agent-output/qa/010-text-to-speech-qa.md) or [agent-output/implementation/010-text-to-speech-implementation.md](agent-output/implementation/010-text-to-speech-implementation.md)

### Scenario 4: Speed control produces measurable duration shift
- **Given**: `TTS_SPEED` is changed from default.
- **When**: Synthesis runs with the updated speed.
- **Then**: Output duration changes by ≥10% without breaking audio quality.
- **Result**: FAIL
- **Evidence**: No measurements reported in [agent-output/qa/010-text-to-speech-qa.md](agent-output/qa/010-text-to-speech-qa.md)

### Scenario 5: Real-time factor and latency targets
- **Given**: RTF < 1.0 and P50 latency < 2000ms targets.
- **When**: Synthesis is executed on reference hardware.
- **Then**: Targets are met.
- **Result**: FAIL
- **Evidence**: No RTF/latency measurements recorded in [agent-output/qa/010-text-to-speech-qa.md](agent-output/qa/010-text-to-speech-qa.md)

## Value Delivery Assessment
Partial. The pipeline emits `AudioSynthesisEvent` in both inline and URI modes, which supports the end-to-end loop. However, the value statement depends on natural, intelligible speech and validated speed control. Those are not evidenced, and RTF/latency targets are unverified. As a result, the business outcome (“spoken naturally, hands-free”) is not yet demonstrated.

## QA Integration
**QA Report Reference**: `agent-output/qa/010-text-to-speech-qa.md`
**QA Status**: QA Complete
**QA Findings Alignment**: QA confirms unit coverage and integration smoke tests but does not verify audio quality, speed control, or RTF/latency targets.

## Technical Compliance
- Plan deliverables:
  - Dual-mode transport: PASS
  - Pluggable synthesizer: PASS (code-level)
  - Observability fields (model_name, latency): PARTIAL (not validated in logs)
  - Speed control: FAIL (not validated)
  - Audio quality check: FAIL (not validated)
- Test coverage: 79% for TTS module per QA
- Known limitations: No RTF/latency measurements; no human audio validation

## Objective Alignment Assessment
**Does code meet original plan objective?**: PARTIAL
**Evidence**: Emission of `AudioSynthesisEvent` proven in QA smoke tests, but the user-facing quality criteria are unverified.
**Drift Detected**: None; gap is missing value evidence, not scope drift.

## UAT Status
**Status**: UAT Failed
**Rationale**: Core value outcomes (natural audio quality, speed control, and performance targets) lack evidence. Without these, the “hands-free, natural speech” objective is unproven.

## Release Decision
**Final Status**: NOT APPROVED
**Rationale**: Business value not sufficiently demonstrated against plan acceptance criteria.
**Recommended Version**: Hold v0.5.0 until audio quality + speed control + RTF/latency evidence exists.
**Key Changes for Changelog**:
- TTS service emits `AudioSynthesisEvent` in inline and URI modes.
- Kokoro ONNX backend wired via pluggable synthesizer factory.

## Next Actions
- Capture audio quality evidence (manual playback of 5 samples) and record results.
- Validate speed control (`TTS_SPEED`) with measurable duration change ≥10%.
- Record RTF and latency P50 for the curated phrase set.
