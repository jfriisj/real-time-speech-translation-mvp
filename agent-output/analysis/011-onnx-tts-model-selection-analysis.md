# Value Statement and Business Objective
Delivery of the TTS service for Epic 1.7 depends on a model that can run consistently on both CPU and GPU while meeting the RTF/latency targets; an ONNX-backed Kokoro-82M implementation provides that runtime stability for the immediate iteration and lets us prove the dual-mode transport, correlation, and speaker-context contracts without carrying the heavier IndexTTS-2 weights. We also want the pipeline to remain model-agnostic so that future releases can swap in other voices or architectures (e.g., Qwen3-TTS variants, IndexTeam/IndexTTS-2) with minimal retraining of downstream logic.

## Changelog
| Date | Summary |
|------|---------|
| 2026-01-25 | Added ONNX-first candidate analysis plus model-agnostic pipeline guidance to support future IndexTTS and Qwen3-TTS iterations. |

## Objective
Clarify whether `onnx-community/Kokoro-82M-v1.0-ONNX` is the best ONNX candidate today, surface its prerequisites (phoneme tokens, style vectors, quantizations, runtime), document the constraints it introduces, and capture the architectural guardrails needed to keep the service ready for later model swaps.

## Context
- Plan 010 mandates dual-mode transport, speaker-context propagation, MinIO retention, and RTF/latency measurement for the TTS service.
- The existing `synthesizer.py` (services/tts/src/tts_service/synthesizer.py) hardcodes `IndexTeam/IndexTTS-2` and expects a Hugging Face pipeline, so it cannot immediately host an ONNX-based graph or the different libraries that future models (Qwen3-TTS, IndexTTS) depend on.
- We do not yet have runtime evidence that any proposed model meets the Success Metrics (RTF < 1.0, latency P50 < 2s) across CPU/GPU combinations, nor that downstream consumers can stay compatible when we swap the synthesizer implementation.

## Root Cause
The current synthesizer implementation is tightly scoped to IndexTTS-2 and its `indextts` dependency, so swapping to a different engine requires (1) reworking the inference path, (2) adding new pre/post-processing (phonemes, voice vectors), and (3) ensuring the new dependencies are safely mocked in tests. Without a lightweight, ONNX-friendly candidate, we would either introduce significant runtime instability or delay the feature entirely.

## Methodology
- Reviewed Plan 010, existing implementation artifacts (`synthesizer.py`, `pyproject.toml`), and released dependency versions (tts-service 0.5.0, torch >=2.6.0, transformers >=4.36) to understand current constraints on third-party libraries.
- Gathered data from Hugging Face for the ONNX candidate (`onnx-community/Kokoro-82M-v1.0-ONNX` README, model metadata) and other ONNX TTS releases (Piper-based variants) to compare licenses, quantization support, and tooling requirements.
- Identified future non-ONNX models (mlx-community Qwen3-TTS-12Hz variants, IndexTeam/IndexTTS-2) to reason about what a pluggable pipeline must accommodate.
- Tool readiness check: `pyproject.toml` currently lacks `onnxruntime` or phoneme libraries (`misaki`), so adding Kokoro will require explicit dependency reviews plus GPU-aware runtime selection (CPU `onnxruntime` vs `onnxruntime-gpu`).
- Version audit: recorded that the service is at version 0.5.0, so any new dependency should target the same release cycle and document its compatibility with existing runtimes.

## Findings
### Facts
- `IndexTTS2Synthesizer` only accepts `IndexTeam/IndexTTS-2` (services/tts/src/tts_service/synthesizer.py) and raises if another model name is provided, so it cannot host the ONNX or Qwen families today.
- `onnx-community/Kokoro-82M-v1.0-ONNX` is Apache-2.0 licensed, exposes several quantized graphs (`model.onnx`, `model_fp16.onnx`, `model_q8f16.onnx`, etc.), runs via `onnxruntime.InferenceSession`, and expects explicit phoneme tokens plus a style vector derived from a voice-specific binary (`voices/<name>.bin`). The README instructs how to convert text to tokens using `hexgrad/misaki` and the Kokoro config, pad to <=510 tokens, and pair tokens with the style vector, `speed`, and then call the session to get 24 kHz audio.
- Kokoro ships dozens of precomputed voices (af_*, am_*, etc.), each with a sample WAV that can be used for speaker-context verification. It also publishes multiple quantized checkpoints down to ~86 MB, which should let us tune RTF vs audio fidelity.
- There are only a couple of ONNX TTS alternatives (Piper-based deployments), and those have either MIT or AGPL licenses and fewer speaker variants, making Kokoro the best fit for now while still aligning with Apache licensing.
- The Qwen3-TTS releases (e.g., `mlx-community/Qwen3-TTS-12Hz-0.6B-Base-4bit`) share the `mlx-audio` runtime and do not provide ONNX graphs; they currently require `mlx-audio` and the `safetensors` weights, so switching to them will likely need a separate code path and different dependency set than the ONNX Kokoro graph.

