# UAT Report: Plan 010 Text-to-Speech (TTS) Service (Kokoro ONNX)

**Plan Reference**: `agent-output/planning/010-text-to-speech-plan.md`
**Date**: 2026-01-26
**UAT Agent**: Product Owner (UAT)

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-26 | QA | QA Complete, ready for value validation | UAT Failed - value evidence incomplete (intelligibility, retention proof, service-level latency). |

## Value Statement Under Test
As a User, I want to receive intelligible spoken audio for translated text, So that I can consume the translation without reading.

## UAT Scenarios
### Scenario 1: Synthesized audio output for translated text
- **Given**: A `TextTranslatedEvent` is produced by the translation service.
- **When**: TTS consumes the event and synthesizes audio.
- **Then**: An `AudioSynthesisEvent` is emitted with payload mode inline or URI.
- **Result**: PASS
- **Evidence**: Prior QA smoke tests in [agent-output/qa/010-text-to-speech-qa.md](agent-output/qa/010-text-to-speech-qa.md)

### Scenario 2: Dual-mode payload transport (inline vs URI)
- **Given**: Small and large synthesized payloads.
- **When**: Payload exceeds inline limit.
- **Then**: `audio_uri` is used and is retrievable.
- **Result**: PASS
- **Evidence**: Prior URI smoke test evidence in [agent-output/qa/010-text-to-speech-qa.md](agent-output/qa/010-text-to-speech-qa.md)

### Scenario 3: Intelligible audio quality
- **Given**: The curated phrase set in tests/data/metrics/tts_phrases.json.
- **When**: Samples are generated and listened to.
- **Then**: Audio is intelligible and understandable for 5 samples.
- **Result**: FAIL
- **Evidence**: No human playback evidence captured (missing quality report) in [agent-output/implementation/010-text-to-speech-implementation.md](agent-output/implementation/010-text-to-speech-implementation.md)

### Scenario 4: Speed control produces measurable duration shift
- **Given**: `TTS_SPEED` is changed from default.
- **When**: Synthesis runs with the updated speed.
- **Then**: Output duration changes by ≥10% without breaking audio quality.
- **Result**: PARTIAL
- **Evidence**: Synthesis-only report shows a -15.62% delta in [agent-output/validation/performance_report.md](agent-output/validation/performance_report.md); service-level validation not captured.

### Scenario 5: Service-level latency and RTF logging
- **Given**: CPU baseline run for the curated phrase set.
- **When**: TTS runs through the service entrypoint.
- **Then**: Logs capture `synthesis_latency_ms` and `RTF` for each request.
- **Result**: FAIL
- **Evidence**: Only synthesis-only measurements exist in [agent-output/validation/performance_report.md](agent-output/validation/performance_report.md).

### Scenario 6: MinIO retention policy evidence
- **Given**: `tts-audio` bucket retention policy is required to be 24 hours.
- **When**: Lifecycle rule inspection evidence is captured.
- **Then**: `agent-output/validation/retention-proof.md` exists and documents the rule.
- **Result**: FAIL
- **Evidence**: No retention proof artifact present (file missing).

## Value Delivery Assessment
Partial. The pipeline emits `AudioSynthesisEvent` in both inline and URI modes, supporting the speech-to-speech loop. However, intelligibility evidence, service-level latency/RTF observability, and retention proof are missing. The business outcome (“intelligible spoken audio without reading”) is not yet demonstrated.

## QA Integration
**QA Report Reference**: `agent-output/qa/010-text-to-speech-qa.md`
**QA Status**: QA Complete
**QA Findings Alignment**: QA confirms unit coverage and prior integration evidence, but notes integration smoke tests were not rerun in the latest pass and value evidence remains unverified.

## Technical Compliance
- Plan deliverables:
  - Dual-mode transport: PASS
  - Pluggable synthesizer: PASS (code-level)
  - Input guard (500-char limit): PASS (unit coverage per QA)
  - Observability fields (model_name, latency): NOT VERIFIED (no service-level log evidence)
  - Speed control: PARTIAL (synthesis-only evidence)
  - Audio quality check: FAIL (no human intelligibility evidence)
  - Retention policy evidence: FAIL (artifact missing)
- Test coverage: main.py 79.03% per QA
- Known limitations: No service-latency measurements; no human audio validation; retention proof missing

## Objective Alignment Assessment
**Does code meet original plan objective?**: PARTIAL
**Evidence**: Event emission proven by QA smoke tests; intelligibility and service-level observability requirements remain unverified.
**Drift Detected**: None; gap is missing value evidence, not scope drift.

## UAT Status
**Status**: UAT Failed
**Rationale**: Core value outcomes (intelligibility, service-level observability, retention evidence) lack proof. Without these, the plan’s value statement remains unverified.

## Release Decision
**Final Status**: NOT APPROVED
**Rationale**: Business value not sufficiently demonstrated against plan acceptance criteria.
**Recommended Version**: Hold v0.5.0 until intelligibility, service-level latency/RTF logging, and retention proof are captured.
**Key Changes for Changelog**:
- TTS service emits `AudioSynthesisEvent` in inline and URI modes.
- Kokoro ONNX backend wired via pluggable synthesizer factory.
- Input guard enforces 500-character text limit.

## Next Actions
- Capture audio quality evidence (manual playback of 5 samples) and record results.
- Validate speed control (`TTS_SPEED`) at the service level with measurable duration change ≥10%.
- Record service-level latency/RTF logs for the curated phrase set.
- Capture MinIO lifecycle rule evidence in `agent-output/validation/retention-proof.md`.
