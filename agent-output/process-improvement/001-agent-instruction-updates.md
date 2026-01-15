# Process Improvement Updates 001

**Date**: 2026-01-15
**Source Retrospective**: `001-shared-infrastructure-retrospective`
**Analysis**: `agent-output/process-improvement/001-process-improvement-analysis.md`

## Summary
Updated 2 agent instruction files to address process gaps identified in the Shared Infrastructure release.

## Files Updated

### 1. `.github/agents/02-planner.agent.md`
- **Change**: Added "Roadmap Alignment Check" step to `Process` section.
    - *Rationale*: Prevents naming drift (e.g., `AudioProcessingEvent` vs `AudioInputEvent`) by forcing explicit comparison.
- **Change**: Added workspace hygiene requirement to `Core Responsibilities`.
    - *Rationale*: Ensures `.gitignore` and other environment setup tasks are not missed in initial plans.

### 2. `.github/agents/11-devops.agent.md`
- **Change**: Added `git remote -v` validation to `Phase 1: Pre-Release Verification`.
    - *Rationale*: Prevents release failures where tagging succeeds but pushing fails due to invalid remotes.

## Validation Plan
1. **Next Planning Cycle**: Verify the Planner explicitly calls out Roadmap alignment in their thinking/output.
2. **Next Release**: Verify the Release agent checks `git remote` before starting.
