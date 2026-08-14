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
repair_cycles_for_current_gate: 1
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

- The delivery branch was merge-forwarded without force to current `develop@15a4b3e02e7e431d04f0b5c6d861a669c4de4743`, incorporating merged PR #1517 which retired the expired `.github/workflows/portal-oidc-owner-bootstrap.yml` and its registry entry. The compare after merge-forward reported `behind_by=0` and merge-base exactly `15a4b3e...`.
- Focused CI repair run `31793940741`, job `94746752927`, completed `success`.
  - 31 focused immutable-ownership/restart/host-isolation tests passed.
  - Ruff passed.
  - `git diff --check` passed.
- Repair commit `aa4e20610cf0f534015063d3d0c06b42eb2c6d1c` aligns stale unit-test fixtures with the stricter immutable ownership contract:
  - failed `docker rm` retains the immutable container ID for safe retry/reconciliation;
  - direct network-attestation unit tests that bypass `prepare_network()` explicitly seed the immutable network ID required by production semantics.
- The lifecycle-bounded one-shot `.github/workflows/repair-1496-ci.yml` removed itself in commit `aa4e20610cf0f534015063d3d0c06b42eb2c6d1c` and is not part of the intended final tree.
- Pull-request workflow attempts emitted automatically from the GitHub Actions bot-authored repair commit were `action_required`; this checkpoint is intentionally owner-authored through the repository connector so the required exact-head workflows can execute against a non-bot-authored final validation head.

## Safety

PAPER-only. No deployment, protected-environment mutation, exchange credentials, real orders, withdrawals, LIVE transition, owner-funded Codex/OpenAI/paid-AI use or owner-owned AI credentials are authorized or used.

## Context checkpoint

```yaml
checkpoint_version: 7
updated_at: 2026-08-14T12:54:00+02:00
pre_checkpoint_head: aa4e20610cf0f534015063d3d0c06b42eb2c6d1c
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
last_progress_at: 2026-08-14T12:54:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
proven:
  - ownership restart repair is present in production code and dedicated restart regressions
  - current branch incorporated develop 15a4b3e without force and was not behind at merge-forward
  - expired Portal owner-bootstrap workflow is retired via merged develop PR 1517
  - focused post-repair validation run 31793940741 / job 94746752927 passed 31 tests plus Ruff and diff-check
  - task-owned one-shot CI repair workflow removed itself from the repair result
waiting_on:
  - terminal required exact-head CI and Runtime Isolation E2E on this checkpoint successor
  - genuinely fresh independent post-repair audit with independent context; this implementing session cannot self-certify that gate
blockers: []
next_action: Verify every required exact-head CI/E2E workflow on this checkpoint successor. If terminal green, perform final base/thread/workflow hygiene verification and hand the exact SHA to a genuinely fresh AUDIT ONLY validator; do not merge without PASS_ZERO_MATERIAL_FINDINGS.
```

## Recovery checkpoint

```yaml
policy_version: 1
generation: 2
session_id: chat-20260814-1244
session_started_at: 2026-08-14T12:44:00+02:00
checkpointed_at: 2026-08-14T12:54:00+02:00
last_progress_at: 2026-08-14T12:54:00+02:00
phase: final_ci_then_fresh_audit
exact_head_parent: aa4e20610cf0f534015063d3d0c06b42eb2c6d1c
pull_request: 1496
active_operation: exact_head_ci
external_run_ids:
  - 31793940741
operation_started_at: 2026-08-14T12:54:00+02:00
wait_deadline_at: null
check_generation: ownership-repair-final-ci-2
checks_used: 0
status: waiting
safe_to_resume: true
resume_condition: PR #1496 remains on the same delivery branch and the checkpoint successor exact SHA is unchanged; inspect terminal workflow outcomes or the first relevant failure.
next_action: Verify the checkpoint successor exact-head workflow matrix and inspect the first relevant failure if any.
```
