# Planner Chatmode (Repo Guidance)

This file defines **what “a good plan” looks like** in this repository and how plans will be reviewed.
It is used by:
- **Planner**: as a preflight checklist before handing off.
- **Critic/Reviewers**: as the shared rubric for approval decisions.

## 1) Scope

Applies to documents in:
- `agent-output/planning/`

This guidance focuses on:
- **Clarity** (what will be delivered)
- **Completeness** (what must be decided vs what can be deferred)
- **Alignment** (roadmap + architecture)
- **Risk** (what can go wrong and how we’ll detect it)

## 2) Non-goals / Hard Constraints

A plan in this repo MUST:
- Describe **WHAT and WHY**, not detailed **HOW**.
- Avoid embedding implementation code.
- Avoid writing QA test cases/strategies (QA owns that in `agent-output/qa/`).
- Avoid tuning thresholds/algorithms unless the threshold itself is a **contract** requirement.

## 3) Approval Rubric (what reviewers score)

### A. Roadmap Alignment
- Correct release/version mapping (epic belongs to the right release theme).
- Epic outcome statement matches roadmap wording (no drift).

### B. Architecture Alignment
- Uses the current architecture boundaries and integration points.
- No boundary creep into shared libraries or cross-service responsibilities.

### C. Outcome Clarity
- Clear value statement: **As a [user], I want [capability], so that [value]**.
- Acceptance criteria are **observable outcomes**, not implementation tasks.

### D. Completeness (the “no hidden decisions” test)
- All **contract decisions** are explicitly stated (see Section 4).
- Dependencies are explicit (services, schemas, storage, messaging, observability).

### E. Scope Control
- Tasks are small enough to implement without creating a multi-week refactor.
- Defer non-essential enhancements explicitly (with rationale and a follow-up pointer).

### F. Risk & Rollback Thinking
- Calls out the top 3–5 failure modes.
- Includes minimal “how we’ll know it’s broken” signals (logs/metrics/traces), without prescribing QA.

## 4) Contract Decision Gates (Blocking if missing)

If any of these are relevant to the epic and not explicitly decided, the plan is **NOT APPROVED**.

### 4.1 Message / Schema Contracts
Must define:
- Producer(s) and consumer(s)
- Required fields vs optional fields
- Backward compatibility expectations (versioning strategy)
- Traceability identifiers (correlation IDs, session IDs, request IDs)

### 4.2 Speaker Context Propagation (when TTS/voice/persona is involved)
Must explicitly decide the contract for **speaker context**:
- **Representation**: reference (ID/URI), embedding/vector, or none
- **Origin**: which component is the source of truth (e.g., Gateway vs VAD vs other)
- **Pass-through requirements**: which services must preserve it unchanged
- **Privacy & retention**: TTL expectations, allowed storage locations, and whether it contains PII
- **Failure behavior**: what happens if it’s missing/invalid (degrade gracefully vs hard fail)

### 4.3 Data Retention & Privacy
Must specify:
- What data is persisted vs transient
- Retention/TTL expectations
- Any redaction rules for logs/traces

### 4.4 Observability Contract
Must specify:
- Minimum tracing propagation requirements across services
- Minimal metrics/logging fields needed for debugging latency and correctness (not thresholds)

## 5) Common Plan Anti-patterns (Reviewers will block)

- “How-to” implementation detail (algorithms, model tuning, step-by-step code instructions)
- QA test case lists, detailed test scripts, or benchmark protocols inside the plan
- Hidden contract changes (schema changes without explicit consumers/versioning)
- Mixing unrelated epics into one plan without a clear dependency story

## 6) Recommended Plan Structure (Template)

A plan should include (in roughly this order):
1. Value Statement and Business Objective
2. Context (roadmap epic + architecture references)
3. Deliverables (bulleted, user-visible outcomes)
4. Contract Decisions (schemas, speaker context, privacy/TTL, observability)
5. Work Packages (tasks with acceptance criteria per task)
6. Risks & Mitigations (top risks only)
7. Rollout / Rollback Notes (high level)

## 7) How to Use This File

- **Planner**: treat Section 4 as a hard preflight gate.
- **Critic/Reviewers**: cite missing Section 4 items as “Critical / Blocking”.
- **Implementer**: if Section 4 is ambiguous during implementation, stop and request clarification before coding the contract.