### Hypotheses
- Using Kokoro's ONNX graphs will force us to insert a phoneme/tokenization pipeline (`misaki`, config mapping) before inference and to persist the voice/style binaries so that `speaker_id` can map to a known style vector (e.g., `speaker_id` -> `af_bella`). Without that mapping, we cannot honor the speaker-context contract and may have to fall back to a default voice.
- The ONNX runtime path will need configuration to select between CPU (`onnxruntime`) and GPU (`onnxruntime-gpu`) providers so that the TPU cluster (if any) can reuse the same inference code while tuning RTF. If we only deploy the CPU provider, GPU paths (Qwen, Index) would require a different loader anyway.
- Because both Kokoro and future models expect different inputs (Kokoro needs `input_ids` and `style`, Qwen/Index expect text or speaker prompts in their own format), we must decouple the pre-inference logic from the transport contract so that we can switch the synthesizer implementation via configuration at runtime.

## Recommendations
- Replace the current `Synthesizer` implementation with a strategy that loads a configurable backend. The default backend should instantiate the Kokoro ONNX graph, handle downloading the selected quantization/model variant, and expose the same `synthesize(text, speaker_reference_bytes)` signature so the rest of the service remains unchanged.
- Build a `speaker_id` -> Kokoro voice map (e.g., `default` -> `af_bella`, `en-male` -> `am_eric`) plus fallback to a neutral voice. Store the binary voice vectors (`voices/<name>.bin`) alongside the model assets, and provide initialization code that loads the correct style vector before inference.
- Introduce the new dependencies (`onnxruntime`/`onnxruntime-gpu`, `numpy` already present, plus `misaki` or another phoneme converter) and ensure they are mocked for unit tests via `tests/conftest.py`; add configuration knobs for CPU/GPU provider selection to keep the runtime stable.
- Prototype Kokoro inference for at least two quantized checkpoints (e.g., `model_q8f16.onnx` and `model_fp16.onnx`) to measure RTF on the target hardware; capture sample metrics (inference time, CPU/GPU usage, payload size) before choosing the default quantization for production.
- Document the steps needed to swap models: include a `MODEL_NAME` config, separate downloader/cache, and `SynthesizerFactory` that can instantiate `IndexTTS2Synthesizer`, `KokoroOnnxSynthesizer`, or a future `QwenSynthesizer`. This will be the switch we flip when moving to `Qwen3-TTS-12Hz-0.6B-Base` or back to `IndexTeam/IndexTTS-2` later.

## Open Questions
- Can we meaningfully translate `speaker_reference_bytes` into Kokoro’s style vectors, or do we have to treat the provided audio merely as a trigger to pick a voice name? The README suggests style vectors are chosen by sequence length, not speaker audio, so we need to confirm how to keep the speaker-context contract intact.
- Which quantized graph gives the best balance between audio fidelity, file size, and RTF across CPUs we control? Is `model_q8f16.onnx` fast enough on the configured worker, or do we need `model_fp16` on GPUs?
- What loader will `mlx-community/Qwen3-TTS` expect once we switch, and how many new dependencies (e.g., `mlx_audio`, custom tokenizers) will we have to inject into the container? Will that require a new synthesizer interface, or can the Kokoro path be extended?
- Do we need to keep IndexTTS available as part of the same release (for fallback) while we exercise Kokoro, or can we release Kokoro-only and revisit IndexTTS later?

## Next Steps
- Build a Kokoro ONNX prototype that (1) downloads the model and voice binaries, (2) runs the provided inference snippet, and (3) measures inference time/RTA on the target infrastructure.
- Define the configuration-driven synthesizer factory and add the new dependencies plus mocks so that tests run without hitting ONNX assets.
- Capture the `speaker_id` to voice/style mapping in configuration/config map and include instructions for how to extend it when new voices or Qwen/Index models are added.
- Document the switching story so the planner can describe how to restore IndexTTS or adopt Qwen3-TTS in a later iteration without changing the message schema or deployment topology.
