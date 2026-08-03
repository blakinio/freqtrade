# FTAI-20260803 Portal Remediation Programme Coordinator

```yaml
task_id: FTAI-20260803-portal-remediation-program
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: durable_remediation_program
phase: coordinate
status: ready
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
branch: program/FTAI-20260803-portal-remediation
base_branch: develop
base_head: ba4173e975b6ae40c8b0266e3c15cb1b19a0755d
pr: none
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

## Initialization evidence

- Audit PR `#1082` was exact-head validated, marked ready and squash-merged.
- Current programme base is `develop@ba4173e975b6ae40c8b0266e3c15cb1b19a0755d`.
- The audit baseline contains documentation, inventory tooling and evidence only; no product repairs were transferred into it.
- No existing programme/task named `FTAI-20260803-portal-remediation`, no overlapping remediation branch and no open Portal remediation implementation PR were found during live preflight.
- All 50 authorized Issues were open at initialization.
- The first safe READY issue is `#1124`, an active application-session authorization failure on Liquid20 local-file BFF reads.

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
- [x] Initial dependency graph, producer ownership and barriers are durable.
- [x] Current exact `develop` head is recorded.
- [x] One exact programme next action is recorded.
- [ ] All 50 Issues are terminal.
- [ ] All related PRs/tasks are terminal and ownership is released.
- [ ] Final fresh audit, real API-mode E2E, exact-image validation and exact-head CI pass.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-03T10:24:00Z
head: e02da211b1f44636b876754ec356d67e17276108
branch: program/FTAI-20260803-portal-remediation
pr: none
status: ready
context_routes:
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
  - docs/ai_platform/portal/AUDIT_2026-08-02_END_TO_END_COMPLETENESS.md
  - issue #1124
owned_paths:
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-program.md
proven:
  - audit PR #1082 merged into develop at ba4173e975b6ae40c8b0266e3c15cb1b19a0755d
  - all 50 authorized implementation Issues were open at initialization
  - no existing remediation programme, branch or open implementation PR was found
  - issue #1124 is the highest-priority independent READY security containment task
  - no product or protected-environment mutation has occurred in programme initialization
derived:
  - shared producer work must be serialized according to the programme ownership table
  - programme setup can merge as a documentation-only lifecycle PR before product child work
unknown:
  - exact Issue label, milestone and GitHub Project metadata not exposed by the available search response
  - future protected-target resources and approvals
conflicts:
  - historical programme completion claims conflict with the merged audit; the audit and live runtime evidence control
first_failure:
  marker: issue-1124-liquid20-current-session-authorization
  evidence: audit PR #1082 and issue #1124
rejected_hypotheses:
  - audit completion means product remediation is complete; rejected by 50 open implementation findings
  - fixture browser evidence proves API-mode composition; rejected by audit evidence
changed_paths:
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-program.md
validation:
  - command: live GitHub inspection of develop, PR #1082, workflow runs, reviews, threads, branches, PRs and authorized Issues
    result: PASS
    evidence: develop ba4173e975b6ae40c8b0266e3c15cb1b19a0755d; PR #1082 merged
  - command: programme/task policy review against prompting standard 2.1 and execution policy 2
    result: PASS
    evidence: required governance documents read from exact trusted develop base
blockers:
  - none
next_action: Create and claim child task FTAI-20260803-portal-remediation-1124 from the current exact develop head and begin the bounded Liquid20 session-authorization repair.
```
