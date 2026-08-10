# FTAI-20260810 — PAPER G0 Architecture Registry Lifecycle Guard

```yaml
task_id: FTAI-20260810-paper-g0-registry-lifecycle-1356
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: ci_governance
phase: validation
status: validating
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

Close PAPER implementation gate G0 finding #1356 by delivering a bounded automated architecture-registry lifecycle guard together with the registry reconciliation. Do not claim completion until exact-head CI, audit and PR hygiene pass.

## Acceptance inventory

- `A1`: resolved findings cannot remain in `open_architecture_findings`.
- `A2`: every top-level open architecture finding has `status: open` and stable Issue/finding identity.
- `A3`: domain-local open-finding indexes cannot retain an entry that is absent from the canonical top-level open set.
- `A4`: the registry's latest accepted ADR exists as `accepted` in the binding decision log.
- `A5`: historical review provenance remains distinct from the latest architecture-change base.
- `A6`: #1356 is moved from the registry open sets into `review.resolved_findings` in PR #1447 together with the preventive guard.
- `A7`: exact-head routed CI, CodeQL/zizmor as applicable, and PR hygiene are green before merge.
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
checkpoint_version: 3
updated_at: 2026-08-10T20:53:22+02:00
last_progress_at: 2026-08-10T20:53:22+02:00
implementation_head_before_checkpoint: 1e6be5adadd6ae5f26355b1aaa3bd58a19a09dce
branch: fix/architecture-registry-lifecycle-1356
pr: 1447
status: validating
counters:
  ci_checks_for_current_head: 0
  unchanged_state_checks: 0
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
proven:
  - develop exact base remains 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
  - Issue 1356 is open and explicitly requires the preventive architecture-registry lifecycle validator
  - historical owner comments on Issue 1356 confirm the intended guard semantics and explain why the earlier PR 1367 prototype was intentionally removed from that over-scoped task
  - PR 1447 contains the bounded tests/ci architecture-registry guard and candidate registry reconciliation
  - the guard rejects resolved/open overlap duplicate identities non-open top-level findings stale domain-local open indexes and missing acceptance of the latest ADR
  - the first exact-head CI failure was confined to formatting of the newly added owned test and was repaired by commit 1e6be5adadd6ae5f26355b1aaa3bd58a19a09dce
  - runtime browser deployment and trading E2E are not applicable to this CI/governance-only package
unknown:
  - exact final-head CI run IDs and terminal results after this checkpoint update
  - final exact-diff audit result after this checkpoint update
blockers: []
next_action: Require exact-head CI on the checkpoint successor; if green, refresh the exact diff and review-thread audit, mark PR 1447 ready and merge; otherwise isolate the first owned failure.
```
