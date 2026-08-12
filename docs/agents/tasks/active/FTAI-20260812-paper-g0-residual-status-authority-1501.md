# FTAI-20260812 — PAPER G0 residual status-authority repair

```yaml
task_id: FTAI-20260812-paper-g0-residual-status-authority-1501
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
issue: 1501
continuation_pr: 1449
base_branch: develop
paper_gate: G0
status: validating
priority: high
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Isolate and repair fresh PR #1449 findings after the parent task exhausted its configured repair cycles. Reconcile every legacy or historical status-routing declaration to the living exact-head implementation ledger without changing the immutable #1101 snapshot, and keep enforcement fail-closed under ordinary Markdown wrapping, competing machine-readable authority contracts, and residual prose that designates superseded roll-ups as authoritative.

## Owned paths

- `docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md`
- `docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md`
- `docs/ai_platform/portal/WEB_SHELL_FOUNDATION.md`
- `tests/ci/test_portal_status_authority.py`
- this task record

## Evidence

- Original successor finding `PRRT_kwDOTdDTU86YB6ww` on PR #1449 is remediated.
- Fresh exact-head finding `PRRT_kwDOTdDTU86YiEyf` proved the focused gate compared a human phrase without normalizing Markdown whitespace; remediated.
- Fresh exact-head findings `PRRT_kwDOTdDTU86YiMdl` and `PRRT_kwDOTdDTU86YiMdp` proved that a second `portal-status-authority-v1` contract without the legacy boolean and wrapped authority prose could evade discovery; both are remediated.
- Fresh finding `PRRT_kwDOTdDTU86YilHh` proved `WEB_SHELL_FOUNDATION.md` still called `UI_DELIVERY_STATUS.md` authoritative. The document now labels that file a compatibility/read-model roll-up, points exact-head status to `tools/portal_audit/ledger/index.json`, and the CI discovery vocabulary rejects the residual `is authoritative in` claim form.
- Issue #1501 owns this isolated successor repair.
- `POST_P12_INTEGRATION_BACKLOG.md` routes current PI/P-stage implementation status to `tools/portal_audit/ledger/index.json` and labels the #1101 JSON only historical compatibility metadata.
- `NEXT_WORK_AND_REPAIR_PLAN.md` derives work selection from live GitHub state, the living exact-head ledger, and repository governance; the #1101 JSON is historical compatibility metadata only.
- `tests/ci/test_portal_status_authority.py` discovers tracked JSON authority contracts by schema/key shape in addition to the legacy boolean, requires the canonical contract to be the only such tracked authority contract, validates all canonical safety grants false, normalizes Portal prose before matching current-authority claims, and explicitly protects the historical web-shell route.
- PR #1449 was reconstructed without force at merge-forward commit `3c24d91cc9597d606d930a8606d3305167dff9ac` from current `develop@0c450ef7fe29ebbae49e7aea5c051018e3fd28f5` plus only the declared G0 candidate paths. The prior contaminated historical diff was removed from the live PR while preserving branch history.
- Trusted base `develop@0c450ef7fe29ebbae49e7aea5c051018e3fd28f5` forbids unapproved owner-funded Codex/AI use. No further Codex review, OpenAI API, owner AI token, or paid/limited AI invocation is authorized for this task.

## Safety

Documentation/CI governance only. PAPER-only. No runtime behavior, deployment, credentials, exchange orders, withdrawals, protected-environment mutation, or LIVE authority.

## Audit state

The prior independent Codex reviews are historical evidence only and cannot be newly invoked after the owner-funded AI prohibition on the trusted base. The latest independent review finding `PRRT_kwDOTdDTU86YilHh` is repaired, but a fresh non-owner-funded exact-head audit is still required before terminal completion.

```yaml
result: PENDING_FRESH_NON_OWNER_FUNDED_VALIDATOR
material_findings_open: 0
finding_PRRT_kwDOTdDTU86YB6ww: remediated
finding_PRRT_kwDOTdDTU86YiEyf: remediated_by_whitespace_normalization
finding_PRRT_kwDOTdDTU86YiMdl: remediated_by_repo_wide_authority_contract_detection
finding_PRRT_kwDOTdDTU86YiMdp: remediated_by_normalized_prose_discovery
finding_PRRT_kwDOTdDTU86YilHh: remediated_by_web_shell_reroute_and_claim_form_detection
runtime_browser_e2e:
  result: NOT_APPLICABLE
  reason: documentation/CI authority routing only; no runtime or browser behaviour changes
```

## Context checkpoint

```yaml
checkpoint_version: 4
updated_at: 2026-08-12T21:03:36Z
branch: feat/paper-g0-status-authority-20260810
head: LIVE_BRANCH_HEAD_REQUIRED
base_head_integrated: 0c450ef7fe29ebbae49e7aea5c051018e3fd28f5
pr: 1449
status: validating
phase: focused_validation_then_exact_head_ci
invocation_started_at: 2026-08-12T20:54:00Z
last_progress_at: 2026-08-12T21:03:36Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 3
context_reconstruction_attempts: 1
stall_warnings: 0
focused_changes_complete: true
fresh_audit: pending_non_owner_funded_validator
fresh_exact_head_ci: pending
unresolved_material_threads: [PRRT_kwDOTdDTU86YilHh]
recovery:
  policy_version: 1
  generation: 4
  session_id: chat-20260812T205400Z
  session_started_at: 2026-08-12T20:54:00Z
  checkpointed_at: 2026-08-12T21:03:36Z
  last_progress_at: 2026-08-12T21:03:36Z
  phase: focused_validation_then_exact_head_ci
  exact_head: LIVE_BRANCH_HEAD_REQUIRED
  pull_request: 1449
  active_operation: none
  external_run_ids: []
  operation_started_at: null
  wait_deadline_at: null
  check_generation: post-web-shell-authority-repair
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: branch head and PR ownership remain unchanged
  next_action: run focused authority validation and exact-head existing GitHub CI without invoking owner-funded AI
next_action: run focused authority validation and exact-head existing GitHub CI without invoking owner-funded AI
```
