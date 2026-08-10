# FTAI-20260810 — PAPER G0 Architecture Registry Lifecycle Guard

```yaml
task_id: FTAI-20260810-paper-g0-registry-lifecycle-1356
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: ci_governance
phase: validation
status: waiting
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: develop
trusted_base_sha: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
delivery_branch: fix/architecture-registry-lifecycle-1356
delivery_pr: 1447
issue: 1356
paper_gate: G0
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Close PAPER implementation gate G0 finding #1356 by delivering a bounded automated architecture-registry lifecycle guard together with the registry reconciliation. Do not claim completion until exact-head CI, independent audit and PR hygiene pass.

## Acceptance inventory

- `A1`: resolved findings cannot remain in `open_architecture_findings`, even if an Issue or finding ID is accidentally remapped.
- `A2`: every top-level open architecture finding has `status: open`, a positive Issue number and a stable unique finding ID.
- `A3`: domain-local open-finding indexes cannot retain an entry that is absent from the canonical top-level open set.
- `A4`: the registry's latest accepted ADR exists as `accepted` in the binding decision log.
- `A5`: historical review provenance (`audited_base_sha` and `synchronized_base_sha`) remains distinct from the latest architecture-change base.
- `A6`: #1356 is moved from registry open sets into `review.resolved_findings` together with the preventive guard.
- `A7`: exact-head routed CI, CodeQL/zizmor as applicable, independent Codex review and PR hygiene are green before merge.
- `A8`: runtime/browser E2E is `NOT_APPLICABLE`; this task changes only CI/governance evidence and grants no runtime, deployment, credentials, order or LIVE authority.

## Owned paths

```yaml
owned_paths:
  - ARCHITECTURE_REGISTRY.yaml
  - tests/ci/test_architecture_registry.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-registry-lifecycle-1356.md
```

## Context checkpoint

```yaml
checkpoint_version: 7
updated_at: 2026-08-10T21:09:00+02:00
last_progress_at: 2026-08-10T21:07:00+02:00
implementation_head_before_checkpoint: 4d4a2f8961af81b75b3ffaf3cb0bfd2aff6bc282
branch: fix/architecture-registry-lifecycle-1356
pr: 1447
status: waiting
counters:
  ci_checks_for_pre_wait_head: 2
  independent_review_checks_for_pre_wait_head: 2
  unchanged_state_checks: 2
  identical_failure_retries: 0
  repair_cycles_for_current_gate: 2
  context_reconstruction_attempts: 0
  stall_warnings: 0
first_failure:
  workflow: Freqtrade CI
  run: 31421127334
  jobs:
    - 93561932198
    - 93561932240
  signature: ruff-format required formatting of tests/ci/test_architecture_registry.py
  repair_commit: 1e6be5adadd6ae5f26355b1aaa3bd58a19a09dce
independent_review:
  reviewer: chatgpt-codex-connector
  reviewed_head: 48c177b299c848da18d031ca41aa03ff5db689b5
  submitted_at: 2026-08-10T19:03:13Z
  finding:
    severity: P2
    thread: PRRT_kwDOTdDTU86X_6vx
    path: tests/ci/test_architecture_registry.py
    summary: historical synchronized_base_sha was type-checked but not required to remain distinct from latest_architecture_change.base_sha
    disposition: remediated
    remediation_head: 4d4a2f8961af81b75b3ffaf3cb0bfd2aff6bc282
  rereview_requested: true
  rereview_state_at_second_check: pending
pre_wait_validation:
  head: 4d4a2f8961af81b75b3ffaf3cb0bfd2aff6bc282
  required_runs:
    freqtrade_ci:
      run: 31422453672
      state_at_second_check: in_progress
    risk_aware_component_ci:
      run: 31422456686
      state_at_second_check: in_progress
    codeql:
      run: 31422453189
      state_at_second_check: success
    zizmor:
      run: 31422453339
      state_at_second_check: success
proven:
  - develop base for this task was 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
  - Issue 1356 explicitly requires the preventive architecture-registry lifecycle validator
  - PR 1447 exact diff is limited to ARCHITECTURE_REGISTRY.yaml the active task record and tests/ci/test_architecture_registry.py
  - the guard rejects duplicate/remapped Issue and finding identities resolved/open overlap non-open top-level findings stale domain-local open indexes and missing acceptance of the latest ADR
  - commit 8d8234be099a61fbd73c023b5a3974714ad0386e closed the remapped-identity loophole found during implementer falsification
  - head 4d4a2f8961af81b75b3ffaf3cb0bfd2aff6bc282 closes the independent P2 by asserting both historical review provenance SHAs remain distinct from latest_architecture_change.base_sha
  - the original P2 review thread is resolved and final Codex re-review was requested
  - PR body now uses Closes #1356 so Issue closure occurs only after successful merge
  - Issues 1354 and 1355 remain genuinely open and are the only top-level open architecture findings in the candidate registry
  - runtime browser deployment and trading E2E are not applicable to this CI/governance-only package
unknown:
  - terminal exact-head CI result on the checkpoint successor created by this wait commit
  - terminal independent Codex re-review disposition on the checkpoint successor
blockers:
  - Freqtrade CI and Risk-aware CI remained non-terminal after two allowed aggregate observations of head 4d4a2f8961af81b75b3ffaf3cb0bfd2aff6bc282
  - independent Codex re-review remained non-terminal after two allowed observations
next_action: Resolve the live PR 1447 successor head and its new check generation once; if all required checks and independent review are terminally clear, complete merge and post-merge closeout, otherwise remediate only the first material owned failure.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 2
  session_id: paper-20260810-2103
  session_started_at: 2026-08-10T21:03:00+02:00
  checkpointed_at: 2026-08-10T21:09:00+02:00
  last_progress_at: 2026-08-10T21:07:00+02:00
  phase: terminal_ci_and_independent_rereview_wait
  exact_head: 4d4a2f8961af81b75b3ffaf3cb0bfd2aff6bc282
  pull_request: 1447
  active_operation: terminal CI and independent Codex re-review wait; this checkpoint commit creates a successor PR head that must be resolved on resume
  external_run_ids:
    - 31422453672
    - 31422456686
    - 31422453189
    - 31422453339
  operation_started_at: 2026-08-10T21:05:00+02:00
  wait_deadline_at: null
  check_generation: post-p2-head-4d4a2f8961af
  checks_used: 2
  status: waiting
  safe_to_resume: true
  resume_condition: The live PR 1447 successor head has terminal required CI and an independent Codex re-review disposition, or a material owned failure appears.
  next_action: Resolve the live PR 1447 successor head once; then either remediate the first material owned failure or complete merge and post-merge closeout when every gate is green and review threads are clear.
```
