---
task_id: FTAI-20260730-closure-time-leakage
status: ready
branch: agent/closure-time-leakage
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
updated_at: 2026-07-30T12:43:00+02:00
head: 6ea38ca9b39587534b88be92be9d362e56814674
branch: agent/closure-time-leakage
pr: 777
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
  - Gate 0 classifies only the reusable closed-bar scheduler as REAL_GAP; canonical UTC, HTF, pivot and leakage contracts remain unchanged.
  - Implementation head 6ea38ca9b39587534b88be92be9d362e56814674 adds deterministic UTC scheduling for configured base and higher timeframes.
  - Naive or non-UTC timestamps, unconfirmed bars, pre-close detection and available_at after decision_time fail closed with typed reason codes.
  - Late bars use actual detection time, exact boundaries are accepted, duplicates are idempotent, conflicting duplicates and out-of-order history are rejected.
  - Canonical schedule hashing and replay tests prove identical manifests and append-only historical prefixes remain deterministic.
  - PR 777 changes exactly the five owned paths and has no review comments, unresolved threads, path overlap or shared-contract mutation.
  - AI Strategy Engine run 30534705422 passed package tests, Ruff, mypy, compile, deterministic E2E, schema and security-boundary checks.
  - Freqtrade CI run 30534705379 passed pre-commit, documentation, Python 3.11-3.14 core tests, coverage, build and the CI Gate.
  - GitHub Actions Security Analysis run 30534705382 passed and develop remained at 91ddbf60c986ff2a85f24ab0416ec1274e5f1460 during implementation validation.
derived:
  - The scheduler is an isolated standard-library timing boundary and requires no shared model, feature formula, simulator or leakage-guard change.
  - The task-record-only readiness commit may be merged after its exact-head required checks pass.
unknown:
  - Exact squash merge commit until PR 777 is merged normally.
conflicts: []
first_failure:
  marker: NONE
  evidence: No implementation, focused-validation, CI, ownership or review failure remains at the validated implementation head.
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
  - command: PR 777 changed-file, diff, review-thread and live-base inspection
    result: PASS
    evidence: Exactly five owned paths, mergeable draft, zero reviews or threads and unchanged develop base.
blockers: []
next_action: Mark PR 777 ready and squash-merge it normally after the task-record-only exact-head required checks pass.
```
