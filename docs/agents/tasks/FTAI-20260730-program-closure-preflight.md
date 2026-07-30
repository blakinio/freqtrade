---
task_id: FTAI-20260730-program-closure-preflight
status: validating
branch: agent/program-closure-preflight
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
program: FTAI-PROGRAM-AI-TRADING-PORTAL
dependencies:
  - PR #759 merged
owned_paths:
  - docs/agents/tasks/FTAI-20260730-program-closure-preflight.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - ai_strategy_engine/TASKS.md
search_first:
  - current develop, open PRs and active owned paths
  - code, tests, merged PRs and exact-head CI for every unchecked item
---

# Program closure preflight

## Goal

Produce the evidence-backed Gate 0 closure matrix, freeze shared ownership, create only real-gap task records and publish a complete manual dispatch graph.

## Gate 0 result

- PR #759 was repaired only for its exact codespell failure and merged normally after green exact-head CI and zero unresolved review threads.
- Every unchecked P0, P1 and P2 backlog item is classified in `PROGRAM_CLOSURE_MATRIX.md`.
- Shared contracts have one exclusive child owner and a version and compatibility policy.
- Ten child records exist: nine repository or integration workstreams plus one blocked owner-managed external lane.
- Exact child implementation paths are pairwise disjoint.
- P11 and repository privacy are owner actions; live capital remains deferred and unauthorized.

## Validation

Run every child checkpoint validator, structural ownership checks, documentation checks and required exact-head CI before merging this branch.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T10:55:00+02:00
head: 1d347a785eddc900f4484c30e06c3ab4e8851b29
branch: agent/program-closure-preflight
pr: null
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-program-closure-preflight.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
proven:
  - PR #759 merged as 1d347a785eddc900f4484c30e06c3ab4e8851b29 after exact-head Freqtrade CI and workflow security succeeded.
  - The matrix classifies every unchecked backlog item and separates repository, external and live-capital lanes.
  - Child task implementation paths are pairwise disjoint and shared contracts have one exclusive owner.
derived:
  - Contracts, closed-bar scheduling, support and resistance and simulator fidelity can begin immediately after Gate 0 merge.
  - Research Data, AI routing and ranking, both frontend tasks and final integration must wait for their recorded dependencies.
unknown:
  - Exact child PR numbers and workflow run IDs until workers execute.
conflicts: []
first_failure:
  marker: PUBLIC_REPOSITORY_VISIBILITY
  evidence: GitHub repository metadata reports visibility public; the owner must change this setting to satisfy the private-repository boundary.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts.
  - Repository fixtures may be described as real external acceptance.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-program-closure-preflight.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - docs/agents/tasks/FTAI-20260730-closure-contracts.md
  - docs/agents/tasks/FTAI-20260730-closure-time-leakage.md
  - docs/agents/tasks/FTAI-20260730-closure-feature-engine.md
  - docs/agents/tasks/FTAI-20260730-closure-simulator.md
  - docs/agents/tasks/FTAI-20260730-closure-research-data.md
  - docs/agents/tasks/FTAI-20260730-closure-ai-routing-ranking.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md
  - docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md
  - docs/agents/tasks/FTAI-20260730-closure-external-staging.md
validation:
  - command: python tools/agents/checkpoint.py <each-created-task> --require-checkpoint
    result: PASS
    evidence: All Gate 0 and child checkpoints satisfy governance contract v1.
  - command: Gate 0 ownership intersection check
    result: PASS
    evidence: No two child tasks declare the same exact mutable path.
  - command: Backlog classification coverage check
    result: PASS
    evidence: Every unchecked P0, P1 and P2 item appears exactly once in the matrix.
blockers:
  - Repository visibility is public and requires an owner setting change; this does not block autonomous repository implementation.
next_action: Validate exact-head CI and review threads for the Gate 0 PR, repair only evidenced failures, synchronize normally if needed, and merge it.
```
