# Architecture Validation 014: Roadmap Alignment (TTS Refresh)

**Date**: 2026-01-27
**Validated By**: Roadmap Agent
**Context**: Re-verification for Epic 1.7 (TTS) following Findings 011/012

## Input Artifacts
- **Roadmap**: `agent-output/roadmap/product-roadmap.md` (v0.5.0 Entry)
- **Architecture**: `agent-output/architecture/system-architecture.md` (Updated)
- **Findings**: 
  - `agent-output/architecture/011-tts-kokoro-onnx-architecture-findings.md`
  - `agent-output/architecture/012-tts-architecture-governance-gaps-architecture-findings.md`

## Validation Summary
**Verdict**: **ARCHITECTURALLY ALIGNED / GOVERNANCE BLOCKED**

The architectural strategy for Epic 1.7 (Kokoro ONNX, Pluggable Factory, Claim Check) is fully aligned with the Roadmap's goals for stability and extensibility. However, the execution planning artifact (`Plan 010`) is missing, which constitutes a critical governance gap inhibiting release verification.

## Detailed Checks

### 1. Technology Strategy (Kokoro ONNX)
- **Roadmap Goal**: "Stable Outcome... Uses Kokoro-82M (ONNX) to ensure reliable runtime on both CPU."
- **Architecture Guardrail (Findings 011)**: "Implement the v0.5.0 TTS backend using Kokoro-82M ONNX... Require a pluggable synthesizer interface."
- **Status**: ✅ **Aligned**. The architecture strictly enforces the roadmap's stability pivot.

### 2. Scalability & Payload Management
- **Roadmap Goal**: "Completes the Speech-to-Speech loop" (implies handling audio output).
- **Architecture Guardrail (Findings 011/013)**: "AudioSynthesisEvent must support either inline audio_bytes OR audio_uri... to protect Kafka payload invariants."
- **Status**: ✅ **Aligned**. The architecture provides the specific mechanism (Claim Check) to enable the user story without crashing the infrastructure.

### 3. Voice Context / Cloning
- **Roadmap Criteria**: "Data flow designed to propagate Source Audio Sample... for cloning context."
- **Architecture Guardrail (Findings 011)**: "Speaker context MUST be optional pass-through metadata... must not force identity semantics."
- **Status**: ✅ **Aligned**. Support is enabled but constrained to prevent scope creep (profiling/identity) that would derail the MVP.

### 4. Governance & Execution
- **Roadmap Status**: "Implementation started; Kokoro ONNX scaffolded."
- **Architecture Status (Findings 012)**: "Plan 010 document is missing from repo... Governance risk identified."
- **Status**: ❌ **Blocked**. The roadmap assumes a plan exists (Rev 8/11/16 referenced), but the file is gone. We cannot validate that the *code* matches the *plan* if the plan is missing.

## Conclusion
The **approach** is sound and fully supports the Epic. The **documentation** is broken.
**Next Step**: The Planner Agent must restore or regenerate `agent-output/planning/010-text-to-speech-plan.md` compliant with Findings 011 before UAT/Release can proceed.
