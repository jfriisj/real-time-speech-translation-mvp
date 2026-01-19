# Analysis 005: Ingress Gateway Implementation Questions

**Plan Reference (if any)**: agent-output/planning/005-ingress-gateway-plan.md  
**Status**: Draft

## Changelog

| Date | Agent Handoff | Request | Summary |
|------|---------------|---------|---------|
| 2026-01-19 | Planner | Investigate technical unknowns for Ingress Gateway plan | Identified decision points around stream buffering, wav synthesis, and publication triggering that must be resolved before implementation. |

## Objective
Answer the remaining technical unknowns required to finalize the Ingress Gateway implementation plan so the work can be scoped to an executable ticket.

## Context
- Relevant modules/files:
  - services/gateway/ (to be created) for HTTP/WebSocket server + optional gRPC server.
  - `speech-lib` shared contract for Avro serialization of `AudioInputEvent`.
  - docker-compose entrypoint for `gateway-service`.
- Known constraints:
  - Audio payload must be valid WAV, ≤1.5 MiB, for compatibility with the current ASR contract.
  - No streaming/event chunking yet (Epic 3.1 handles that later).
  - Gateway must support at least WebSocket; gRPC is secondary but desirable.
  - Each client should map to a single `AudioInputEvent` so the ASR consumption behavior remains unchanged.

## Methodology
- Reviewed the roadmap plan to extract explicit requirements.
- Surveyed available Python libs (FastAPI websockets, grpcio, standard `wave` module) to confirm they support the needed buffering and PCM-to-WAV conversion without additional dependencies.
- Cross-checked the shared architecture ADRs to ensure the Gateway can emit `AudioInputEvent` inline and still preserve the `correlation_id`/schema expectations.

## Findings

### Facts
- FastAPI supports binary WebSocket messages and can stream them via `await websocket.receive_bytes()` loops; gRPC streaming can be implemented with a `StreamAudio` server-streaming RPC that receives `bytes` chunks.
- The standard library `wave` module can wrap PCM bytes into a WAV file by writing headers once the total duration is known; it only requires specifying sample rate, channels, and bytes-per-sample.
- `speech-lib` already defines `AudioInputEvent` fields; to produce a new event the Gateway must provide `payload.audio_format = "wav"` plus the serialized `.wav` bytes and a `correlation_id`.
- The plan’s buffer limit of 1.4 MiB leaves room for WAV headers while staying within Kafka’s 1.5 MiB cap (per Decision: Message size policy). Buffering in memory is acceptable for a handful of concurrent clients but requires capping connections/config.

### Hypotheses
- **Hypothesis 1**: WebSocket clients can signal end-of-stream either by closing the socket or sending a sentinel message (e.g., `{"event":"done"}`) so Gateway knows when to finalize a WAV buffer.
- **Hypothesis 2**: gRPC streaming can reuse the same buffering logic by requiring an explicit `EndStream` proto message (or closing the stream) before the Gateway serializes to WAV.
- **Hypothesis 3**: A simple in-memory buffer with per-connection limits (e.g., 1.5 MiB) plus an asyncio Lock per client is sufficient to prevent memory storms for the MVP workload (<10 simultaneous loaders).

## Recommendations
- Finalize the Gateway buffering contract: define the WebSocket sentinel message, a gRPC `EndStream` signal, and the invariant that each stream publishes only one `AudioInputEvent` with a `correlation_id` (preferably client-supplied when available).
- Implement buffering by accumulating PCM bytes in `io.BytesIO`, convert to WAV using the standard `wave` module once the stream signals completion, and enforce the 1.4 MiB cap before publishing to Kafka.
- Apply per-connection limits (max concurrent streams, max chunk size) and fail fast for oversized payloads to protect memory, documenting these thresholds in the plan’s constraints section.

## Open Questions
- Should the Gateway accept a client-provided `correlation_id`, or must it generate one and return it in a handoff message for debugging/traceability?
- What is an acceptable concurrency limit (number of active WebSocket sessions) before backpressure or connection limits need to be enforced for the MVP?
- Is gRPC support essential for the initial release, or can it be delivered in a follow-up sprint once the WebSocket path proves stable?

## Handoff

**To**: Implementer / Planner updating the plan
**Status**: Draft
**Key Context**: Buffering streaming clients, converting PCM to WAV, enforcing message-size limits, and ensuring each connection results in a single `AudioInputEvent` are the remaining decisions.
**Recommended Action**: Resolve the open questions above and update Plan 005 with explicit streaming contracts before moving to implementation.