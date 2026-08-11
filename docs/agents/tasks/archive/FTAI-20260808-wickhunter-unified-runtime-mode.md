---
task_id: FTAI-20260808-wickhunter-unified-runtime-mode
project_lane: freqtrade-wickhunter
programme: WickHunter
status: completed
task_kind: implementation
feature_scope:
  type: full_stack
  completion_claim: partial_producer
repository: blakinio/freqtrade
base_branch: develop
delivery_branch: feat/wickhunter-unified-runtime-mode-1396
delivery_pr: 1397
related_issue: 1396
completed: 2026-08-08
archived: 2026-08-11
live_capital_authorized: false
trading_credentials_authorized: false
real_order_adapter_authorized: false
real_exchange_execution_authorized: false
ownership_released: true
---

# WickHunter Unified Runtime Mode — producer terminal closeout

## Result

The bounded WickHunter producer slice is complete. It reuses canonical `BotMode`, represents SHADOW/PAPER mode and PAPER eligibility as immutable digest material, resolves only zero-real-trading-authority capabilities, and keeps LIVE_BLOCKED/RESEARCH fail-closed for managed trading runtime use.

This closeout is **only for the producer task**. Issue #1396 and the full Portal/runtime-generation consumer path remain separate programme work; archiving this producer does not claim those consumers complete.

## Delivery evidence

```yaml
delivery:
  pull_request: 1397
  state: merged
  final_head: 5eee605343b2fbcd1e1e6231ed80315195bd5eba
  merge_commit: f46d10e30302b7310fe2a6e235c2ca05a0281a0a
  changed_paths:
    - ai_platform/wickhunter/runtime_mode.py
    - tests/ai_platform/test_wickhunter_runtime_mode.py
    - docs/agents/tasks/active/FTAI-20260808-wickhunter-unified-runtime-mode.md
```

## Independent audit

Final Codex review of exact head `5eee605343b2fbcd1e1e6231ed80315195bd5eba` reported no major issues (PR comment `5228471720`). Prior material review findings were repaired before that review.

## Exact-head CI

```yaml
exact_head_ci:
  - name: Freqtrade CI
    run_id: 31281392431
    result: PASS
  - name: Risk-aware component CI
    run_id: 31281392481
    result: PASS
  - name: CodeQL Security Analysis
    run_id: 31281392428
    result: PASS
  - name: GitHub Actions Security Analysis with zizmor
    run_id: 31281392432
    result: PASS
  - name: Pre-commit Types update
    run_id: 31281392429
    result: SKIPPED_BY_ROUTING
```

## Handover

The remaining consumer must bind the producer contract through the canonical Portal generation chain rather than introducing another authority:

`BotConfigRevision -> normalized runtime config digest -> RuntimeGeneration -> rollout -> observed generation reconciliation`.

The UI may expose SHADOW/PAPER only from server-provided eligibility. LIVE remains unavailable under current authority.

## Closeout

```yaml
closeout:
  implementation_complete: true
  bounded_producer_outcome_verified: true
  independent_audit: PASS
  material_findings_open: 0
  exact_head_ci: PASS
  delivery_pr_terminal: true
  task_archived: true
  ownership_released: true
  issue_1396_closed_by_this_task: false
  remaining_programme_work: canonical Portal/runtime-generation consumer integration and broader WickHunter acceptance
```

PAPER-only safety remains unchanged. No exchange credential, real order adapter, real exchange execution, withdrawal, automatic promotion or LIVE/live-capital authority was introduced.
