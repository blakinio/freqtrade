---
task_id: FTAI-20260815-portal-adr023-backlog-cutover-1560
status: validating
repository: blakinio/freqtrade
lane: freqtrade-portal
related_issue: 1560
branch: docs/portal-adr023-backlog-cutover-20260815
base_head: 1f62ff29f4a2a25c929218bd3b69bf19257f3055
owner: chatgpt
task_kind: architecture_closeout
phase: backlog_cutover
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: single
execution_mode: chat
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
next_action: Open the cutover PR, pass exact-head CI/review, merge, then execute the issue/PR terminal dispositions recorded in the ledger.
---

# ADR-023 Portal/WickHunter backlog cutover

## Objective

Make ADR-023 operational in repository coordination by retiring the former 50-Issue coordinator, classifying all remaining old Portal/WickHunter work, archiving stale active tasks, and establishing #1561 as the sole current P1 owner-facing vertical slice.

## Owned paths

- `docs/ai_platform/portal/ADR023_BACKLOG_RECLASSIFICATION_2026-08-15.md`
- `docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md`
- `docs/agents/tasks/archive/FTAI-20260803-portal-remediation-program.md`
- `docs/agents/tasks/archive/FTAI-20260803-portal-remediation-1137.md`
- `docs/agents/tasks/archive/FTAI-20260812-wh09-e2e-recovery-1396.md`
- `docs/agents/tasks/archive/FTAI-20260815-portal-developer-platform-reset-1555.md`
- this task record
- `tests/ci/test_portal_programme_coordinator_consistency.py`

## Acceptance

- [x] Exact classification base is ADR-023 merge `1f62ff29...`.
- [x] Every open former 50-Issue remediation item is `KEEP_NOW`, `SIMPLIFY`, `DEFER` or `OBSOLETE`.
- [x] Additional open WickHunter/PAPER producer work is classified.
- [x] Open related delivery PRs have a terminal/reframe disposition.
- [x] Former 50-Issue programme cannot autonomously dispatch #1132.
- [x] Former coordinator is archived and no longer active.
- [x] Stale #1396 and old #1137 protected-acceptance tasks are archived without rewriting historical evidence.
- [x] Completed ADR-023 architecture-reset task #1555 is archived.
- [x] Successor MVP Issue #1561 exists.
- [ ] Exact-head CI passes and all review threads are resolved.
- [ ] Cutover PR merges to develop.
- [ ] Obsolete/superseded issues and PRs recorded by the ledger become intentionally terminal.
- [ ] #1211 programme issue points to current ADR-023 programme/#1561.
- [ ] This task is archived and Issue #1560 closes.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-15T23:20:00+02:00
status: validating
head: 3df78486fb90c8085130c9d73a99cf35fa085930
proven:
  - ADR-023 merged via PR #1558 at develop@1f62ff29f4a2a25c929218bd3b69bf19257f3055.
  - Issue #1560 owns current backlog cutover.
  - Issue #1561 owns current Developer Quant MVP.
  - Canonical classification ledger has been created.
  - Former coordinator and stale old-mode/protected-acceptance tasks have terminal archive records on this branch.
derived:
  - Old PAPER/production/multi-tenant work must not remain as autonomous coordination authority after this cutover merges.
unknown:
  - exact-head CI/review result for the cutover PR until opened
blockers: []
next_action: Open the cutover PR, validate exact-head CI and review, merge, then apply ledger-recorded GitHub issue/PR terminal dispositions.
```
