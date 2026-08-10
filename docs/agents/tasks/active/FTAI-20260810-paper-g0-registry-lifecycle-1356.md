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
- `A5`: historical review provenance remains distinct from the latest architecture-change base.
- `A6`: #1356 is moved from the registry open sets into `review.resolved_findings` in PR #1447 together with the preventive guard.
- `A7`: exact-head routed CI, CodeQL/zizmor as applicable, an independent Codex review and PR hygiene are green before merge.
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
checkpoint_version: 5
updated_at: 2026-08-10T21:01:38+02:00
last_progress_at: 2026-08-10T20:58:45+02:00
implementation_head_before_checkpoint: 8d8234be099a61fbd73c023b5a3974714ad0386e
pre_wait_head: 48c177b299c848da18d031ca41aa03ff5db689b5
branch: fix/architecture-registry-lifecycle-1356
pr: 1447
status: waiting
counters:
  ci_checks_for_pre_wait_head: 2
  unchanged_state_checks: 2
  identical_failure_retries: 0
  repair_cycles_for_current_gate: 1
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
pre_wait_validation:
  head: 48c177b299c848da18d031ca41aa03ff5db689b5
  required_runs:
    freqtrade_ci:
      run: 31421848405
      state_at_second_check: queued
    risk_aware_component_ci:
      run: 31421848582
      state_at_second_check: in_progress
    codeql:
      run: 31421848353
      state_at_second_check: pending
    zizmor:
      run: 31421848240
      state_at_second_check: success
  independent_codex_review:
    requested_for_head: 48c177b299c848da18d031ca41aa03ff5db689b5
    review_count_at_second_check: 0
proven:
  - develop exact base remained 5a19ae32f1f71b112130ea66cb8d56d9a3e44049 through the implementation audit
  - Issue 1356 is open and explicitly requires the preventive architecture-registry lifecycle validator
  - historical owner comments on Issue 1356 confirm the intended guard semantics and explain why the earlier PR 1367 prototype was intentionally removed from that over-scoped task
  - PR 1447 contains the bounded tests/ci architecture-registry guard and candidate registry reconciliation
  - the guard rejects duplicate or remapped Issue/finding identities resolved/open overlap non-open top-level findings stale domain-local open indexes and missing acceptance of the latest ADR
  - the first exact-head CI failure was confined to formatting of the newly added owned test and was repaired by commit 1e6be5adadd6ae5f26355b1aaa3bd58a19a09dce
  - a fresh implementer-side falsification pass identified and closed the remapped-identity loophole in commit 8d8234be099a61fbd73c023b5a3974714ad0386e
  - Issues 1354 and 1355 remain genuinely open and therefore remain the only top-level open architecture findings in the candidate registry
  - exact PR diff contains only ARCHITECTURE_REGISTRY.yaml the active task record and tests/ci/test_architecture_registry.py
  - runtime browser deployment and trading E2E are not applicable to this CI/governance-only package
unknown:
  - terminal exact-head CI result on the checkpoint successor created by this recovery commit
  - independent Codex review disposition on the checkpoint successor
blockers:
  - terminal CI and independent review were still external and non-terminal after the maximum two observations allowed for pre-wait head 48c177b299c848da18d031ca41aa03ff5db689b5
next_action: Resolve the live PR 1447 head and its current check generation once; if all required checks and the independent Codex review are terminally clear, continue closeout, otherwise remediate the first material owned failure.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: paper-20260810-2040
  session_started_at: 2026-08-10T20:40+02:00
  checkpointed_at: 2026-08-10T21:01:38+02:00
  last_progress_at: 2026-08-10T20:58:45+02:00
  phase: terminal_ci_and_independent_review
  exact_head: 48c177b299c848da18d031ca41aa03ff5db689b5
  pull_request: 1447
  active_operation: terminal CI and independent Codex review wait; this checkpoint commit creates a successor PR head that must be resolved on resume
  external_run_ids:
    - 31421848405
    - 31421848582
    - 31421848353
    - 31421848240
  operation_started_at: 2026-08-10T18:59:00Z
  wait_deadline_at: null
  check_generation: pre-wait-head-48c177b299c8
  checks_used: 2
  status: waiting
  safe_to_resume: true
  resume_condition: The live PR 1447 head has terminal required CI and an independent Codex review disposition, or a material failure appears that requires owned remediation.
  next_action: Resolve the live PR 1447 head and aggregate current checks once; then either remediate the first material failure or complete PR closeout when every gate is green and review threads are clear.
```
