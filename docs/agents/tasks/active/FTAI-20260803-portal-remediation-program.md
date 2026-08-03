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
last_resolved_develop_head: 9f437158bbb2c7dfc40f10fd1a3aaf8ea11fea17
current_child_task: FTAI-20260803-portal-remediation-1137
current_child_branch: fix/portal-1137-atomic-oidc-state-claim
current_child_pr: 1154
current_child_head: 6035a94106758cf2d2bf3d2a1e32d424a4cc4d30
closed_issues: 3
active_issues: 1
waiting_issues: 0
blocked_issues: 0
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
- Issue `#1124` is merged, closed and archived through PR `#1146`.
- Issue `#1126` is merged, closed and archived through PR `#1149`.
- Issue `#1127` is merged and closed through PR `#1151`; archive and classifier ownership release are recorded by the current closeout task.
- Issue `#1137` is active in PR `#1154` with an atomic conditional login-state claim, repository concurrency tests and a fail-closed exact-image probe. Fresh audit expanded the task to attributable claim/replay/provider/identity terminal evidence before protected-target classification.

## Coordination rules

- One Issue is one acceptance unit; create a durable child task, branch and PR before mutation.
- A multi-Issue PR requires a recorded atomic shared-contract justification.
- Shared producers and consumers follow the sole-owner table in the programme record.
- Do not dispatch a child while its paths or producer lease overlap an active task.
- A task waiting on CI/review/protected acceptance is checkpointed; continue another independent READY task only within the anti-stall budget.
- Product Issues close only after implementation, focused/integration validation, independent audit, applicable real API-mode/system E2E, exact-head CI, terminal PR state, task archival and ownership release.
- Repository merge authority does not authorize protected deployment, credentials, live trading, withdrawals or capital.

## Acceptance

- [x] Audit PR `#1082` is terminal and evidence is available on `develop`.
- [x] Exact authorized Issue inventory and severity/module map are durable.
- [x] Dependency graph, producer ownership and barriers are durable.
- [x] Three authorized Issues are merged, closed and archived/reconciling.
- [x] Current exact `develop` and one exact programme next action are recorded.
- [ ] All 50 Issues are terminal.
- [ ] All related PRs/tasks are terminal and ownership is released.
- [ ] Final fresh audit, real API-mode E2E, exact-image validation and exact-head CI pass.

## Context checkpoint

```yaml
checkpoint_version: 5
updated_at: 2026-08-03T13:38:00Z
head: 9f437158bbb2c7dfc40f10fd1a3aaf8ea11fea17
status: active
context_routes:
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
  - issue #1137
  - PR #1154
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1137.md
proven:
  - audit, programme initialization and Issues 1124, 1126 and 1127 are merged
  - Issue 1127 exact-head CI, staging, exact-image artifacts and fresh audit passed
  - Issue 1127 closed through PR 1151 at merge commit 9f437158bbb2c7dfc40f10fd1a3aaf8ea11fea17
  - Issue 1137 has one active owner/branch/PR on overlapping identity paths
  - the first Issue 1137 exact-image run was false-green with an empty artifact and was replaced by a fail-closed non-empty proof
  - fresh Issue 1137 audit requires attributable terminal callback evidence before repository closeout
  - Issue 1132 is next READY only after Issue 1137 ownership release
  - no protected production, credential, trading, withdrawal or live-capital mutation occurred
derived:
  - PR 1154 must incorporate the exact post-1127 develop head before final validation
  - protected Authentik acceptance may become one WAITING boundary only after all repository-owned Issue 1137 work is complete
unknown:
  - availability of an existing authorized protected Authentik concurrency runner for Issue 1137
conflicts: []
blockers: []
next_action: Merge the Issue 1127 closeout record, integrate that exact develop head into PR 1154, then finish attributable OIDC callback evidence and exact-head validation for Issue 1137.
```
