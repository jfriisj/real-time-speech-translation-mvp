# Implementation 009: Voice Activity Detection (VAD) Service

## Plan Reference
- [agent-output/planning/009-voice-activity-detection-plan.md](agent-output/planning/009-voice-activity-detection-plan.md)

## Date
- 2026-01-19

## Changelog

| Date | Handoff/Request | Summary |
|------|------------------|---------|
| 2026-01-19 | Implementation | Added SpeechSegmentEvent schema, VAD service, ASR dual-mode input support, compose wiring, unit tests, and v0.4.0 release stub. |
| 2026-01-19 | Plan revision sync | Plan updated with measurement methodology; no implementation changes required in this update. |

## Implementation Summary
Implemented Epic 1.6 by introducing a VAD microservice that consumes `AudioInputEvent`, detects speech segments, and publishes `SpeechSegmentEvent` keyed by `correlation_id`. Added the new Avro schema, shared library payload class and topic constant, and updated ASR to support dual-mode input selection via `ASR_INPUT_TOPIC` (defaulted to VAD output in Compose). This delivers the value statement by filtering silence prior to ASR, reducing downstream compute while preserving deterministic ordering.

## Milestones Completed
- [x] Shared schema + speech-lib updates (`SpeechSegmentEvent`, topic constant, payload class).
- [x] VAD service added with ONNX/energy-based segmentation and configurable thresholds.
- [x] ASR dual-mode input topic selection (legacy or segmented).
- [x] Compose wiring updated to include VAD and default ASR to VAD output.
- [x] Version management: created v0.4.0 release stub.
- [ ] QA artifact updates (QA docs are QA-owned; not modified).

## Files Modified

| Path | Description | Lines |
| --- | --- | --- |
| [docker-compose.yml](docker-compose.yml) | Added VAD service and default ASR input topic to `speech.audio.speech_segment`. | 147 |
| [services/asr/README.md](services/asr/README.md) | Documented `ASR_INPUT_TOPIC`. | 19 |
| [services/asr/src/asr_service/config.py](services/asr/src/asr_service/config.py) | Added `ASR_INPUT_TOPIC` setting. | 28 |
| [services/asr/src/asr_service/main.py](services/asr/src/asr_service/main.py) | Dual-mode input schema selection + segment-index logging. | 130 |
| [services/asr/tests/test_processing.py](services/asr/tests/test_processing.py) | Added schema selection tests. | 81 |
| [shared/speech-lib/src/speech_lib/constants.py](shared/speech-lib/src/speech_lib/constants.py) | Added `TOPIC_SPEECH_SEGMENT`. | 11 |
| [shared/speech-lib/src/speech_lib/events.py](shared/speech-lib/src/speech_lib/events.py) | Added `SpeechSegmentPayload` validation. | 94 |
| [shared/speech-lib/src/speech_lib/__init__.py](shared/speech-lib/src/speech_lib/__init__.py) | Exported new topic/payload. | 43 |
| [shared/speech-lib/tests/test_events.py](shared/speech-lib/tests/test_events.py) | Added payload validation tests. | 74 |

## Files Created

| Path | Purpose | Lines |
| --- | --- | --- |
| [shared/schemas/avro/SpeechSegmentEvent.avsc](shared/schemas/avro/SpeechSegmentEvent.avsc) | New VAD output schema. | 29 |
| [services/vad/Dockerfile](services/vad/Dockerfile) | VAD service container definition. | 41 |
| [services/vad/pyproject.toml](services/vad/pyproject.toml) | VAD service packaging and deps. | 31 |
| [services/vad/README.md](services/vad/README.md) | VAD service usage/configuration. | 28 |
| [services/vad/CHANGELOG.md](services/vad/CHANGELOG.md) | VAD service changelog. | 4 |
| [services/vad/src/vad_service/__init__.py](services/vad/src/vad_service/__init__.py) | Package init. | 1 |
| [services/vad/src/vad_service/config.py](services/vad/src/vad_service/config.py) | VAD env configuration. | 46 |
| [services/vad/src/vad_service/main.py](services/vad/src/vad_service/main.py) | VAD consumer/producer pipeline. | 185 |
| [services/vad/src/vad_service/processing.py](services/vad/src/vad_service/processing.py) | Audio decoding, segmentation, and wav slicing. | 218 |
| [services/vad/src/vad_service/vad.py](services/vad/src/vad_service/vad.py) | ONNX VAD loader + inference helper. | 82 |
| [services/vad/tests/test_processing.py](services/vad/tests/test_processing.py) | VAD unit tests (synthetic wav). | 114 |
| [agent-output/releases/v0.4.0.md](agent-output/releases/v0.4.0.md) | v0.4.0 release tracking stub. | 50 |

## Code Quality Validation
- [x] Ruff lint via analyzer on all changed Python files (no issues).
- [x] Unit tests executed for speech-lib, ASR, and VAD processing.
- [ ] Integration tests (pipeline smoke) pending.

## Value Statement Validation
**Original**: Filter out silence before ASR to reduce compute waste and improve latency.
**Implementation**: Added VAD service to emit speech-only segments and wired ASR to consume segmented input by default in Compose, preserving `correlation_id` ordering to keep latency/compute improvements measurable.

## Test Coverage
- **Unit**: Added tests for `SpeechSegmentPayload`, ASR schema selection, and VAD segmentation logic.
- **Integration**: Planned pipeline smoke tests not run (requires Kafka/Compose run).

## Test Execution Results

| Command | Result | Notes |
| --- | --- | --- |
| `pytest shared/speech-lib/tests/test_events.py services/asr/tests/test_processing.py services/vad/tests/test_processing.py` | Passed | 6 tests passed. |

## Outstanding Items
- Integration smoke tests for Pipeline A/B (Ingress → VAD → ASR → Translation) not executed.
- QA/UAT reports pending; QA docs are QA-owned and not modified in this implementation.
- Validate ONNX model filename for `onnx-community/silero-vad` in the target environment; energy-based fallback logs warning if model load fails.

## Next Steps
- QA to execute integration pipeline smoke and validate acceptance criteria.
- UAT to confirm latency/efficiency improvements on representative speech samples.

## Assumption Log

| Description | Rationale | Risk | Validation Method | Escalation |
| --- | --- | --- | --- | --- |
| ONNX model filename `silero_vad.onnx` exists in `onnx-community/silero-vad`. | Common naming in HF repos. | Model download failure at build/runtime. | Build VAD container and verify model download. | Moderate (update config if filename differs). |
| QA/UAT prompt guidance files are not accessible from this workspace. | `read_file` is restricted outside workspace. | Missing guidance could affect reporting format. | Rely on repo conventions; request access if needed. | Minor (documented here). |

