---
task_id: FTAI-20260730-program-closure-preflight
status: validating
branch: agent/program-closure-preflight
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 767
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
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
search_first:
  - current develop, open PRs and active owned paths
  - code, tests, merged PRs and exact-head CI for every unchecked item
---

# Program closure preflight

## Goal

Produce the evidence-backed Gate 0 closure matrix, freeze shared ownership, create only real-gap task records and publish a complete manual dispatch graph.

## Gate 0 result

- PR #759 merged normally as `1d347a785eddc900f4484c30e06c3ab4e8851b29`.
- Gate 0 synchronized normally with `develop` through PR #768 and again through PR #774 at `develop@d57c12b030259d0ae5931306c3e3046713e2e8aa`.
- PR #766 merged the canonical inherited validation repair with green exact-head Freqtrade, AI Platform, Portal, WickHunter and security workflows.
- Duplicate repair PR #770 was closed without merge as `DUPLICATE_OR_SUPERSEDED`.
- Every one of the 73 unchecked P0/P1/P2 backlog entries is classified exactly once.
- Shared contracts have one exclusive child owner and an explicit compatibility policy.
- Ten child records exist: nine repository/integration workstreams plus one blocked owner-managed P11 lane.
- All 69 exact child mutable-path declarations are pairwise disjoint and exclude active PR #761/#762/#758 paths.
- Private Freqtrade means a private runtime/API boundary; GitHub repository visibility is not a Gate 0 blocker.
- P11 remains external, P13 remains measured-need-only and live capital remains unauthorized.

## Validation

Run every child checkpoint validator, structural ownership checks, documentation checks and required exact-head CI before merging this branch.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T12:05:00+02:00
head: 354c21832d2bfd60d38baef4c7bccd513ba6386f
branch: agent/program-closure-preflight
pr: 767
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
  - PR #759 merged normally; PR #768 and PR #774 synchronized current develop into Gate 0 without force push.
  - PR #766 passed exact-head Freqtrade, AI Platform, Portal, WickHunter and security CI and merged as `ac545041046e618c477e0ab5d999e11d261a742e`.
  - PR #770 was closed without merge because PR #766 already supplied the canonical repair.
  - The matrix classifies all 73 unchecked P0, P1 and P2 items exactly once.
  - Ten child task records exist with one exclusive shared-contract owner.
  - All 69 exact child mutable-path declarations are pairwise disjoint and exclude active adjacent PR paths.
  - The manual dispatch table lists every exact child mutable path and start condition.
derived:
  - Contracts, closed-bar scheduling, support and resistance and simulator fidelity can start after Gate 0 merges.
  - Research Data, AI routing and ranking, both frontend tasks and final integration must wait for recorded dependencies.
unknown:
  - Exact-head CI conclusions and unresolved review-thread state after this checkpoint commit.
conflicts: []
first_failure:
  marker: EXACT_HEAD_VALIDATION_PENDING
  evidence: The Gate 0 PR head moved after normal synchronization and checkpoint refresh; required exact-head CI and review verification must complete before merge.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - Public GitHub source visibility is equivalent to a public Freqtrade runtime or browser execution path.
  - A duplicate repair should merge after its canonical equivalent has already merged.
  - Repository fixtures may be described as real P11 acceptance.
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
    evidence: All eleven Gate 0 and child task checkpoints passed against the repository governance contract.
  - command: Gate 0 ownership intersection check
    result: PASS
    evidence: 69 owned-path declarations are unique with zero exact collisions.
  - command: Gate 0 next-action cardinality check
    result: PASS
    evidence: Every Gate 0 and child checkpoint contains exactly one next_action.
  - command: Backlog classification coverage check
    result: PASS
    evidence: All 73 unchecked P0, P1 and P2 entries appear exactly once with an allowed status.
blockers:
  - Exact-head required CI and review-thread verification remain pending after this commit.
next_action: Verify PR #767 exact-head CI and unresolved review threads, repair only evidenced failures, synchronize normally if develop advances, and merge normally when green.
```
