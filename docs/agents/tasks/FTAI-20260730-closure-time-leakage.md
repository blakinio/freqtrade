---
task_id: FTAI-20260730-closure-time-leakage
status: ready
branch: agent/closure-time-leakage
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
dependencies:
  - none
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-time-leakage.md
  - ai_strategy_engine/src/strategy_engine/timing/__init__.py
  - ai_strategy_engine/src/strategy_engine/timing/closed_bar_scheduler.py
  - ai_strategy_engine/tests/unit/test_closed_bar_scheduler.py
  - ai_strategy_engine/tests/integration/test_closed_bar_scheduler_replay.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - ai_strategy_engine/TASKS.md
search_first:
  - current develop, open PRs and exact owned-path conflicts
  - canonical implementation and tests before adding code
  - shared contract freeze commit and dependency state
---

# Closure closed-bar scheduling

## Goal

Implement the missing reusable closed-bar scheduler without changing already proven UTC, HTF, pivot, point-in-time or leakage contracts.

## Evidence at Gate 0

UTC validation, timestamp ordering, HTF confirmation, pivot delay, future-shift and target-leakage rejection already have implementation and tests. No reusable scheduler module exists.

## Deliverables

- Deterministic UTC closed-bar scheduling for base and higher timeframes.
- Late, duplicate, out-of-order and boundary-time behavior.
- Append-only replay parity tests.
- Fail-closed handling for naive time and unconfirmed bars.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.

## Acceptance criteria

- Identical input manifests produce identical schedules.
- No bar is available before its close or confirmation time.
- Historical output cannot be rewritten by later data.

## Validation

Run narrow tests first, then all repository workflows required by the changed paths. Validate this task checkpoint before every handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T10:55:00+02:00
head: 1d347a785eddc900f4484c30e06c3ab4e8851b29
branch: agent/closure-time-leakage
pr: null
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-time-leakage.md
  - ai_strategy_engine/src/strategy_engine/timing/__init__.py
  - ai_strategy_engine/src/strategy_engine/timing/closed_bar_scheduler.py
  - ai_strategy_engine/tests/unit/test_closed_bar_scheduler.py
  - ai_strategy_engine/tests/integration/test_closed_bar_scheduler_replay.py
proven:
  - UTC validation, timestamp ordering, HTF confirmation, pivot delay, future-shift and target-leakage rejection already have implementation and tests. No reusable scheduler module exists.
derived:
  - The bounded implementation scope is restricted to 5 exact path entries.
unknown:
  - Exact implementation HEAD, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: PRE_IMPLEMENTATION_GATE
  evidence: Implementation has not started; the Gate 0 dispatch condition is the first enforced gate.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts.
  - Repository fixtures may be described as real external acceptance.
changed_paths: []
validation:
  - command: python tools/agents/checkpoint.py <task-path> --require-checkpoint
    result: PASS
    evidence: Gate 0 validates this compact checkpoint before dispatch.
blockers: []
next_action: Create the branch from current develop, implement the isolated scheduler and tests, and open one focused PR.
```
