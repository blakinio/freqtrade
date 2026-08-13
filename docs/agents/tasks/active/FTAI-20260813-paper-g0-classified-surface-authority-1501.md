# FTAI-20260813 — G0 classified status-surface authority repair

```yaml
task_id: FTAI-20260813-paper-g0-classified-surface-authority-1501
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
issue: 1501
continuation_pr: 1449
base_branch: develop
delivery_branch: feat/paper-g0-status-authority-20260810
paper_gate: G0
status: implementing
priority: high
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
live_capital_authorized: false
protected_production_deployment_authorized: false
invocation_started_at: 2026-08-13T08:58:00+02:00
last_progress_at: 2026-08-13T09:01:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
```

## Objective

Close fresh audit finding `G0-AUTH-20260813-01` on existing PR #1449 without creating another PR. The fail-closed prose discovery must inspect every text status-bearing surface classified by `tools/portal_audit/ledger/status_authority.json`, not only files below `docs/ai_platform/portal/`.

## Finding

`status_authority.json` classifies status-bearing surfaces outside the Portal documentation subtree, including `docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md`, while `tests/ci/test_portal_status_authority.py` currently discovers competing current-authority prose only under `docs/ai_platform/portal/`. A classified roll-up outside that subtree can therefore reintroduce a contradictory current implementation authority claim without failing the G0 guard.

Severity: `P1 / material merge blocker`.

## Owned paths

- `tests/ci/test_portal_status_authority.py`
- this task record

## Acceptance

- prose scanning derives its status-bearing text surface set from the machine-readable `legacy_surfaces` contract;
- classified surfaces outside `docs/ai_platform/portal/` are included;
- agent task records remain outside product-status scanning unless explicitly classified by the authority contract;
- current allowed authority claims remain bounded to the canonical/reconciled surfaces;
- the immutable #1101 snapshot is not changed;
- PAPER/LIVE safety grants remain unchanged;
- focused G0 tests and exact-head required CI pass before closeout;
- fresh independent audit is still required before merge.

## Safety

Documentation/CI governance only. No runtime, deployment, credentials, exchange orders, withdrawals, protected-environment mutation, LIVE transition, or owner-funded Codex/OpenAI/paid-AI use is authorized.

## Context checkpoint

```yaml
checkpoint_version: 1
head_at_start: 84408d8305e1ae03ad60adfbdafa9b73b30ea6cb
branch: feat/paper-g0-status-authority-20260810
pr: 1449
status: implementing
proven:
  - exact-head CI on the pre-repair head was green but did not exercise this missing surface class
  - status_authority.json classifies docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md as a legacy/work-ownership roll-up
  - current prose discovery is rooted only at docs/ai_platform/portal
blockers: []
next_action: update tests/ci/test_portal_status_authority.py so classified text surfaces drive fail-closed prose discovery, then run exact-head validation
```
