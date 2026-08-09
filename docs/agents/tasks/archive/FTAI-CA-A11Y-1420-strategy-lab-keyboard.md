# FTAI-CA-A11Y-1420 — Strategy Lab keyboard experiment selection

```yaml
task_id: FTAI-CA-A11Y-1420-strategy-lab-keyboard
programme_id: FTAI-20260805-platform-continuous-assurance
issue: 1420
parent_issue: 1140
repository: blakinio/freqtrade
lane: whole-platform-assurance
task_kind: implementation
phase: closeout
status: completed
priority: P2
prompting_standard_version: 2.1
execution_policy_version: 2
execution_mode: github_only
run_scope: single_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
base_branch: develop
product_validation_head: 1aa0fa50b7b24e27c5b8201479dabbf3864ddcb5
branch: repair/1420-strategy-lab-keyboard
pull_request: 1421
claim_id: FTAI-CA-A11Y-1420-20260809T1609Z
claim_session_id: repair-1420-chat-20260809T1609Z
finding_disposition: CONFIRMED
conflict_groups:
  - portal-strategy-lab-ui
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Replace the pointer-only Strategy Lab experiment-row activation with a native keyboard-operable action and prove the same experiment-detail behavior through Playwright without broadening into parent WCAG programme #1140.

## Implemented result

- Removed `onClick`/pointer semantics from the experiment `<tr>`.
- Added a native focusable `button` per experiment using the same `openExperiment(experiment_id)` action for pointer and keyboard activation.
- Added deterministic selected-experiment state on the existing E2E test boundary.
- Added `strategy-lab-keyboard.spec.ts` using the two deterministic Strategy Lab fixture experiment IDs.
- The regression is tagged `@a11y`, `@regression`, and `@critical`, so ordinary Portal PR Chromium CI executes it.

## Validation evidence

```yaml
validation:
  independent_audit:
    result: PASS
    material_findings_open: 0
    remediated_finding:
      - initial regression lacked @critical routing and would not run in ordinary Portal PR critical Chromium CI
  e2e:
    result: PASS
    head: 1aa0fa50b7b24e27c5b8201479dabbf3864ddcb5
    workflow_run: 31323660989
    job: 93270583218
    journey: Strategy Lab variant experiment focused and activated with Enter, then baseline restored with pointer click
  component_validation:
    head: 1aa0fa50b7b24e27c5b8201479dabbf3864ddcb5
    risk_aware_component_ci_run: 31323660989
    result: PASS
    portal_web_validation: PASS
    portal_chromium_regression: PASS
  exact_head_ci:
    product_head: 1aa0fa50b7b24e27c5b8201479dabbf3864ddcb5
    freqtrade_ci_run: 31323660816
    freqtrade_ci: PASS
    codeql: PASS
    zizmor: PASS
    portal_api_mode_browser: PASS
    portal_exact_image_supply_chain: PASS
```

The product behavior and browser regression are proven on `1aa0fa50...`. This archive-only lifecycle commit must receive its own exact-head repository CI before PR #1421 is merged.

## Scope and safety

No backend, authorization, tenant, runtime execution, trading, deployment, credential, protected-environment or live-capital boundary changed. Parent #1140 remains open for the broader WCAG/accessibility programme.

## Terminal checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-09T16:28:00Z
status: completed
proven:
  - Issue 1420 defect was confirmed against live develop before mutation
  - native keyboard-operable experiment selection is implemented
  - pointer and keyboard actions share openExperiment(experiment_id)
  - critical Chromium E2E passed on product head 1aa0fa50b7b24e27c5b8201479dabbf3864ddcb5
  - independent validator has zero open material findings
  - parent Issue 1140 remains open and linked
unknown: []
conflicts: []
blockers: []
next_action: Merge PR #1421 only after required exact-head CI passes on the archive/final head, then verify Issue closure and release claim ownership.
```
