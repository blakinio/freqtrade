---
task_id: FTAI-20260730-closure-time-leakage
status: in_progress
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
updated_at: 2026-07-30T12:16:00+02:00
head: 91ddbf60c986ff2a85f24ab0416ec1274e5f1460
branch: agent/closure-time-leakage
pr: null
status: in_progress
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
  - Gate 0 classifies only the reusable closed-bar scheduler as REAL_GAP; UTC, timestamp ordering, HTF, pivot and leakage guards are already canonical and read-only for this task.
  - Current develop is 91ddbf60c986ff2a85f24ab0416ec1274e5f1460.
  - Open PRs 758, 761 and 762 do not overlap any owned path.
derived:
  - The scheduler can remain an isolated standard-library timing module and consume no mutable shared contract.
unknown:
  - Exact implementation HEAD, PR number and CI run IDs until implementation is published.
conflicts: []
first_failure:
  marker: IMPLEMENTATION_NOT_STARTED
  evidence: The branch and ownership checkpoint exist, but scheduler code and focused tests are not yet committed.
rejected_hypotheses:
  - Existing inline simulator checks are a reusable scheduling boundary.
  - This task may change proven domain, feature, pivot or leakage contracts.
  - A late bar may be inserted by rewriting previously emitted history.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-time-leakage.md
validation:
  - command: repository/live-state preflight
    result: PASS
    evidence: Gate 0 READY, exact branch absent before creation, no owned-path overlap, and no contract dependency.
blockers: []
next_action: Open the focused draft PR, implement the isolated scheduler and add deterministic unit and replay tests.
```
