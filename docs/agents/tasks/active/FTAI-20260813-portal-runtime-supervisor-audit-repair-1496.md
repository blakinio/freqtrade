# FTAI-20260813 — Runtime Supervisor fresh-audit repair

```yaml
task_id: FTAI-20260813-portal-runtime-supervisor-audit-repair-1496
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
issue: 1355
continuation_pr: 1496
base_branch: develop
delivery_branch: codex/portal-runtime-supervisor-1355
status: waiting
priority: critical
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
live_capital_authorized: false
protected_production_deployment_authorized: false
invocation_started_at: 2026-08-13T08:58:00+02:00
last_progress_at: 2026-08-13T09:13:00+02:00
ci_checks_for_current_head: 0
pre_checkpoint_head_ci_observations: 2
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 2
context_reconstruction_attempts: 0
stall_warnings: 0
```

## Objective

Close the three material trust-boundary findings from the fresh audit of PR #1496 on the existing delivery PR, remove all one-shot repair workflows, synchronize with current `develop`, and reach exact-head closeout validation without creating another implementation PR.

## Findings and disposition

- `RS-AUDIT-20260813-01 / P1` — **REPAIRED**: failed-runtime cleanup now captures and uses immutable container identity and refuses name-based destructive cleanup when immutable evidence is unavailable.
- `RS-AUDIT-20260813-02 / P1` — **REPAIRED**: distinct authorized lifecycle UID now requires an explicit dedicated filesystem group; trusted root/socket group ownership and access are configured and validated fail-closed.
- `RS-AUDIT-20260813-03 / P1` — **REPAIRED**: execution adapter validates Supervisor outcome tenant/bot/generation/spec-digest/operation/command/correlation identity before trusting returned state/version.

## Owned paths

- `ai_platform/portal/execution/driver.py`
- `ai_platform/portal/execution/adapter.py`
- `ai_platform/portal/runtime_supervisor/transport.py`
- `tests/ai_platform/portal/execution/test_driver.py`
- `tests/ai_platform/portal/execution/test_adapter.py`
- `tests/ai_platform/portal/runtime_supervisor/test_transport.py`
- this task record

The three one-shot repair workflows are no longer owned because they were deleted by product repair commit `4eef00b90e5a5550b15c176c089b1325a911363b` and direct exact-head content lookup returned 404 for each path.

## Acceptance state

- failure cleanup never removes a container by mutable runtime name: **PASS by direct code inspection**;
- immutable container identity is retained and used for failure cleanup: **PASS by direct code inspection**;
- distinct lifecycle UID requires configured group access and unrelated identities remain excluded: **PASS by direct code inspection**;
- same-UID supervisor sockets remain owner-only: **PASS by direct code inspection**;
- adapter validates bounded Supervisor outcome identity: **PASS by direct code inspection**;
- focused Ruff/mypy/tests: **PASS**, run `31676285852`, 106/106 tests;
- one-shot workflow cleanup: **PASS**, product commit `4eef00b90e5a5550b15c176c089b1325a911363b`;
- synchronization with current `develop@0bc9fd995a63fac469fa4f014195f5cc83983dec`: **PASS**, merge-forward candidate `917bf19deb9608c8b91292ae2f951f78b8b8ada9` before this checkpoint-only commit;
- required exact-head CI/E2E: **WAITING** — second/final observation on `917bf19...` had zizmor success, CodeQL/API-mode/Runtime-Isolation in progress and Freqtrade/Component/remaining E2E queued;
- fresh independent post-repair security audit: **WAITING / REQUIRED**;
- merge: **NOT AUTHORIZED until remaining gates pass**.

## Safety

PAPER-only. No deployment, protected-environment mutation, exchange credentials, real orders, withdrawals, LIVE transition, or owner-funded Codex/OpenAI/paid-AI use is authorized or used.

## Context checkpoint

```yaml
checkpoint_version: 2
checkpoint_head: LIVE_BRANCH_HEAD_REQUIRED
pre_checkpoint_head: 917bf19deb9608c8b91292ae2f951f78b8b8ada9
product_repair_commit: 4eef00b90e5a5550b15c176c089b1325a911363b
integrated_develop: 0bc9fd995a63fac469fa4f014195f5cc83983dec
branch: codex/portal-runtime-supervisor-1355
pr: 1496
status: waiting
proven:
  - all three fresh-audit P1 findings are repaired in repository code
  - run 31676285852 passed Ruff, mypy and 106 focused tests
  - all three one-shot repair workflows are absent after product commit 4eef00b
  - branch was merge-forwarded without force to develop@0bc9fd9
waiting_on:
  - terminal required exact-head CI and Runtime Isolation E2E after GitHub Actions queue advances
  - genuinely fresh independent post-repair security audit with independent context
blockers:
  - no permitted independent fresh validator is exposed in the current execution surface; owner-funded Codex/OpenAI/paid-AI is prohibited without separate explicit authorization
next_action: In a fresh invocation, resolve the live branch head from GitHub, observe required exact-head CI/E2E once the queue has advanced, then obtain a permitted genuinely fresh independent security audit; merge only if both gates pass and review/base hygiene remains clean.
```
