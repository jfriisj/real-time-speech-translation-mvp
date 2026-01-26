# Retrospective 010: Text-to-Speech (TTS) Service

**Plan Reference**: `agent-output/planning/010-text-to-speech-plan.md`
**Date**: 2026-01-26
**Retrospective Facilitator**: retrospective

## Summary
**Value Statement**: As a User, I want to hear the translated text spoken naturally, So that I can consume the translation hands-free.
**Value Delivered**: NO (UAT Failed)
**Implementation Duration**: 2 days (2026-01-25 to 2026-01-26)
**Overall Assessment**: The technical implementation successfully established the TTS pipeline (infrastructure, events, dual-mode transport), but the specific value proposition ("natural" speech) remains unverified due to lack of human validation and performance metrics. The choice of Python 3.14 introduced friction with ML dependencies (`onnxruntime`).
**Focus**: Dependency management for ML workloads and rigorous UAT for sensory features.

## Timeline Analysis
| Phase | Planned Duration | Actual Duration | Variance | Notes |
|-------|-----------------|-----------------|----------|-------|
| Planning | 0.5 days | 1 day | +0.5 days | Refined logic for large payload handling (URI vs Inline). |
| Analysis | 0.5 days | 0.5 days | 0 | - |
| Implementation | 1 day | 1.5 days | +0.5 days | Delays due to `onnxruntime` compatibility with Python 3.14. |
| QA | 0.5 days | 0.5 days | 0 | Rapid iteration, though blocked by tool/env issues initially. |
| UAT | 0.5 days | 0.5 days | 0 | Failed quickly due to missing qualitative evidence. |
| **Total** | 3 days | 4 days | +1 day | - |

## What Went Well (Process Focus)
### Workflow and Communication
- **Smoke Testing Strategy**: The use of `tests/e2e/tts_pipeline_smoke.py` with Docker Compose effectively validated the complex "Dual-Mode" payload logic (switching to MinIO for large files) without requiring a full frontend.
- **Defensive Planning**: The plan explicitly defined the "Pluggable Synthesizer" (Factory pattern), which allowed the team to pivot from IndexTTS to Kokoro ONNX without rewriting the core service logic.

### Quality Gates
- **Dependency Checks**: QA quickly identified the missing `boto3` dependency in `speech-lib` when running integration tests, preventing a runtime failure in production.
- **UAT Rigor**: UAT correctly refused to pass the feature based solely on code coverage, insisting on the "business value" (audio quality) which had not been demonstrated.

## What Didn't Go Well (Process Focus)
### Technical Risk Assessment
- **Bleeding Edge Python**: The project uses Python 3.14, but `onnxruntime` (required for Kokoro) does not yet publish wheels for 3.14. This caused significant friction in testing and required mocking/stubbing that may mask real runtime issues.
- **Missing Sensory Validation**: The plan defined "Audio Quality" as a metric but did not provision a tool or workflow for the Agent to actually *listen* or validate it (e.g., uploading samples to an artifact store for human review).

### Workflow Bottlenecks
- **Terminal Tool Limitations**: QA was repeatedly blocked by "runTests and terminal tools disabled" or similar access restrictions, forcing workarounds or halting progress.
- **Evidence Gaps**: The Implementer focused on unit tests (79% coverage) but did not produce the "artifacts" (generated .wav files) required for UAT to make a quality judgment.

## Agent Output Analysis

### Changelog Patterns
**Total Handoffs**: 5 (Plan -> Impl -> QA -> Impl -> QA -> UAT)
**Handoff Chain**: planner -> implementer -> qa -> implementer -> qa -> uat

| From Agent | To Agent | Artifact | What Requested | Issues Identified |
|------------|----------|----------|----------------|-------------------|
| QA | Implementer | QA Report | Fix dependency issues (`misaki`/`onnxruntime`) | Python 3.14 compatibility mismatch caught late. |
| QA | UAT | QA Report | Validate Value | QA passed technical tests but UAT rejected due to missing "quality" evidence. |

### Issues and Blockers Documented
| Issue | Artifact | Resolution | Escalated? | Time to Resolve |
|-------|----------|------------|------------|-----------------|
| `onnxruntime` missing for Py3.14 | QA Report | Workaround (mocking/stubbing) | No | 4 hours |
| Missing `boto3` | QA Report | Installed | No | 1 hour |
| UAT Missing Evidence | UAT Report | Unresolved (UAT Failed) | Yes (Release Blocked) | N/A |

### Artifact Update Frequency
- **QA Report**: High churn (updated 8+ times) as tests were re-run and dependencies fixed.
- **Plan**: Stable after initial heavy refinement (13 revisions).

## Technical Debt Incurred
- **Mocked Inference**: Unit tests mock the ONNX runtime. We have low confidence that the model actually works on the target architecture (especially given the Python 3.14 issue).
- **Dependency Pinning**: The project relies on a "bleeding edge" Python version that is hostile to the ML ecosystem. This will likely recur with other ML libraries.

## Follow-Up Actions
- [ ] **Architect**: Review Python version strategy. Consider downgrading to 3.12 or 3.11 for services requiring heavy ML libraries (ONNX, PyTorch) to ensure wheel compatibility.
- [ ] **QA/Implementer**: Create a "Manual Evidence" pattern where the agent generates artifacts (e.g., sample .wav files) and explicit logs of their properties (duration, format) into the `agent-output` folder for UAT to review.
- [ ] **Planner**: For sensory features, include a "Validation Tooling" section in the plan (e.g., "Script to generate 5 sample files").

## Metrics
**Lines of Code Changed**: ~450 (TTS Service + Tests)
**Files Modified**: 8
**Tests Added**: 13 Unit Tests, 2 Integration Smoke Tests
**Test Coverage**: 79% (Unit)
**UAT Issues**: 3 (Quality, Speed, Latency)
