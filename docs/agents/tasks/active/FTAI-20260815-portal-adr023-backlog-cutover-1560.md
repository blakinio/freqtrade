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
next_action: Validate the current PR #1564 exact head, resolve the verified review threads, merge the cutover to develop, archive this task, and close Issue #1560.
---

# ADR-023 Portal/WickHunter backlog cutover

## Objective

Make ADR-023 operational in repository coordination by retiring the former 50-Issue coordinator, classifying all remaining old Portal/WickHunter work, archiving stale active tasks, and establishing #1561 as the sole current P1 owner-facing vertical slice.

## Owned paths

- `docs/ai_platform/portal/ADR023_BACKLOG_RECLASSIFICATION_2026-08-15.md`
- `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`
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
- [x] Additional open WickHunter/PAPER producer work is classified, including residual #1501.
- [x] Open related delivery PRs have a terminal/reframe disposition.
- [x] Former 50-Issue programme cannot autonomously dispatch #1132.
- [x] Former coordinator is archived and no longer active.
- [x] Stale #1396 and old #1137 protected-acceptance tasks are archived without rewriting historical evidence.
- [x] Completed ADR-023 architecture-reset task #1555 is archived.
- [x] Successor MVP Issue #1561 exists.
- [x] Obsolete/superseded issues and PRs recorded by the ledger are intentionally terminal.
- [x] #1211 programme issue points to ADR-023 and #1561.
- [ ] Exact-head CI passes and all review threads are resolved.
- [ ] Cutover PR merges to develop.
- [ ] This task is archived and Issue #1560 closes.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-16T08:32:38+02:00
head: 43f1f517b323e5e72f23f28a4ed14319cd3f250c
branch: docs/portal-adr023-backlog-cutover-20260815
pr: 1564
status: validating
context_routes:
  - Issue #1560 ADR-023 backlog cutover
  - PR #1564 cutover delivery
  - Issue #1561 Developer Quant MVP successor
  - ADR-023 current Portal product authority
owned_paths:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1137.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-program.md
  - docs/agents/tasks/active/FTAI-20260812-wh09-e2e-recovery-1396.md
  - docs/agents/tasks/active/FTAI-20260815-portal-adr023-backlog-cutover-1560.md
  - docs/agents/tasks/active/FTAI-20260815-portal-developer-platform-reset-1555.md
  - docs/agents/tasks/archive/FTAI-20260803-portal-remediation-1137.md
  - docs/agents/tasks/archive/FTAI-20260803-portal-remediation-program.md
  - docs/agents/tasks/archive/FTAI-20260812-wh09-e2e-recovery-1396.md
  - docs/agents/tasks/archive/FTAI-20260815-portal-developer-platform-reset-1555.md
  - docs/ai_platform/portal/ADR023_BACKLOG_RECLASSIFICATION_2026-08-15.md
  - tests/ci/test_portal_programme_coordinator_consistency.py
proven:
  - ADR-023 merged via PR #1558 at develop@1f62ff29f4a2a25c929218bd3b69bf19257f3055.
  - Issue #1560 owns the ADR-023 backlog cutover.
  - Issue #1561 owns the current Developer Quant MVP vertical slice.
  - Canonical classification ledger covers the former 50-Issue inventory and additional legacy Portal/WickHunter/PAPER work including #1501.
  - Former coordinator and stale old-mode/protected-acceptance task records are archived on this branch.
  - Legacy delivery PRs recorded for closure are terminal without merge; useful #1553 merged to develop as 876e5755dc3cc699e8d271a6068730f119b1e152.
  - Obsolete legacy Issues including #1396, #1144 and #1501 are closed not_planned.
  - Programme parent #1211 now names Developer Quant Portal and points to ADR-023 and #1561.
derived:
  - The former PAPER-first producer graph can no longer be the current Portal work-selection authority after this cutover merges.
  - Issue #1561 is the only current P1 owner-facing Portal/WickHunter product journey established by this cutover.
unknown:
  - Exact-head CI result after this checkpoint/programme correction commit.
  - Whether branch protection will require #1564 to be updated onto the latest develop head before merge.
conflicts: []
first_failure:
  marker: PR_REVIEW_CHECKPOINT_CONTRACT
  evidence: PR #1564 review identified missing v1 checkpoint fields and a non-literal #1561 programme pointer; both are corrected on this branch.
rejected_hypotheses:
  - The original checkpoint was already v1-complete; rejected against tools/agents/checkpoint.py and docs/agents/GOVERNANCE_CONTRACT.json.
  - Issue #1501 could remain outside the cutover ledger; rejected because it is a residual PAPER G0 current-routing task.
changed_paths:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1137.md
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-program.md
  - docs/agents/tasks/active/FTAI-20260812-wh09-e2e-recovery-1396.md
  - docs/agents/tasks/active/FTAI-20260815-portal-adr023-backlog-cutover-1560.md
  - docs/agents/tasks/active/FTAI-20260815-portal-developer-platform-reset-1555.md
  - docs/agents/tasks/archive/FTAI-20260803-portal-remediation-1137.md
  - docs/agents/tasks/archive/FTAI-20260803-portal-remediation-program.md
  - docs/agents/tasks/archive/FTAI-20260812-wh09-e2e-recovery-1396.md
  - docs/agents/tasks/archive/FTAI-20260815-portal-developer-platform-reset-1555.md
  - docs/ai_platform/portal/ADR023_BACKLOG_RECLASSIFICATION_2026-08-15.md
  - tests/ci/test_portal_programme_coordinator_consistency.py
validation:
  - command: python tools/agents/checkpoint.py docs/agents/tasks/active/FTAI-20260815-portal-adr023-backlog-cutover-1560.md --require-checkpoint
    result: NOT_RUN
    evidence: Checkpoint was rewritten from the current v1 contract; exact-head repository validation is pending after this commit.
  - command: GitHub PR #1553 required checks and squash merge
    result: PASS
    evidence: Required CI was green and #1553 merged to develop as 876e5755dc3cc699e8d271a6068730f119b1e152.
  - command: GitHub legacy PR and obsolete-Issue disposition audit
    result: PASS
    evidence: Ledger-designated legacy delivery PRs were closed without merge and OBSOLETE Issues were closed not_planned; #1211 was reframed before cutover merge.
blockers: []
next_action: Validate the current PR #1564 exact head, resolve only review threads whose findings are now materially fixed, merge to develop, archive this task, and close Issue #1560.
```
