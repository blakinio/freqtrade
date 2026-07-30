---
task_id: FTAI-20260730-closure-time-leakage
status: completed
branch: agent/closure-time-leakage-terminal
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 777
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

## Terminal result

- PR #777 merged normally into `develop` as `979744f1143246bd42e42fc2213c7e79fc68ea57`.
- The merged scheduler provides deterministic UTC closed-bar scheduling for configured base and higher timeframes.
- Bars remain unavailable before close and confirmation time; `available_at > decision_time` fails closed.
- Duplicate events are idempotent, conflicting duplicates and out-of-order history are rejected, and later data cannot rewrite emitted history.
- Canonical payload hashing and replay tests prove deterministic append-only parity.
- Canonical UTC, HTF, pivot, feature, simulator and leakage contracts remain unchanged.

## Deliverables

- Deterministic UTC closed-bar scheduling for base and higher timeframes.
- Late, duplicate, out-of-order and boundary-time behavior.
- Append-only replay parity tests.
- Fail-closed handling for naive time and unconfirmed bars.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- No changes outside exact implementation ownership were required.

## Acceptance evidence

- Identical input manifests produce identical schedules and canonical SHA-256 values.
- No bar is available before its close or configured confirmation time.
- Historical output remains append-only and cannot be rewritten by later observations.
- Focused tests, AI Strategy Engine CI, full Freqtrade CI and security analysis passed.
- PR #777 changed exactly the five declared owned paths and had zero unresolved review threads.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T16:52:00+02:00
head: 979744f1143246bd42e42fc2213c7e79fc68ea57
branch: agent/closure-time-leakage-terminal
pr: 777
status: completed
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
  - PR 777 merged normally into develop as 979744f1143246bd42e42fc2213c7e79fc68ea57.
  - Implementation head 6ea38ca9b39587534b88be92be9d362e56814674 added deterministic UTC scheduling for configured base and higher timeframes.
  - Naive or non-UTC timestamps, unconfirmed bars, pre-close detection and available_at after decision_time fail closed with typed reason codes.
  - Late bars use actual detection time, exact close boundaries are accepted, duplicates are idempotent, and conflicting duplicates or out-of-order history are rejected.
  - Canonical schedule hashing and replay tests prove identical manifests and append-only historical prefixes remain deterministic.
  - PR 777 changed exactly the five owned paths and had no review comments, unresolved threads, path overlap or shared-contract mutation.
  - AI Strategy Engine run 30534705422 passed package tests, Ruff, mypy, compile, deterministic E2E, schema and security-boundary checks.
  - Freqtrade CI run 30534705379 passed pre-commit, documentation, Python 3.11-3.14 core tests, coverage, build and the terminal CI Gate.
  - GitHub Actions Security Analysis run 30534705382 passed zizmor security analysis.
derived:
  - The scheduler is an isolated standard-library timing boundary and requires no shared model, feature formula, simulator or leakage-guard change.
  - The time/leakage workstream has no remaining autonomous implementation, validation, review or merge action.
unknown: []
conflicts: []
first_failure:
  marker: NONE
  evidence: All implementation, deterministic replay, exact-head CI, review and merge gates passed.
rejected_hypotheses:
  - Existing inline simulator checks are a reusable scheduling boundary.
  - This task may redefine canonical timestamp, HTF, pivot or leakage contracts.
  - A late or conflicting bar may rewrite previously emitted history.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-time-leakage.md
  - ai_strategy_engine/src/strategy_engine/timing/__init__.py
  - ai_strategy_engine/src/strategy_engine/timing/closed_bar_scheduler.py
  - ai_strategy_engine/tests/unit/test_closed_bar_scheduler.py
  - ai_strategy_engine/tests/integration/test_closed_bar_scheduler_replay.py
validation:
  - command: python -m py_compile strategy_engine/timing/closed_bar_scheduler.py tests/test_closed_bar_scheduler.py tests/test_closed_bar_scheduler_replay.py
    result: PASS
    evidence: Isolated Python 3.13 syntax validation completed without output.
  - command: pytest -q
    result: PASS
    evidence: Isolated focused scheduler suite completed with 13 passed.
  - command: AI Strategy Engine run 30534705422
    result: PASS
    evidence: Exact implementation head passed tests, Ruff, mypy, compile, deterministic E2E, schemas and security scans.
  - command: Freqtrade CI run 30534705379
    result: PASS
    evidence: Exact implementation head passed the Linux Python 3.11-3.14 matrix and terminal CI Gate.
  - command: GitHub Actions Security Analysis run 30534705382
    result: PASS
    evidence: Exact implementation head completed zizmor security analysis successfully.
  - command: PR 777 merge, changed-file and review-thread inspection
    result: PASS
    evidence: Squash merge 979744f1143246bd42e42fc2213c7e79fc68ea57, exactly five owned paths and zero unresolved review threads.
blockers: []
next_action: Closure coordinator consumes the merged scheduler from develop at or after 979744f1143246bd42e42fc2213c7e79fc68ea57 and continues the remaining program-closure integration.
```
