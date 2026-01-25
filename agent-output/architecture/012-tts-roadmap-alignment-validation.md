# Roadmap Alignment Validation: Epic 1.7 (TTS)

**Date**: 2026-01-25
**Scope**: Validation of Epic 1.7 (Text-to-Speech with IndexTTS-2) against Architecture Findings 011 and System Architecture.
**Status**: ALIGNED

## Epic Definition (Roadmap)
- **User Story**: "hear the translated text spoken naturally... hands-free."
- **Dependencies**: Epic 1.3 (Translation output).
- **Key Features**: IndexTTS-2 (Hugging Face), Zero-Shot voice cloning, `AudioSynthesisEvent`.

## Architecture Alignment (Findings 011 + System Architecture)

### 1. Payload & Transport Strategy
- **Roadmap Constraint**: "Consumer hands-free" implies audible length output.
- **Problem**: Synthesized audio frequently exceeds the 1.5 MiB inline cap.
- **Architectural Solution**: Findings 011 explicitly recommends **Option D2 (Dual-mode inline-or-URI)**.
    - *Validation*: This directly supports the user story. If only inline was allowed, the system would fail for long sentences ("natural" speech). The dual-mode decision enables "natural" length while respecting infrastructure limits.

### 2. Voice Cloning / Speaker Context
- **Roadmap Feature**: "Zero-Shot capabilities (voice cloning)... Configurable Reference Speaker".
- **Architectural Constraint**: System Architecture mandate: "Speaker context MUST be optional... degraded gracefully."
- **Architectural Solution**: Findings 011 supports propagation via inline reference or embedding.
    - *Validation*: The roadmap asks for "configuration," and architecture provides the mechanism (context propagation + optionality). The mandate to "degrade gracefully" prevents feature bloat from blocking core functionality.

### 3. Latency & Measurement
- **Roadmap Goal**: "Performance" / "Efficiency" (Thesis hypothesis).
- **Architectural Constraint**: Findings 011 (Constraint G) mandates "measurable performance... Real-Time Factor (RTF)".
- **Process Improvement**: PI-009 mandates "Success Metric Measurement Method" in the plan.
    - *Validation*: The requirement for RTF measurement in architecture perfectly aligns with the thesis goals in the roadmap.

## Gaps / Risks
- **Object Store Complexity**: The "Dual-mode" recommendation implies a MinIO/S3 dependency. This is widely standard but technically "new infrastructure" for the MVP.
    - *Mitigation*: The plan must explicitly define the local dev setup (e.g., MinIO container in docker-compose) to avoid breaking "single-command bring-up."

## Conclusion
The architectural approach (Findings 011) fully supports the Epic 1.7 outcomes. It proactively solves the "large payload" blocker that would otherwise cause the "natural speech" requirement to fail in the existing infrastructure.

**Verdict**: Proceed to Planning (Plan 010).
