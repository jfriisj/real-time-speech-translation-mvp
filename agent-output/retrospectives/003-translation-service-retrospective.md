# Retrospective 003: Translation Service (v0.2.0)

**Plan Reference**: [agent-output/planning/003-translation-service-plan.md](agent-output/planning/003-translation-service-plan.md)
**Date**: 2026-01-19
**Retrospective Facilitator**: retrospective

## Summary
**Value Statement**: "As a User, I want recognized text to be translated into my target language, So that I can understand the content."
**Value Delivered**: YES
**Implementation Duration**: Fast (Single iteration with one QA blocking cycle)
**Overall Assessment**: High success. The team successfully delivered a working Translation Service with a **real Hugging Face model** (exceeding the planned "Mock" scope) while staying within the CPU-only infrastructure constraints after a critical QA intervention.
**Focus**: Dependency management in containerized Python environments and Plan-to-Code alignment.

## Timeline Analysis
| Phase | Status | Notes |
|-------|--------|-------|
| **Planning** | Available | Plan 003 proposed a "Deterministic Mock" to minimize risk. |
| **Analysis** | Skipped | No dedicated analysis for the late "Mock -> Real" swap; decision was made in-flight. |
| **Implementation** | Completed | Implemented real `OS-Helsinki` model instead of mock. Initial build included CUDA blobs. |
| **QA** | **Blocked** | Caught 5GB+ Docker image causing overlayfs errors. Rejected. |
| **QA (Fix)** | Passed | Implementer switched to CPU-only PyTorch wheels. QA verified integration. |
| **UAT** | Approved | Validated value; accepted the "Real Model" deviation as value-positive. |
| **Release** | Completed | Tagged v0.2.0. |

## What Went Well (Process Focus)
### Workflow and Communication
- **Critical QA Gate**: The QA agent prevented a broken release by flagging the Docker build failure (snapshotter error due to CUDA size). This proved the value of "Operational Safety" testing in QA, not just functional testing.
- **Rapid Remediation**: The loop from QA Rejection -> Implementation Fix (CPU-only wheels) -> QA Pass was executed efficiently without lengthy re-planning.

### Quality Gates
- **UAT Flexibility**: UAT correctly identified that the deviation from Plan (Mock -> Real Model) was **value-positive** and approved it, rather than rejecting it for strict adherence to the deprecated "Mock" strategy.

## What Didn't Go Well (Process Focus)
### Workflow Bottlenecks
- **Late Architectural Shift**: The "No Mocks" rule invocation occurred during implementation. Ideally, the Plan should have been updated to "Proposed - Revision 2" to reflect the Real Model strategy, adjusting the "Milestone 2" deliverables before coding began.

### Technical Patterns (Systemic)
- **Dependency Bloat**: The initial implementation used standard `pip install torch`, which pulls NVIDIA CUDA binaries by default. This nearly broke the local development environment constraints (disk space/I/O).

## Agent Output Analysis

### Changelog Patterns
- **Handoff Chain**: Planner -> Implementer (Mock) -> Implementer (Real/No-Mock) -> QA (Fail) -> Implementer (Fix) -> QA (Pass) -> UAT -> Release.
- **Context Preservation**: Good. The `correlation_id` requirement from the shared infrastructure (Epic 1.1) was correctly preserved and validated in translation (Epic 1.3).

### Issues and Blockers
| Issue | Artifact | Resolution | Complexity |
|-------|----------|------------|------------|
| Docker Overlayfs Error | QA Report | Switched to CPU-only PyTorch wheels | High (Environment blocker) |
| Plan Drift (Mock vs Real) | UAT Report | Accepted as value-add | Medium (Process drift) |

## Process Improvements (Recommendations)

### 1. Standardize "Heavy" Python Dependencies
**Observation**: Python ML libraries (Torch, TensorFlow) default to massive GPU-enabled builds.
**Action**: Create a **Skill** or **Standard Pattern** for "CPU-Only Python Container" that mandates using `--index-url https://download.pytorch.org/whl/cpu` (or equivalent) for MVP services.
**Owner**: Architect / DevOps

### 2. "Plan Drift" Protocol
**Observation**: The implementation significantly exceeded the plan (Real Model vs Mock).
**Action**: When an Implementer changes the fundamental approach (e.g., library vs mock), they should add a **Decision Note** to the Implementation Report header explaining *why*.
**Owner**: Implementer

### 3. Git Tag Stewardship
**Observation**: Release agent had to delete a stale local tag.
**Action**: Release instructions should explicitly include `git tag -l | grep vX.Y.Z` checks and safe deletion as a standard preamble.
**Owner**: Release Agent

## Technical Debt Incurred
- **Model Download Latency**: The integration test had to have its timeout increased (180s) to accommodate the first-run model download.
    - *Remediation*: Future releases should introduce "Model Baking" (downloading models during Docker build) to ensure fast, deterministic startup.

## Follow-Up Actions
- [ ] **Architect**: Document "CPU-Only PyTorch" installation strategy in `docs/` or `shared/` guidelines.
- [ ] **DevOps**: Investigate "Model Baking" in Dockerfile for v0.3.0 to remove runtime network dependency.

## Related Artifacts
- **Plan**: `agent-output/planning/003-translation-service-plan.md`
- **Release**: `agent-output/releases/v0.2.0.md`
- **QA**: `agent-output/qa/003-translation-service-qa.md`
