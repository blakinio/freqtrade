# FTAI-20260813 — Runtime Supervisor fresh-audit repair

```yaml
task_id: FTAI-20260813-portal-runtime-supervisor-audit-repair-1496
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
issue: 1355
continuation_pr: 1496
base_branch: develop
delivery_branch: codex/portal-runtime-supervisor-1355
status: validating
priority: critical
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
live_capital_authorized: false
protected_production_deployment_authorized: false
repair_cycles_for_current_gate: 1
```

## Objective

Close all material trust-boundary findings on PR #1496, synchronize the delivery with current `develop`, prove exact-head validation, and leave only a genuinely fresh independent audit as a separate-role gate if repository policy still requires it. PAPER remains the only authorized operational mode.

## Findings and disposition

- `RS-AUDIT-20260813-01 / P1` — **REPAIRED**: failed-runtime cleanup captures immutable container identity and refuses name-based destructive cleanup when immutable evidence is unavailable.
- `RS-AUDIT-20260813-02 / P1` — **REPAIRED**: distinct authorized lifecycle UID requires a protected filesystem group; trusted root/socket ownership and permissions fail closed.
- `RS-AUDIT-20260813-03 / P1` — **REPAIRED**: execution adapter validates Supervisor outcome tenant/bot/generation/spec-digest/operation/command/correlation identity before trusting returned state/version.
- `RS-FRESH-20260813-01 / HIGH` — **REPAIRED**: lifecycle ownership is now bound to immutable Docker container/network IDs, not deterministic names plus copyable labels. Same-name/same-label replacement with a different immutable ID fails closed before inspection probes or destructive/disruptive lifecycle actions.

## Immutable-identity repair evidence

- `ai_platform/portal/execution/driver.py` captures Docker create output in `_container_ids`, requires current name resolution to match the captured immutable ID, and performs state inspection, readiness probes, pause/stop/retire/release by immutable container ID.
- stopped-state reconciliation retains the immutable container ID until retirement so a later replacement cannot inherit lifecycle authority.
- `ai_platform/portal/execution/host_isolation.py` captures Docker network create output in `_network_ids`, verifies name resolution against that immutable ID, removes only the captured network ID, and refuses name-based cleanup when immutable identity is unavailable.
- `tests/ai_platform/portal/execution/test_immutable_runtime_identity.py`, `test_runtime_identity_retention.py`, `test_driver.py`, and `test_host_isolation_cleanup.py` cover same-name/same-label replacement and immutable-ID retention/cleanup behavior.
- real Docker Runtime Isolation E2E run `31712704901` passed the repaired lifecycle path on the post-repair line; subsequent changes before this checkpoint were formatter/base-synchronization/task-record-only.

## Base synchronization

Current integration base is `develop@c0f229d5aec11765cef95996d2a256329b170d25`. Its only delta after the previously integrated `10330a7a...` is G0 task-record archival from `docs/agents/tasks/active/` to `docs/agents/tasks/archive/`.

Task-owned synchronization PR #1514 was merged terminally with the repository-allowed squash method so the branch tree exactly adopted those G0 archive moves. GitHub then generated PR #1496 merge-ref `3525957d8c01dd09f697a33368f859cdd8f59523`, with parents `develop@c0f229d5...` and delivery head `8f6ae778...`; the delivery branch was fast-forwarded to that verified merge-ref without force. Direct comparison now proves `behind_by: 0` and merge-base exactly `c0f229d5...`.

Final changed-file inventory relative current `develop` is 25 task-owned Runtime Supervisor paths; no temporary repair/format/sync workflow remains in the final diff.

## Safety

PAPER-only. No deployment, protected-environment mutation, exchange credentials, real orders, withdrawals, LIVE transition, owner-funded Codex/OpenAI/paid-AI use or owner-owned AI credentials are authorized or used.

## Context checkpoint

```yaml
checkpoint_version: 4
updated_at: 2026-08-13T18:39:00+02:00
checkpoint_head: LIVE_BRANCH_HEAD_REQUIRED
pre_checkpoint_head: 3525957d8c01dd09f697a33368f859cdd8f59523
current_develop: c0f229d5aec11765cef95996d2a256329b170d25
branch: codex/portal-runtime-supervisor-1355
pr: 1496
status: validating
phase: final_ci_then_fresh_audit
invocation_started_at: 2026-08-13T18:25:00+02:00
last_progress_at: 2026-08-13T18:39:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
proven:
  - all four material audit findings are repaired in repository code
  - immutable container and network identity is required before privileged lifecycle actions
  - real Docker Runtime Isolation E2E passed after the functional repair
  - temporary formatting/sync workflow files are absent from final changed-file inventory
  - synchronization PR 1514 is terminal merged
  - current develop is a true ancestor of the delivery branch; behind_by is 0
  - all previously known inline review threads were resolved before this checkpoint
waiting_on:
  - terminal required exact-head CI and Runtime Isolation E2E on this checkpoint successor
  - genuinely fresh independent post-repair audit with independent context; this implementing session cannot self-certify that gate
blockers: []
next_action: Verify exact-head required CI/E2E on the checkpoint successor. If terminal green, persist WAITING/READY for a separate fresh audit-only validator; merge only after PASS_ZERO_MATERIAL_FINDINGS and a final zero-thread/base-freshness check.
```
