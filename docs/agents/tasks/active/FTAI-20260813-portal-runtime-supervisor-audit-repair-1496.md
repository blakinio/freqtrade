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
status: validating
priority: critical
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
live_capital_authorized: false
protected_production_deployment_authorized: false
repair_cycles_for_current_gate: 2
```

## Objective

Close all material trust-boundary findings on PR #1496, synchronize the delivery with current `develop`, prove exact-head validation, and leave only a genuinely fresh independent audit as a separate-role gate if repository policy still requires it. PAPER remains the only authorized operational mode.

## Findings and disposition

- `RS-AUDIT-20260813-01 / P1` — **REPAIRED**: failed-runtime cleanup captures immutable container identity and refuses name-based destructive cleanup when immutable evidence is unavailable.
- `RS-AUDIT-20260813-02 / P1` — **REPAIRED**: distinct authorized lifecycle UID requires a protected filesystem group; trusted root/socket ownership and permissions fail closed.
- `RS-AUDIT-20260813-03 / P1` — **REPAIRED**: execution adapter validates Supervisor outcome tenant/bot/generation/spec-digest/operation/command/correlation identity before trusting returned state/version.
- `RS-FRESH-20260813-01 / HIGH` — **REPAIRED**: lifecycle ownership is bound to immutable Docker container/network IDs, not deterministic names plus copyable labels. Same-name/same-label replacement with a different immutable ID fails closed before inspection probes or destructive/disruptive lifecycle actions.
- `RS-FRESH-CLOSEOUT-20260813-01 / P1` — **REPAIRED IN CODE, FINAL VALIDATION PENDING**: immutable container/network ownership is persisted through the Supervisor ownership store so a fresh driver/Supervisor can reconcile a surviving generation after restart without trusting mutable names.

## Immutable-identity repair evidence

- `ai_platform/portal/execution/driver.py` captures Docker create output in `_container_ids`, binds it into the Supervisor ownership store, requires current Docker identity to match the durable immutable ID, and performs state inspection, readiness probes, pause/stop/retire/release by immutable container ID.
- stopped-state reconciliation retains the immutable container ID until retirement so a later replacement cannot inherit lifecycle authority.
- `ai_platform/portal/execution/host_isolation.py` captures Docker network create output in `_network_ids`, binds it into the same ownership store, verifies name resolution against that immutable ID, removes only the captured network ID, and refuses name-based cleanup when immutable identity is unavailable.
- `tests/ai_platform/portal/execution/test_immutable_runtime_identity.py`, `test_runtime_identity_retention.py`, `test_driver.py`, `test_host_isolation_cleanup.py`, and `tests/ai_platform/portal/runtime_supervisor/test_durable_ownership_restart.py` cover same-name/same-label replacement, immutable-ID retention/cleanup, and restart durability.

## Current repair and validation evidence

- The delivery branch was merge-forwarded without force to `develop@15a4b3e02e7e431d04f0b5c6d861a669c4de4743`, incorporating merged PR #1517 which retired the expired `.github/workflows/portal-oidc-owner-bootstrap.yml` and its registry entry. The compare after merge-forward reported `behind_by=0` and merge-base exactly `15a4b3e...`.
- Focused immutable-ownership CI repair run `31793940741`, job `94746752927`, completed `success`: 31 focused tests passed, Ruff passed, and `git diff --check` passed.
- Repair commit `aa4e20610cf0f534015063d3d0c06b42eb2c6d1c` aligns stale immutable-ownership unit-test fixtures with the stricter production contract and removes its lifecycle-bounded one-shot repair workflow.
- Exact-head validation on `97e77c6a3bfad9adffdd2ec2df54fa0105e784b8` independently proved the ownership repair itself: Runtime Isolation E2E `31794125856`, Portal Exact-Image `31794126002`, Portal API Browser `31794125853`, WickHunter Browser `31794126111`, CodeQL `31794125952`, and zizmor `31794125989` reached success before that head was superseded by the integration-test repair.
- Risk-aware run `31794126034`, AI Platform job `94747528939`, reduced the prior 7 ownership-related failures to exactly one base-synchronization failure: `tests/ai_platform/portal/deployment/test_portal_oidc_owner_bootstrap.py` still tried to read the intentionally retired workflow. The job result was `1 failed, 1536 passed, 83 skipped`.
- Commit `e87cec8f23147dafcbe58b14bd7688953e35f0e0` replaces that stale assertion with a terminal-retirement contract: `test_expired_request_only_workflow_is_retired()` now requires the workflow to remain absent. No production Portal/runtime behavior is changed.
- `.github/workflows/repair-1496-ci.yml` and `.github/workflows/portal-oidc-owner-bootstrap.yml` are absent from the intended final tree.

## Safety

PAPER-only. No deployment, protected-environment mutation, exchange credentials, real orders, withdrawals, LIVE transition, owner-funded Codex/OpenAI/paid-AI use or owner-owned AI credentials are authorized or used.

## Context checkpoint

```yaml
checkpoint_version: 8
updated_at: 2026-08-14T13:03:00+02:00
pre_checkpoint_head: e87cec8f23147dafcbe58b14bd7688953e35f0e0
current_develop: 15a4b3e02e7e431d04f0b5c6d861a669c4de4743
branch: codex/portal-runtime-supervisor-1355
pr: 1496
status: validating
phase: final_ci_then_fresh_audit
session_id: chat-20260814-1244
session_role: implementer
execution_mode: github_only
policy_version: 2
context_pressure: medium
context_growth: stable
decomposition_decision: phased
validation_level: exact_head_final
invocation_started_at: 2026-08-14T12:44:00+02:00
last_progress_at: 2026-08-14T13:03:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 2
context_reconstruction_attempts: 0
stall_warnings: 0
proven:
  - ownership restart repair is present in production code and dedicated restart regressions
  - current branch incorporated develop 15a4b3e without force and was not behind at merge-forward
  - expired Portal owner-bootstrap workflow is retired via merged develop PR 1517
  - focused ownership validation passed 31 tests plus Ruff and diff-check
  - Runtime Isolation E2E and all bounded security/browser/image gates passed on the immediately preceding validation head before the stale OIDC test repair
  - stale OIDC workflow test was isolated from a 1536-pass AI Platform run and repaired without changing production code
  - task-owned one-shot CI repair workflow is absent
