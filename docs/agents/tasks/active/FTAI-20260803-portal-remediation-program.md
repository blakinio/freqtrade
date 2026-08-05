# FTAI-20260803 Portal Remediation Programme Coordinator

```yaml
task_id: FTAI-20260803-portal-remediation-program
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: durable_remediation_program
phase: coordinate
status: active
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: split
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
base_branch: develop
last_resolved_develop_head: 108eff8149f3c5dba77bfcdeaea0c63c8a22b551
current_child_task: pending_issue_1132_creation
current_child_branch: pending
current_child_pr: pending
current_child_head: 108eff8149f3c5dba77bfcdeaea0c63c8a22b551
closed_issues: 4
active_issues: 0
waiting_issues: 1
blocked_issues: 0
repository_implemented_but_open_issues: 1
owned_paths:
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-program.md
  - tests/ci/test_portal_programme_coordinator_consistency.py
shared_path_leases: []
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Objective

Coordinate and execute the separate implementation programme covering exactly the 50 Issues listed in `docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md`. This task owns programme state, dependency/barrier resolution, child-task selection and terminal reconciliation. It does not own product implementation paths and cannot be used as an omnibus repair PR.

## Terminal progress

- Audit PR `#1082` and programme initialization PR `#1145` are merged.
- Issues `#1124`, `#1126` and `#1127` are merged, closed and archived.
- Issue `#1122` completed through PR `#1159`, merge commit `4cceecc6078c72f582202815adc3e1891cc0f016`; its durable task is archived at `docs/agents/tasks/archive/FTAI-20260803-portal-remediation-1122.md` and migration/schema ownership is released.
- Issue `#1137` repository implementation merged through PR `#1154`; it remains open only for separately governed protected Authentik staging concurrency using an authorized synthetic identity.
- Issue `#1132` no longer waits on `#1122`. The authoritative migration chain and durable production schema now exist, so back-channel logout replay protection is the next safe READY identity task.

## Coordination rules

- One Issue is one acceptance unit; create a durable child task, branch and PR before product mutation.
- A multi-Issue PR requires a recorded atomic shared-contract justification.
- Shared producers and consumers follow the sole-owner table in the programme record.
- Do not dispatch a child while its paths or producer lease overlap an active task.
- A task waiting on protected acceptance is checkpointed; an independent READY producer task may continue.
- Product Issues close only after implementation, focused/integration validation, independent audit, applicable real API-mode/system E2E, exact-head CI, terminal PR state, task archival and ownership release.
- Repository merge authority does not authorize protected deployment, credentials, live trading, withdrawals or capital.

## Deterministic consistency contract

`tests/ci/test_portal_programme_coordinator_consistency.py` enforces that:

- the coordinator-selected Issue is `READY` or `ACTIVE` in the canonical inventory;
- an Issue cannot remain `WAITING_ON_<dependency>` after that dependency is `COMPLETE`;
- Issue `#1122` is terminal, Issue `#1132` is READY and both programme and coordinator select `#1132` as the next action.

The test runs inside the required lightweight routing contract and prevents the stale state recorded by Issue `#1250` from returning.

## Acceptance

- [x] Audit PR `#1082` is terminal and evidence is available on `develop`.
- [x] Exact authorized 50-Issue inventory and producer ownership are durable.
- [x] Issues `#1124`, `#1126`, `#1127` and `#1122` are merged, closed and archived.
- [x] Issue `#1137` repository work is merged and protected acceptance is truthfully separated.
- [x] Issue `#1132` is reclassified as the next safe READY task.
- [x] Coordinator/programme consistency is protected by deterministic required CI.
- [ ] Issue `#1132` durable implementation task, branch and PR are created after this reconciliation merges.
- [ ] All 50 Issues and related PRs/tasks are terminal.
- [ ] Final fresh audit, real API-mode E2E, exact-image validation and exact-head CI pass.

## Context checkpoint

```yaml
checkpoint_version: 7
updated_at: 2026-08-05T16:20:00Z
head: 108eff8149f3c5dba77bfcdeaea0c63c8a22b551
status: active
invocation_started_at: 2026-08-05T16:15:00Z
last_progress_at: 2026-08-05T16:20:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 1
stall_warnings: 0
proven:
  - PR 1159 merged and closed Issue 1122
  - archived Issue 1122 task exists and ownership is released
  - Issue 1132 has no active task, branch or open implementation PR
  - Issue 1137 remains open only for protected Authentik acceptance
  - previous coordinator state was stale and selected completed Issue 1122
  - deterministic consistency validation is added in this reconciliation
unknown:
  - terminal exact-head result of the coordinator reconciliation PR
  - protected Authentik acceptance outcome for Issue 1137
conflicts: []
blockers: []
next_action: Merge the coordinator reconciliation only after exact-head governance and required CI pass, then create exactly one durable Issue 1132 child task, implementation branch and PR from the resulting develop head.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: portal-coordinator-recovery-20260805T161500Z
  session_started_at: 2026-08-05T16:15:00Z
  checkpointed_at: 2026-08-05T16:20:00Z
  last_progress_at: 2026-08-05T16:20:00Z
  phase: stale_state_reconciliation
  exact_head: 108eff8149f3c5dba77bfcdeaea0c63c8a22b551
  active_operation: coordinator programme reconciliation
  operation_started_at: 2026-08-05T16:15:00Z
  wait_deadline_at: 2026-08-05T17:00:00Z
  check_generation: portal-coordinator-1250-reconciliation
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: reconciliation PR exact-head checks become terminal
  next_action: Validate canonical programme, coordinator and consistency test on the reconciliation head; merge only through branch protection.
```
