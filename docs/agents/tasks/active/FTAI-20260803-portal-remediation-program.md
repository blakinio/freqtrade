# FTAI-20260803 Portal Remediation Programme Coordinator

```yaml
task_id: FTAI-20260803-portal-remediation-program
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: durable_remediation_program
phase: coordinate
status: active
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: high
decomposition_decision: split
execution_mode: chat
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
last_resolved_develop_head: f1bf851733ecc870f61c1206b0ee0fe8755c6e67
current_child_task: pending_issue_1122_creation
current_child_branch: pending
current_child_pr: pending
current_child_head: f1bf851733ecc870f61c1206b0ee0fe8755c6e67
closed_issues: 3
active_issues: 0
waiting_issues: 2
blocked_issues: 0
repository_implemented_but_open_issues: 1
owned_paths:
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-program.md
shared_path_leases: []
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Objective

Coordinate and execute the separate implementation programme covering exactly the 50 Issues listed in `docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md`. This task owns programme state, dependency/barrier resolution, child-task selection and terminal reconciliation. It does not own product implementation paths and cannot be used as an omnibus repair PR.

## Terminal progress

- Audit PR `#1082` is merged and remains the audit-only baseline.
- Programme initialization PR `#1145` is merged.
- Issues `#1124`, `#1126` and `#1127` are merged, closed and archived.
- Issue `#1137` repository implementation merged through PR `#1154` at `f1bf851733ecc870f61c1206b0ee0fe8755c6e67` after exact-image, independent PostgreSQL concurrency, fresh audit, workflow-security and full exact-head CI passed.
- Issue `#1137` remains open and its task is `waiting` only for protected Authentik staging concurrency using an authorized synthetic identity. Its repository ownership and OIDC state-claim lease are released.
- Issue `#1132` is not safe to start before `#1122`: complete replay protection requires a durable production table, while `#1122` is the sole migration/schema authority.
- Issue `#1122` is the next safe READY task.

## Coordination rules

- One Issue is one acceptance unit; create a durable child task, branch and PR before product mutation.
- A multi-Issue PR requires a recorded atomic shared-contract justification.
- Shared producers and consumers follow the sole-owner table in the programme record.
- Do not dispatch a child while its paths or producer lease overlap an active task.
- A task waiting on protected acceptance is checkpointed; owner instruction permits continuing an independent READY producer task.
- Product Issues close only after implementation, focused/integration validation, independent audit, applicable real API-mode/system E2E, exact-head CI, terminal PR state, task archival and ownership release.
- Repository merge authority does not authorize protected deployment, credentials, live trading, withdrawals or capital.

## Acceptance

- [x] Audit PR `#1082` is terminal and evidence is available on `develop`.
- [x] Exact authorized Issue inventory and severity/module map are durable.
- [x] Dependency graph, producer ownership and barriers are durable.
- [x] Three authorized Issues are merged, closed and archived.
- [x] Issue `#1137` repository work is merged and protected acceptance is truthfully separated.
- [x] Current exact `develop` and one exact programme next action are recorded.
- [ ] Issue `#1122` durable task, branch and PR are created and executed.
- [ ] All 50 Issues are terminal.
- [ ] All related PRs/tasks are terminal and ownership is released.
- [ ] Final fresh audit, real API-mode E2E, exact-image validation and exact-head CI pass.

## Context checkpoint

```yaml
checkpoint_version: 6
updated_at: 2026-08-03T15:15:00Z
head: f1bf851733ecc870f61c1206b0ee0fe8755c6e67
status: active
invocation_started_at: 2026-08-03T14:26:00Z
last_progress_at: 2026-08-03T15:15:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 1
stall_warnings: 0
context_routes:
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
  - issue #1122
  - issue #1132
  - issue #1137
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1137.md
proven:
  - PR 1154 merged at f1bf851733ecc870f61c1206b0ee0fe8755c6e67 after all exact-head gates passed
  - Issue 1137 remains open only for protected Authentik staging synthetic-identity concurrency
  - Issue 1137 repository ownership and OIDC state-claim lease are released
  - Issue 1132 requires durable replay persistence and cannot create a competing migration authority
  - Issue 1122 is the sole migration/schema producer and has no active task or implementation PR
  - no protected production, credential, trading, withdrawal or live-capital mutation occurred
derived:
  - Issue 1122 is the highest-priority safe READY task before Issue 1132
unknown:
  - protected Authentik staging concurrency outcome for Issue 1137
  - exact current ORM/migration drift on post-1154 develop until Issue 1122 inventory runs
conflicts: []
blockers: []
next_action: Create the Issue 1122 durable task and implementation branch from develop head f1bf851733ecc870f61c1206b0ee0fe8755c6e67, then inventory and repair the authoritative migration/schema/dialect foundation.
```
