# FTAI-CA-A11Y-1420 — Strategy Lab keyboard experiment selection

```yaml
task_id: FTAI-CA-A11Y-1420-strategy-lab-keyboard
programme_id: FTAI-20260805-platform-continuous-assurance
issue: 1420
parent_issue: 1140
repository: blakinio/freqtrade
lane: whole-platform-assurance
task_kind: implementation
phase: implementing
status: implementing
priority: P2
prompting_standard_version: 2.1
execution_policy_version: 2
execution_mode: github_only
run_scope: single_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
base_branch: develop
base_head: 76ab4293f1d25baa4a7ecb60ae00772171f95923
branch: repair/1420-strategy-lab-keyboard
claim_id: FTAI-CA-A11Y-1420-20260809T1609Z
claim_session_id: repair-1420-chat-20260809T1609Z
conflict_groups:
  - portal-strategy-lab-ui
owned_paths:
  - ai_platform/portal/web/app/ai/experiments/strategy-lab-client.tsx
  - ai_platform/portal/web/e2e/specs/ai/**
  - docs/agents/tasks/active/FTAI-CA-A11Y-1420-strategy-lab-keyboard.md
  - docs/agents/tasks/archive/FTAI-CA-A11Y-1420-strategy-lab-keyboard.md
forbidden_paths:
  - ai_platform/portal/api/**
  - ai_platform/portal/security/**
  - freqtrade/**
  - deploy/**
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Replace the pointer-only Strategy Lab experiment-row activation with a native keyboard-operable action and prove the same experiment-detail behavior through Playwright without broadening into the parent WCAG programme.

## Live re-validation

`CONFIRMED` on `develop@76ab4293f1d25baa4a7ecb60ae00772171f95923`:

- `strategy-lab-client.tsx` attaches `onClick` to `<tr>` and `cursor: pointer`;
- the row is not focusable and exposes no native keyboard activation target for opening experiment detail;
- fixture data contains two deterministic experiment IDs, allowing a keyboard regression to select the second experiment and prove the detail changed;
- no related implementation PR for Issue #1420 exists.

## Acceptance inventory

- [ ] Native focusable semantic control exists for experiment selection.
- [ ] Pointer and keyboard activation call the same experiment-load behavior.
- [ ] Non-focusable `<tr>` is no longer the sole activation target.
- [ ] Keyboard focus is visible/discoverable without a hidden focus target.
- [ ] Playwright proves keyboard activation of the second fixture experiment loads that exact experiment detail.
- [ ] Existing pointer behavior remains available through the same native control.
- [ ] No backend/security/runtime/deployment/live-capital boundary changes.
- [ ] Focused validation passes.
- [ ] Independent audit has zero open material findings.
- [ ] Required exact-head CI passes.
- [ ] PR, Issue, task and claim reach terminal state and ownership is released.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-09T16:11:00Z
status: implementing
proven:
  - Issue 1420 is an atomic child of parent finding 1140
  - claim FTAI-CA-A11Y-1420-20260809T1609Z is the only claim on Issue 1420
  - current develop defect is confirmed in strategy-lab-client.tsx
  - fixture Strategy Lab exposes deterministic baseline and variant experiments
unknown: []
conflicts: []
blockers: []
next_action: Replace pointer-only row activation with a native button, add a keyboard Playwright regression, then run focused validation and open the single delivery PR.
```
