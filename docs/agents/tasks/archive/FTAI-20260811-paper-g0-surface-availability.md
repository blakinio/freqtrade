# FTAI-20260811 — PAPER G0 Product Surface Availability Truth

```yaml
task_id: FTAI-20260811-paper-g0-surface-availability
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: product_truth_guardrail
phase: closeout
status: completed
priority: high
execution_mode: github_only
base_branch: develop
delivery_branch: feat/paper-g0-surface-availability-20260811
delivery_pr: 1470
delivery_head: 26366c77870a6b239bdee5158784a1eac6b25919
merge_commit: 8e09a6a372a8e867b942f8f216562e867a3f7f81
paper_gate: G0
paper_work_item: 7
live_capital_authorized: false
protected_production_deployment_authorized: false
repair_cycles_for_current_gate: 5
repair_budget_exception_authorized: true
owner_continuous_repair_authorization: true
ownership_released: true
```

## Result

PAPER G0 work item 7 is complete. Every canonical left-navigation surface whose living exact-head completeness ledger classifies overall as `DISCONNECTED` or `MISSING` is projected into the Portal as explicitly unavailable. The projection is CI-checked against the living ledger, unavailable navigation state is visible and accessible, and direct-route warnings do not suppress bounded read-only evidence.

The direct-route advisory uses `role="note"` with an accessible label rather than the generic application `status` role. This preserves truthful unavailable-state semantics while keeping existing bot-finalization and terminal-risk result messages unambiguous.

No downstream disconnected capability, ledger-status weakening, credential, real order submission, withdrawal, automatic promotion, protected deployment, LIVE authority or live capital was introduced.

## Delivered paths

- `ai_platform/portal/web/lib/product-surface-availability.json`
- `ai_platform/portal/web/components/surface-availability-notice.tsx`
- `ai_platform/portal/web/components/app-shell.tsx`
- `ai_platform/portal/web/e2e/specs/surface-availability.spec.ts`
- `tools/portal_audit/navigation_matrix.py`
- `tests/ci/test_portal_surface_availability.py`

## Terminal evidence

```yaml
delivery_pr:
  number: 1470
  state: merged
  final_head: 26366c77870a6b239bdee5158784a1eac6b25919
  merge_commit: 8e09a6a372a8e867b942f8f216562e867a3f7f81
  base_before_merge: 170b69d2a14e254cd1fb6d2f633c9fb77d2466de
  behind_by_before_merge: 0
  changed_files: 7
independent_audit:
  result: PASS
  reviewer: Codex
  reviewed_commit: 26366c7787
  comment_id: 5256972062
  material_findings: 0
review_hygiene:
  unresolved_material_threads: 0
exact_head_ci:
  - name: Freqtrade CI
    run_id: 31520444072
    result: PASS
  - name: Risk-aware component CI
    run_id: 31520444328
    result: PASS
  - name: CodeQL Security Analysis
    run_id: 31520444273
    result: PASS
  - name: GitHub Actions Security Analysis with zizmor
    run_id: 31520444218
    result: PASS
  - name: AI Platform WickHunter Market Evidence CI
    run_id: 31520444139
    result: PASS
  - name: Portal WickHunter Browser E2E
    run_id: 31520444347
    result: PASS
  - name: Portal API Mode Browser
    run_id: 31520444114
    result: PASS
  - name: Portal Exact-Image Supply Chain
    run_id: 31520444057
    result: PASS
browser_e2e:
  full_portal_chromium_job: 93876063116
  full_portal_chromium_result: PASS
  programme_critical_chromium_job: 93876644165
  programme_critical_chromium_result: PASS
  universal_chromium_job: 93877551308
  universal_chromium_result: PASS
  focused_surface_availability: PASS
checkpoint_validation:
  job: 93876644193
  step: Validate durable checkpoint
  result: PASS
static_completeness_audit:
  job: 93877479337
  result: PASS
```

## Repair history

1. Added critical routing to the focused browser proof; the first location was outside Playwright `testDir`.
2. Moved the spec into `e2e/specs` and exposed the unavailable state through an accessible description; prior Codex P1/P2 findings were resolved.
3. Applied the deterministic `ruff-format` output emitted by Freqtrade CI.
4. Re-encoded the Context checkpoint to shared governance contract version 1 after an owner-authorized budget exception; the exact successor received a fresh Codex PASS.
5. Full Chromium regression exposed a deterministic duplicate-`role="status"` collision in existing Create Bot and Trading Terminal journeys. The availability advisory was changed to accessible `role="note"`; the final exact-head full Chromium, critical and universal journeys all passed.

## Durable handoff

```yaml
completed_at: 2026-08-11T18:19:33Z
develop_after_delivery: 8e09a6a372a8e867b942f8f216562e867a3f7f81
programme_complete: false
blockers: []
next_action: Re-evaluate the current PAPER programme barrier from live develop state and continue the highest-priority safe READY package without reopening work item 7.
```
