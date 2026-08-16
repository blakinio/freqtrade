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
next_action: Validate PR #1564 exact head, merge after required CI passes, then archive this task and close Issue #1560.
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
- `tools/portal_audit/validate_issue_states.py`
- `tools/portal_audit/tests/test_audit_ledger.py`
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
- [x] Legacy completeness-Issue state validation no longer blocks the current Portal under ADR-023 while pre-ADR-023 validation remains fail-closed.
- [ ] Exact-head CI passes and all review threads are resolved.
- [ ] Cutover PR merges to develop.
- [ ] This task is archived and Issue #1560 closes.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-16T11:13:00+02:00
head: dda87f24ef9dca1b601db1c4cf21bd08a0f64890
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
  - docs/agents/tasks/active/FTAI-20260815-portal-adr023-backlog-cutover-1560.md
  - docs/agents/tasks/archive/FTAI-20260803-portal-remediation-1137.md
  - docs/agents/tasks/archive/FTAI-20260803-portal-remediation-program.md
  - docs/agents/tasks/archive/FTAI-20260812-wh09-e2e-recovery-1396.md
  - docs/agents/tasks/archive/FTAI-20260815-portal-developer-platform-reset-1555.md
  - docs/ai_platform/portal/ADR023_BACKLOG_RECLASSIFICATION_2026-08-15.md
  - tools/portal_audit/validate_issue_states.py
  - tools/portal_audit/tests/test_audit_ledger.py
  - tests/ci/test_portal_programme_coordinator_consistency.py
proven:
  - ADR-023 merged via PR #1558 at develop@1f62ff29f4a2a25c929218bd3b69bf19257f3055.
  - Issue #1561 owns the current Developer Quant MVP vertical slice.
  - Canonical classification ledger covers the former 50-Issue inventory and additional legacy Portal/WickHunter/PAPER work including #1501.
  - Legacy delivery PRs recorded for closure are terminal without merge; useful #1553 merged to develop as 876e5755dc3cc699e8d271a6068730f119b1e152.
  - Obsolete legacy Issues including #1396, #1144 and #1501 are closed not_planned.
  - Programme parent #1211 now names Developer Quant Portal and points to ADR-023 and #1561.
  - PR #1564 source branch was restored at exact prior head d71c13aede569f40572430d23c6053abffe7637d after it was unexpectedly deleted while the PR remained open.
  - The only failing Risk-aware component job was the legacy completeness Issue-state network gate; all product/browser/exact-image/core checks on d71c13a were green.
derived:
  - The former PAPER-first producer graph can no longer be the current Portal work-selection authority after this cutover merges.
  - Legacy completeness-Issue state is compatibility diagnostics under ADR-023 rather than current delivery authority.
unknown:
  - Exact-head CI result after the ADR-023 legacy audit-gate repair.
conflicts: []
first_failure:
  marker: LEGACY_COMPLETENESS_ISSUE_STATE_HTTP_403
  evidence: Risk-aware component CI run 31931822680 failed only when tools/portal_audit/validate_issue_states.py queried GitHub Issue #1085 and received HTTP 403; the old Issue-state authority is also semantically superseded by ADR-023.
rejected_hypotheses:
  - Product/runtime code caused the Risk-aware failure; rejected because Freqtrade CI, Portal API Browser, WickHunter Browser E2E, Exact-Image, CodeQL and all other selected component jobs passed.
  - Retrying the old network check alone would make it a valid current gate; rejected because ADR-023 explicitly supersedes the old completeness-Issue state as current Portal authority.
changed_paths:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
  - docs/agents/tasks/active/FTAI-20260815-portal-adr023-backlog-cutover-1560.md
  - docs/agents/tasks/archive/FTAI-20260803-portal-remediation-1137.md
  - docs/agents/tasks/archive/FTAI-20260803-portal-remediation-program.md
  - docs/agents/tasks/archive/FTAI-20260812-wh09-e2e-recovery-1396.md
  - docs/agents/tasks/archive/FTAI-20260815-portal-developer-platform-reset-1555.md
  - docs/ai_platform/portal/ADR023_BACKLOG_RECLASSIFICATION_2026-08-15.md
  - tools/portal_audit/validate_issue_states.py
  - tools/portal_audit/tests/test_audit_ledger.py
  - tests/ci/test_portal_programme_coordinator_consistency.py
validation:
  - command: Risk-aware component CI run 31931822680 on d71c13aede569f40572430d23c6053abffe7637d
    result: FAIL
    evidence: Only legacy Portal completeness Issue-state step failed with GitHub API HTTP 403; all other selected component/product jobs passed.
  - command: Freqtrade CI run 31931822493 on d71c13aede569f40572430d23c6053abffe7637d
    result: PASS
    evidence: Freqtrade CI completed successfully.
  - command: Portal API/WickHunter Browser/Exact-Image and CodeQL on d71c13aede569f40572430d23c6053abffe7637d
    result: PASS
    evidence: All named workflows completed successfully.
  - command: tools/portal_audit regression for ADR-023 legacy issue-state applicability
    result: NOT_RUN
    evidence: New regression tests are committed on dda87f24ef9dca1b601db1c4cf21bd08a0f64890 and await exact-head CI.
blockers: []
next_action: Validate PR #1564 exact head, merge after required CI passes, then archive this task and close Issue #1560.
```
