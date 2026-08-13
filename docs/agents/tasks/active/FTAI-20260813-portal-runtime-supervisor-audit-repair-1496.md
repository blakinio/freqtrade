# FTAI-20260813 — Runtime Supervisor fresh-audit repair

```yaml
task_id: FTAI-20260813-portal-runtime-supervisor-audit-repair-1496
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
issue: 1355
continuation_pr: 1496
base_branch: develop
delivery_branch: codex/portal-runtime-supervisor-1355
status: implementing
priority: critical
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
live_capital_authorized: false
protected_production_deployment_authorized: false
invocation_started_at: 2026-08-13T08:58:00+02:00
last_progress_at: 2026-08-13T09:05:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
```

## Objective

Close the three material trust-boundary findings from the fresh audit of PR #1496 on the existing delivery PR, then remove all one-shot repair workflows and restore exact-head validation. Reuse the existing prepared transformations; do not create another implementation PR.

## Findings

- `RS-AUDIT-20260813-01 / P1`: failed-runtime cleanup uses mutable runtime name rather than immutable container identity.
- `RS-AUDIT-20260813-02 / P1`: distinct authorized lifecycle UID lacks a fail-closed dedicated-group filesystem access path to the UDS.
- `RS-AUDIT-20260813-03 / P1`: execution adapter does not verify returned `SupervisorOutcome` identity before trusting state/version.

The prepared repair workflow reached product validation on run `31675863717`. Ruff and mypy passed; 104 focused tests passed. Two transport tests failed because their hermetic fixture simulates peer UID `42` but does not provide the newly required `socket_access_gid`. The production ACL behavior itself failed closed as designed.

## Owned paths

- `ai_platform/portal/execution/driver.py`
- `ai_platform/portal/execution/adapter.py`
- `ai_platform/portal/runtime_supervisor/transport.py`
- `tests/ai_platform/portal/execution/test_driver.py`
- `tests/ai_platform/portal/execution/test_adapter.py`
- `tests/ai_platform/portal/runtime_supervisor/test_transport.py`
- `.github/workflows/apply-runtime-supervisor-self-audit-repair.yml`
- `.github/workflows/apply-runtime-supervisor-self-audit-repair-v2.yml`
- `.github/workflows/apply-runtime-supervisor-self-audit-repair-v3.yml`
- this task record

## Acceptance

- failure cleanup never removes a container by mutable runtime name;
- exact immutable container identity is captured from `docker create` and used for failure cleanup;
- distinct lifecycle UID requires configured group access and unrelated identities remain excluded;
- same-UID supervisor sockets remain owner-only;
- adapter validates tenant, bot, generation, spec digest, operation, command and correlation identity in Supervisor outcomes;
- mismatched Supervisor outcomes fail closed before workspace/runtime state is trusted;
- hermetic transport fixtures explicitly provide a safe test group when simulating a distinct peer UID;
- focused Ruff, mypy and supervisor/execution tests pass;
- all three one-shot repair workflows are deleted from the final delivery head;
- required exact-head CI/E2E passes after synchronization with current `develop`;
- independent fresh post-repair audit remains mandatory before merge.

## Safety

PAPER-only. No deployment, protected-environment mutation, exchange credentials, real orders, withdrawals, LIVE transition, or owner-funded Codex/OpenAI/paid-AI use is authorized.

## Context checkpoint

```yaml
checkpoint_version: 1
head_at_start: 85ebd78aadd3a79d50bf68deeb96dbf9ff8105a3
branch: codex/portal-runtime-supervisor-1355
pr: 1496
status: implementing
proven:
  - run 31675863717 applied the prepared transformations successfully
  - Ruff and mypy passed after lint normalization
  - 104 focused tests passed
  - two failures are isolated to distinct-UID test fixtures missing socket_access_gid
blockers: []
next_action: update the bounded repair workflow to supply a safe test gid in the two distinct-UID transport fixtures, then rerun the focused repair and remove all one-shot workflows on success
```
