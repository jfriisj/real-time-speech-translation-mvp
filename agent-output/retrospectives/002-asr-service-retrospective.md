# Retrospective 002: Audio-to-Text Ingestion (ASR Service)

**Plan Reference**: `agent-output/planning/002-asr-service-plan.md`
**Date**: 2026-01-15
**Retrospective Facilitator**: retrospective

## Summary
**Value Statement**: As a User, I want my speech audio to be captured and converted to text events, So that the system has raw material to translate.
**Value Delivered**: YES
**Implementation Duration**: Same-day (2026-01-15)
**Overall Assessment**: High-quality implementation delivering MVP functionality with strong guardrails (wav-only, 1.5MB limit). The process was smooth until the final release step, where a secret scanning violation blocked the push.
**Focus**: Preventing secret leakage and maintaining "Contract-First" discipline.

## Timeline Analysis
| Phase | Planned Duration | Actual Duration | Variance | Notes |
|-------|-----------------|-----------------|----------|-------|
| Planning | - | - | - | Plan 002 was reused/revised effectively. |
| Implementation | - | - | - | Completed with high quality (Docker, tests, code). |
| QA | - | - | - | All tests passed; CPU benchmark added value. |
| UAT | - | - | - | Confirmed value delivery and MVP constraints. |
| Release | - | - | - | Blocked by GitHub Secret Scanning. |
| **Total** | < 1 day | < 1 day | - | Fast cycle, derailed by security block at finish line. |

## What Went Well (Process Focus)
### Workflow and Communication
- **Contract-First Success**: The plan explicitly defined topics and schemas (`speech.audio.ingress`, `speech.asr.text`, `TextRecognizedEvent`), and the implementation adhered to them without drift. This indicates the lesson from Retrospective 001 (Roadmap Alignment) was learned and applied.
- **Guardrail Enforcement**: The decision to "Log and Drop" oversized/invalid payloads was correctly implemented and verified in QA, protecting the system from stability risks in the MVP phase.

### Agent Collaboration Patterns
- **Seamless QA/UAT**: The handoff from QA (functional verification) to UAT (value verification) was frictionless. Both agreed on the "Ready" status, with QA providing the necessary evidence for UAT to approve quickly.
- **Proactive Benchmarking**: The QA/Implementation phase included a CPU latency benchmark script `benchmark_latency.py`, adding tangible data to the "feasibility" assessment.

### Quality Gates
- **Packaging Integrity**: The release process again included a packaging build check (`python -m build`), which successfully verified the artifacts (despite the known warning).
- **Security Scanning (External)**: GitHub's secret scanning worked exactly as intended, catching a committed secret before it could be pushed to the remote repository. This is a critical safety net.

## What Didn't Go Well (Process Focus)
### Workflow Bottlenecks
- **Secret Leakage**: A Hugging Face user token was committed to `.vscode/mcp.json`. This halted the release process (`git push` blocked).
    - **Root Cause**: The MCP tool configuration likely included a sensitive token in a file tracked by git.
    - **Impact**: Release blocked; remediation required (history rewrite or token revocation + removal).

### Agent Collaboration Gaps
- **Secret Management**: The agent system allowed a secret to be written to a tracked file. There should be a stricter rule or pattern for handling secrets (e.g., using environment variable references in MCP headers/config rather than literals).

### Quality Gate Failures
- **Secret Detection (Local)**: We relied on the *remote* (GitHub) to catch the secret. A local pre-commit check or agent-side heuristic could have prevented the commit entirely.
- **Deprecation Warning**: The `project.license` warning in `pyproject.toml` persists. It wasn't fixed in this cycle, contributing to technical debt.

### Misalignment Patterns
- None detected. The contract, topics, and scope remained aligned throughout.

## Agent Output Analysis

### Changelog Patterns
**Total Handoffs**: 5 phases (Plan -> Impl -> QA -> UAT -> Release).
**Handoff Chain**: planner -> implementer -> qa -> uat -> release -> retrospective.

| From Agent | To Agent | Artifact | What Requested | Issues Identified |
|------------|----------|----------|----------------|-------------------|
| Planner | Implementer | Plan 002 | Implementation | - |
| Implementer | QA | Impl Report | Verification | - |
| QA | UAT | QA Report | Value Alignment | - |
| UAT | Release | UAT Report | Release | - |
| Release | Retro | Release Doc | Lessons | Blocked by secret scanning |

**Handoff Quality Assessment**:
- Extremely clean. Artifacts were consistent in version (`0.2.0`), naming, and scope.
- The only break was technical (blocked push), not communicative.

### Issues and Blockers Documented
**Total Issues Tracked**: 2 (Secret Scanning, License Warning).

| Issue | Artifact | Resolution | Escalated? | Time to Resolve |
|-------|----------|------------|------------|-----------------|
| Secret Scanning | Release Doc | Blocked / Pending | Yes | Open |
| License Warning | Release Doc | Noted | No | Open |

**Issue Pattern Analysis**:
- **Security**: The most critical pattern is the mishandling of secrets in configuration files.
- **Tech Debt**: The license warning is a recurring low-priority noise item.

### Changes to Output Files
**Artifact Update Frequency**:
- Plan: 0 updates (stable).
- Implementation: 1 creation.
- QA: 1 creation.
- UAT: 1 creation.
- Release: 1 creation (blocked status).
- **Assessment**: Efficient.

## Technical Debt Incurred
- **License Config**: `pyproject.toml` uses a table for `project.license` (deprecated). Remediation needed by 2026-02-18.
- **Secret Remediation**: `git history` now contains a secret in `92fc0fc`. This technically pollutes the local history even if not pushed.

## Follow-Up Actions
- [ ] **Immediate**: Remove the secret from `.vscode/mcp.json` and squash/amend the commit before pushing. (DevOps)
- [ ] **Process**: Update `mcp.json` guidance to use `${env:VAR}` syntax or ignored config files for secrets. (Process Improvement)
- [ ] **Tech Debt**: Update `services/asr/pyproject.toml` (and others) to use the SPDX string format for `project.license`. (Implementer)

## Metrics
**Lines of Code Changed**: ~436 insertions (per git log).
**Files Modified**: 10 (Plan, changelogs, new service code).
**Tests Added**: 5 (Unit) + 1 (Integration) + 1 (Benchmark).
**Tests Passed**: 100%.
**Bugs Found in QA**: 0 functional; 1 security (at release).
**UAT Issues**: 0.

## Related Artifacts
- **Plan**: `agent-output/planning/002-asr-service-plan.md`
- **QA Report**: `agent-output/qa/002-asr-service-qa.md`
- **UAT Report**: `agent-output/uat/002-asr-service-uat.md`
- **Release**: `agent-output/releases/v0.2.0.md`