waiting_on:
  - terminal required exact-head CI/E2E on this checkpoint successor
  - genuinely fresh independent post-repair audit with independent context; this implementing session cannot self-certify that gate
blockers: []
next_action: Verify every required exact-head CI/E2E workflow on this checkpoint successor. If terminal green, verify base freshness, mergeability, zero unresolved threads and temporary-workflow absence, then hand the exact SHA to a genuinely fresh AUDIT ONLY validator; do not merge without PASS_ZERO_MATERIAL_FINDINGS.
```

## Recovery checkpoint

```yaml
policy_version: 1
generation: 3
session_id: chat-20260814-1244
session_started_at: 2026-08-14T12:44:00+02:00
checkpointed_at: 2026-08-14T13:03:00+02:00
last_progress_at: 2026-08-14T13:03:00+02:00
phase: final_ci_then_fresh_audit
exact_head_parent: e87cec8f23147dafcbe58b14bd7688953e35f0e0
pull_request: 1496
active_operation: exact_head_ci
external_run_ids:
  - 31793940741
  - 31794126034
operation_started_at: 2026-08-14T13:03:00+02:00
wait_deadline_at: null
check_generation: ownership-repair-final-ci-3
checks_used: 0
status: waiting
safe_to_resume: true
resume_condition: PR #1496 remains on the same delivery branch and this checkpoint successor exact SHA is unchanged; inspect terminal workflow outcomes or the first relevant failure.
next_action: Verify the checkpoint successor exact-head workflow matrix and inspect the first relevant failure if any.
```
