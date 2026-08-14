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
- `RS-FINAL-AUDIT-20260814-01 / MEDIUM` — **REPAIRED IN CODE, FINAL VALIDATION PENDING**: Supervisor outcomes echo generation ordinal, state-version precondition, correlation and causation identity; the adapter rejects any one-field mismatch before trusting returned state/state_version.

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

## Final-audit response-binding repair evidence

- `ai_platform/portal/runtime_supervisor/types.py` extends `SupervisorOutcome` with the authoritative request precondition/causation echo fields while retaining fail-closed compatibility for legacy serialized outcomes.
- `ai_platform/portal/runtime_supervisor/service.py` emits those fields and includes them, correlation identity and causation identity in `evidence_digest`.
- `ai_platform/portal/execution/adapter.py` rejects mismatched generation ordinal, expected state version or causation identity before any returned runtime state/version is trusted.
- `tests/ai_platform/portal/execution/test_adapter.py` now mutates every authoritative identity field one at a time, including the newly repaired fields.
- `tests/ai_platform/portal/runtime_supervisor/test_outcome_binding.py` proves serialization and digest binding for the new fields.
- Lifecycle-bounded focused repair workflow run `31800186305` executes compile, focused tests, Ruff, Ruff format, mypy and `git diff --check` before creating the repair commit, then removes itself from the final tree.

## Safety

PAPER-only. No deployment, protected-environment mutation, exchange credentials, real orders, withdrawals, LIVE transition, owner-funded Codex/OpenAI/paid-AI use or owner-owned AI credentials are authorized or used.

## Context checkpoint

```yaml
checkpoint_version: 9
updated_at: 2026-08-14T14:26:25+02:00
pre_checkpoint_head: b3d7a271ae00d7ab8873a9c0d6672ca3849cfd49
current_develop: 15a4b3e02e7e431d04f0b5c6d861a669c4de4743
branch: codex/portal-runtime-supervisor-1355
pr: 1496
status: validating
phase: exact_head_ci_then_fresh_audit
session_id: chat-20260814-1418
session_role: implementer
execution_mode: github_only
policy_version: 2
context_pressure: medium
context_growth: stable
decomposition_decision: phased
validation_level: focused_repair_complete_exact_head_pending
invocation_started_at: 2026-08-14T14:18:00+02:00
last_progress_at: 2026-08-14T14:26:25+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
proven:
  - prior durable immutable container/network ownership restart repair remains present
  - RS-FINAL-AUDIT-20260814-01 response-boundary repair is present in production code
  - Supervisor outcome carries and evidence-digest binds expected generation ordinal, expected state version, correlation and causation identity
  - execution adapter rejects one-field-at-a-time authoritative outcome mismatches before trusting state/state_version
  - bounded workflow run 31800186305 performs focused tests, compile, Ruff, Ruff format, mypy and diff-check before commit
  - task-owned one-shot repair workflow is removed from the intended final tree
waiting_on:
  - terminal required exact-head CI/E2E on the response-binding repair successor
  - genuinely fresh independent post-repair audit with independent context; this implementing session cannot self-certify that gate
blockers: []
next_action: Verify every required exact-head CI/E2E workflow on the repair successor. If terminal green, verify base freshness, mergeability, zero unresolved threads and temporary-workflow absence, then hand the exact SHA to a genuinely fresh AUDIT ONLY validator; do not merge without PASS_ZERO_MATERIAL_FINDINGS.
```

## Recovery checkpoint

```yaml
policy_version: 1
generation: 4
session_id: chat-20260814-1418
session_started_at: 2026-08-14T14:18:00+02:00
checkpointed_at: 2026-08-14T14:26:25+02:00
last_progress_at: 2026-08-14T14:26:25+02:00
phase: exact_head_ci_then_fresh_audit
exact_head_parent: b3d7a271ae00d7ab8873a9c0d6672ca3849cfd49
pull_request: 1496
active_operation: exact_head_ci
external_run_ids:
  - 31800186305
operation_started_at: 2026-08-14T14:26:25+02:00
wait_deadline_at: null
check_generation: outcome-binding-final-ci-1
checks_used: 0
status: waiting
safe_to_resume: true
resume_condition: PR #1496 remains on the same delivery branch and the repair-successor exact SHA is unchanged; inspect terminal workflow outcomes or the first relevant failure.
next_action: Verify the repair-successor exact-head workflow matrix and inspect the first relevant failure if any.
```
