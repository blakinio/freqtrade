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

Close PAPER implementation gate G0 finding #1356 by delivering a bounded automated architecture-registry lifecycle guard together with the registry reconciliation. Do not claim completion until exact-head CI, independent audit and PR hygiene pass.

## Acceptance inventory

- `A1`: resolved findings cannot remain in `open_architecture_findings`, even if an Issue or finding ID is accidentally remapped.
- `A2`: every architecture finding identity uses a positive exact integer Issue number, a non-empty unique finding ID and valid lifecycle status; YAML booleans are rejected as Issue identifiers.
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
checkpoint_version: 8
updated_at: 2026-08-10T21:16:08+02:00
last_progress_at: 2026-08-10T21:16:08+02:00
implementation_head_before_checkpoint: 93eaf7630a69d62f2da90f8f6d504d76aafb08f9
branch: fix/architecture-registry-lifecycle-1356
pr: 1447
status: validating
counters:
  ci_checks_for_current_head: 0
  independent_review_checks_for_current_head: 0
  unchanged_state_checks: 0
  identical_failure_retries: 0
  repair_cycles_for_current_gate: 3
  context_reconstruction_attempts: 0
  stall_warnings: 0
first_ci_failure:
  workflow: Freqtrade CI
  run: 31421127334
  jobs:
    - 93561932198
    - 93561932240
  signature: ruff-format required formatting of tests/ci/test_architecture_registry.py
  repair_commit: 1e6be5adadd6ae5f26355b1aaa3bd58a19a09dce
independent_review_history:
  - reviewed_head: 48c177b299c848da18d031ca41aa03ff5db689b5
    submitted_at: 2026-08-10T19:03:13Z
    severity: P2
    thread: PRRT_kwDOTdDTU86X_6vx
    summary: synchronized_base_sha was not required to remain distinct from latest_architecture_change.base_sha
    disposition: remediated
    remediation_head: 4d4a2f8961af81b75b3ffaf3cb0bfd2aff6bc282
  - reviewed_head: 4d4a2f8961af81b75b3ffaf3cb0bfd2aff6bc282
    submitted_at: 2026-08-10T19:09:02Z
    severity: P2
    thread: PRRT_kwDOTdDTU86YABz6
    summary: bool Issue identifiers were accepted because bool is a subclass of int in Python
    disposition: remediated
    remediation_head: 93eaf7630a69d62f2da90f8f6d504d76aafb08f9
proven:
  - Issue 1356 explicitly requires the preventive architecture-registry lifecycle validator
  - PR 1447 changed-file scope remains limited to ARCHITECTURE_REGISTRY.yaml the active task record and tests/ci/test_architecture_registry.py
  - the guard rejects duplicate/remapped Issue and finding identities resolved/open overlap non-open top-level findings stale domain-local open indexes and missing acceptance of the latest ADR
  - commit 8d8234be099a61fbd73c023b5a3974714ad0386e closed the remapped-identity loophole found during implementer falsification
  - head 4d4a2f8961af81b75b3ffaf3cb0bfd2aff6bc282 closed the first independent P2 by asserting both historical review provenance SHAs remain distinct from latest_architecture_change.base_sha
  - head 93eaf7630a69d62f2da90f8f6d504d76aafb08f9 closes the second independent P2 by requiring type(issue) is int and issue > 0
  - PR body uses Closes #1356 so Issue closure occurs only after successful merge
  - Issues 1354 and 1355 remain genuinely open and are the only top-level open architecture findings in the candidate registry
  - runtime browser deployment and trading E2E are not applicable to this CI/governance-only package
unknown:
  - terminal exact-head CI result on the successor created by this task-record commit
  - final independent Codex disposition on that successor/final substantive remediation
blockers: []
next_action: Resolve the live PR 1447 successor head, mark ready/request final independent review and collect exact-head CI; merge and close/archive only when all gates are green and no unresolved review threads remain.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 3
  session_id: paper-20260810-2114
  session_started_at: 2026-08-10T21:14:00+02:00
  checkpointed_at: 2026-08-10T21:16:08+02:00
  last_progress_at: 2026-08-10T21:16:08+02:00
  phase: final_independent_review_and_exact_head_ci
  exact_head: 93eaf7630a69d62f2da90f8f6d504d76aafb08f9
  pull_request: 1447
  active_operation: persist the second P2 remediation; this task-record commit creates the exact successor to validate
  external_run_ids: []
  operation_started_at: 2026-08-10T21:16:08+02:00
  wait_deadline_at: null
  check_generation: post-bool-identity-remediation-successor
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: Final exact-head CI and independent Codex review are terminally clear, or a material owned failure appears.
  next_action: Resolve the live PR 1447 successor head once; then complete merge/closeout if all gates pass or remediate only the first material owned failure.
```
