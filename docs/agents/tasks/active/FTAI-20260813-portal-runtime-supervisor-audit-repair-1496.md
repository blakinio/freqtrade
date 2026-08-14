# FTAI-20260813 — Runtime Supervisor fresh-audit repair

```yaml
task_id: FTAI-20260813-portal-runtime-supervisor-audit-repair-1496
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
repository: blakinio/freqtrade
issue: 1355
continuation_pr: 1496
base_branch: develop
delivery_branch: codex/portal-runtime-supervisor-1355
status: implementing
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
- `RS-FRESH-CLOSEOUT-20260813-01 / P1` — **REPAIRED IN CODE, VALIDATION PENDING**: immutable container/network ownership is now persisted through the Supervisor ownership store so a fresh driver/Supervisor can reconcile a surviving generation after restart without trusting mutable names.

## Immutable-identity repair evidence

- `ai_platform/portal/execution/driver.py` captures Docker create output in `_container_ids`, binds it into the Supervisor ownership store, requires current Docker identity to match the durable immutable ID, and performs state inspection, readiness probes, pause/stop/retire/release by immutable container ID.
- stopped-state reconciliation retains the immutable container ID until retirement so a later replacement cannot inherit lifecycle authority.
- `ai_platform/portal/execution/host_isolation.py` captures Docker network create output in `_network_ids`, binds it into the same ownership store, verifies name resolution against that immutable ID, removes only the captured network ID, and refuses name-based cleanup when immutable identity is unavailable.
- `tests/ai_platform/portal/execution/test_immutable_runtime_identity.py`, `test_runtime_identity_retention.py`, `test_driver.py`, `test_host_isolation_cleanup.py`, and `tests/ai_platform/portal/runtime_supervisor/test_durable_ownership_restart.py` cover same-name/same-label replacement, immutable-ID retention/cleanup, and restart durability.

## Current CI failure fingerprint

Exact head before this checkpoint: `ec9512b3dc156ade15c09dfe10238727952729b6`.
Current base: `develop@c54153358a0a0dcfcbc2c8ba28b1b5b9e7a84077`; compare reports `behind_by=0`.

- Freqtrade CI `31783651105`: failed.
  - first actionable governance failure: `.github/workflows/portal-oidc-owner-bootstrap.yml: temporary workflow expired on 2026-08-13`.
  - repository registry retirement contract requires removal of the expired workflow and its registry entry; retirement evidence must be updated.
- Risk-aware component CI `31783651338`: failed in AI Platform tests with 7 failures / 1530 passed / 83 skipped.
  - `test_driver_cleanup.py` still expected immutable container ownership to be discarded after failed `docker rm`; the repaired fail-closed implementation intentionally retains it for safe retry/reconciliation.
  - direct `test_host_isolation.py` attestation fixtures bypass `prepare_network()` and therefore do not seed the immutable network identity now required by the production contract.
- Runtime Isolation E2E, Portal API Browser, WickHunter Browser E2E, Exact-Image, CodeQL, and zizmor all passed on `ec9512b3...`.

## Safety

PAPER-only. No deployment, protected-environment mutation, exchange credentials, real orders, withdrawals, LIVE transition, owner-funded Codex/OpenAI/paid-AI use or owner-owned AI credentials are authorized or used.

## Context checkpoint

```yaml
checkpoint_version: 6
updated_at: 2026-08-14T12:44:00+02:00
checkpoint_head: ec9512b3dc156ade15c09dfe10238727952729b6
current_develop: c54153358a0a0dcfcbc2c8ba28b1b5b9e7a84077
branch: codex/portal-runtime-supervisor-1355
pr: 1496
status: implementing
phase: ci_failure_repair
session_id: chat-20260814-1244
session_role: implementer
execution_mode: github_only
policy_version: 2
context_pressure: medium
context_growth: stable
decomposition_decision: phased
validation_level: focused
invocation_started_at: 2026-08-14T12:44:00+02:00
last_progress_at: 2026-08-14T12:44:00+02:00
ci_checks_for_current_head: 1
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
proven:
  - current branch is not behind develop at the observed head
  - immutable container and network identity is required before privileged lifecycle actions
  - current exact-head Runtime Isolation E2E and security/browser workflows pass
  - current CI failures have deterministic first actionable causes
waiting_on: []
blockers: []
next_action: Apply one bounded GitHub-only repair for stale test expectations/fixtures and retire the expired Portal owner-bootstrap workflow plus registry/catalog state, run focused validation, then verify the resulting exact-head CI.
```

## Recovery checkpoint

```yaml
policy_version: 1
generation: 1
session_id: chat-20260814-1244
session_started_at: 2026-08-14T12:44:00+02:00
checkpointed_at: 2026-08-14T12:44:00+02:00
last_progress_at: 2026-08-14T12:44:00+02:00
phase: ci_failure_repair
exact_head: ec9512b3dc156ade15c09dfe10238727952729b6
pull_request: 1496
active_operation: none
external_run_ids:
  - 31783651105
  - 31783651338
operation_started_at: null
wait_deadline_at: null
check_generation: ownership-repair-ci-1
checks_used: 1
status: ready
safe_to_resume: true
resume_condition: PR #1496 remains on the same delivery branch with no conflicting writer; execute the recorded bounded repair against the current branch head.
next_action: Apply the bounded CI repair and trigger focused validation on the resulting head.
```
