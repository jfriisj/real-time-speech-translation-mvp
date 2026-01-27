# Analysis 010: Text-to-Speech (TTS) Plan Unknowns

**Date**: 2026-01-27
**Related Plan**: agent-output/planning/010-text-to-speech-plan.md
**Purpose**: Surface technical unknowns that must be resolved before executing the plan.

## Questions to Answer
1. **Model tokenization requirements**
   - Question: Does the Kokoro ONNX bundle expect phonemized input or raw text, and what tokenizer/token set must we ship to the service? (Success = document the tokenizer, lexicon, and how it is initialized in the container.)
2. **Object storage availability & fallback**
   - Question: In environments without MinIO/S3, what is the documented behavior when a large payload exceeds `MAX_INLINE_BYTES`? (Success = ship documented fallback behavior and configuration flag that disables URI generation.)
3. **Quantifying WAV duration per byte**
   - Question: What duration of synthesized WAV (sample rate 24k, 16-bit) fits within the 1.25 MiB inline budget, so we can sensibly warn users before dropping payloads? (Success = provide bytes-to-duration reference table/formula.)
4. **GPU runtime readiness**
   - Question: What runtime dependencies (CUDA/cuDNN) are required when switching to `onnxruntime-gpu`, and how will the container detect support? (Success = list required packages, driver versions, and detection strategy.)
5. **Latency/RTF measurement baseline**
   - Question: What script or load pattern should we use to capture service-level latency/RTF for the curated phrase set (serving as QA evidence)? (Success = provide command plus metrics to record.)

## Methodology
- Interviewed Architect notes (Findings 011/013/015).
- Reviewed master architecture to capture message-size invariants and claim-check requirements.
- Studied Plan 010 to identify missing data (tokenization, fallback behavior, automation hooks).

## Findings
1. **Tokenization**: Kokoro requires phoneme sequences; we need to bundle the same tokenizers as the model release and confirm license. Without confirmation, implementing `KokoroSynthesizer` risks mismatch.
2. **Storage Fallback**: Plan now states storage is optional, but no configuration entry exists; implementation must add env flag and doc for what happens when the bucket is missing.
3. **Duration Guidance**: Inline cap is 1.25 MiB but duration depends on sample rate; we need a helper to convert to seconds to provide warnings.
4. **GPU Dependencies**: No hardware/driver guidance currently; we need to document which CUDA/cuDNN versions are compatible and how the plan ensures `onnxruntime-gpu` only runs where `CUDAExecutionProvider` is available.
5. **Performance Evidence**: QA requires latency and RTF numbers; define script/resolution.

## Recommendations
1. Capture tokenizer spec and embed within `services/tts` (vendor license check). Create issue for confirming input format.
2. Add plan section explaining `DISABLE_STORAGE=true` fallback plus log behavior.
3. Provide helper function or doc for bytes→seconds (24kHz, 16-bit stereo/mono) to enforce inline caps.
4. Add future plan (011) details as references for GPU readiness; include driver/package table.
5. Define test script (curl + faker event) to record latency/RTF.

## Next Steps
- Confirm Kokoro tokenizer requirements and embed steps in plan.
- Document storage fallback behavior (env flag, log/drop).
- Provide duration reference for inline payload.
- Reference GPU runtime requirements and detection strategy.
- Draft latency/RTF measurement script for QA evidence.