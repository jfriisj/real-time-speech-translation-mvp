# Future Plan 011: GPU Validation for TTS (Kokoro ONNX)

**Created**: 2026-01-26
**Owner**: Implementation
**Source**: Plan 010 Rev 20 follow-up requirement

## Objective
Validate the GPU runtime profile for the Kokoro ONNX TTS service and produce evidence that the service runs reliably on GPU with measured latency/RTF.

## Scope
- Build and run a GPU-enabled container profile using `onnxruntime-gpu`.
- Verify provider selection (`CUDAExecutionProvider`) works end-to-end.
- Capture service-level latency and RTF metrics on reference GPU hardware.

## Out of Scope
- New model swaps (IndexTTS/Qwen).
- Architectural changes to the event schema.

## Required Artifacts
- `agent-output/validation/gpu_tts_profile.md` with:
  - GPU hardware details
  - Driver/CUDA versions
  - Container image tag and runtime config
  - RTF and latency metrics for the curated phrase set
- `agent-output/validation/gpu_tts_logs.txt` (sanitized)

## Acceptance Criteria
- TTS service runs with `CUDAExecutionProvider` without fallback to CPU.
- Emits `AudioSynthesisEvent` for the curated phrase set.
- Reports latency/RTF metrics for n=10 runs.

## Dependencies
- GPU-capable host
- `onnxruntime-gpu` wheels available for the runtime Python version
- Container image build pipeline for GPU profile
