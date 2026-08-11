# FTAI-20260811 — PAPER G0 Product Surface Availability Truth

```yaml
task_id: FTAI-20260811-paper-g0-surface-availability
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: product_truth_guardrail
phase: validation
status: validating
priority: high
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: develop
delivery_branch: feat/paper-g0-surface-availability-20260811
delivery_pr: 1470
paper_gate: G0
paper_work_item: 7
live_capital_authorized: false
protected_production_deployment_authorized: false
repair_cycles_for_current_gate: 3
repair_budget_exhausted: true
fresh_isolation_repairs: 1
```

## Objective

Close PAPER G0 work item 7 without implementing later-gate product functionality: every canonical left-navigation surface whose living exact-head completeness ledger classifies overall as `DISCONNECTED` or `MISSING` must be explicitly presented as unavailable in the Portal shell and on direct navigation. The web projection must be CI-checked against the canonical ledger so status cannot drift silently.

## Implementation

- `ai_platform/portal/web/lib/product-surface-availability.json` projects exactly the living-ledger `DISCONNECTED`/`MISSING` rows, preserving route, label, status, linked issues/boundary and canonical reason.
- `SurfaceAvailabilityNotice` shows a visible shell-level informational warning on projected direct routes without suppressing useful bounded read-only evidence. The persistent notice uses ARIA `role="note"`; transient action-result `role="status"` channels remain reserved for operation feedback.
- `AppShell` shows `Unavailable` while preserving the established accessible link name; projected links expose `Capability unavailable` through `aria-describedby`.
- `navigation_matrix.py` exact-compares the committed web projection with the living ledger so status/reason/blocker drift fails closed.
- `tests/ci/test_portal_surface_availability.py` independently reconstructs the projection and verifies shell/notice/accessibility contracts, including that the persistent notice cannot reclaim `role="status"`.
- `ai_platform/portal/web/e2e/specs/surface-availability.spec.ts` is inside configured Playwright `testDir`, tagged `@critical` and `@regression`, and proves projected `/ai` versus non-projected `/market/liquidations` behavior.

## Scope

Owned paths:

- `ai_platform/portal/web/lib/product-surface-availability.json`
- `ai_platform/portal/web/components/surface-availability-notice.tsx`
- `ai_platform/portal/web/components/app-shell.tsx`
- `tools/portal_audit/navigation_matrix.py`
- `tests/ci/test_portal_surface_availability.py`
- `ai_platform/portal/web/e2e/specs/surface-availability.spec.ts`
- `docs/agents/tasks/active/FTAI-20260811-paper-g0-surface-availability.md`

Forbidden scope remains downstream capability implementation, ledger-status weakening, #1396/#1450 WickHunter/Liquid20 paths, #1354/#1464 runtime-isolation paths, credentials, protected deployment, real execution, LIVE or live capital.

## Acceptance

- web projection equals exactly the living-ledger `DISCONNECTED`/`MISSING` set;
- navigation and direct routes expose truthful unavailable state;
- assistive technology receives the unavailable status while established link names remain stable;
- the persistent direct-route availability warning does not share the transient action-result `role="status"` channel;
- non-projected routes receive neither warning nor unavailable accessible description;
- ledger projection drift fails CI;
- focused Playwright proof is discovered and selected by ordinary PR critical routing;
- existing action-result Playwright assertions such as create-bot and risk-gate retain unique `getByRole("status")` semantics;
- no product capability or execution/LIVE authority is added;
- final exact-head CI, browser E2E, fresh independent audit and review hygiene pass before merge;
- task remains active until delivery merge is real.

## Repair history

```yaml
parent_repair_cycles:
  used: 3
  budget_exhausted: true
  note: no fourth same-gate parent repair is authorized
fresh_isolation_1:
  reason: exact-head component CI and independent review exposed new material failures after parent repair budget exhaustion
  source_parent_head: fc908158053fa8289829e8f0eaa9537a1ccd8e81
  failures:
    - Risk-aware component CI 31479176155 failed Chromium regression because persistent availability warnings and transient action results both exposed role=status
    - checkpoint review thread PRRT_kwDOTdDTU86YLbnu proved checkpoint_version 5 and validation vocabulary were invalid under GOVERNANCE_CONTRACT.json
  remediation:
    - persistent SurfaceAvailabilityNotice uses role=note instead of role=status
    - static CI guard forbids role=status on the persistent notice
    - context checkpoint is re-encoded as contract version 1 without resetting the parent repair counter
```

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T14:45:00+02:00
head: LIVE_BRANCH_HEAD_REQUIRED
branch: feat/paper-g0-surface-availability-20260811
pr: 1470
status: validating
context_routes:
  - PAPER G0 work item 7 product-surface availability truth
  - living Portal completeness ledger projection
  - Portal Chromium action-result status semantics
owned_paths:
  - ai_platform/portal/web/lib/product-surface-availability.json
  - ai_platform/portal/web/components/surface-availability-notice.tsx
  - ai_platform/portal/web/components/app-shell.tsx
  - ai_platform/portal/web/e2e/specs/surface-availability.spec.ts
  - tools/portal_audit/navigation_matrix.py
  - tests/ci/test_portal_surface_availability.py
  - docs/agents/tasks/active/FTAI-20260811-paper-g0-surface-availability.md
proven:
  - living ledger is the CI-enforced product-surface status authority
  - projected unavailable browser proof is inside configured Playwright testDir and critical-routed
  - navigation links expose Capability unavailable through aria-describedby while retaining their established accessible link names
  - Risk-aware component CI 31479176155 failed because the new persistent warning role=status collided with existing transient action-result role=status locators in create-bot and risk-gate journeys
  - existing transient status locators are legitimate product feedback and must not be weakened to accommodate a persistent informational warning
  - parent repair budget is exhausted at three and this remediation is a fresh bounded isolation rather than a fourth parent cycle
  - current checkpoint predecessor was invalid under governance contract version 1 and resume tooling
  - PAPER remains the only authorized operational trading mode and LIVE remains unreachable/fail-closed
derived:
  - role=note preserves visible and accessible informational semantics for persistent availability truth without usurping the transient status channel
  - after the isolation merges, only exact evidence for the resolved live parent head can authorize delivery merge
unknown:
  - isolation review and CI disposition
  - final parent browser E2E, exact-head CI and independent audit disposition after isolation merge and develop synchronization
conflicts: []
first_failure:
  marker: strict Playwright locator collision caused by duplicate role=status semantics
  evidence: Risk-aware component CI 31479176155; Portal Chromium job 93740261563 and Universal Portal E2E Chromium job 93745474617
rejected_hypotheses:
  - weaken existing create-bot or risk-gate getByRole(status) assertions; rejected because those elements are transient operation-result statuses and their uniqueness is meaningful
  - perform a fourth parent repair cycle; rejected because repair_cycles_for_current_gate is already 3
  - keep checkpoint_version 5 or FAIL_THEN_REPAIRED validation values; rejected because tools/agents/checkpoint.py and GOVERNANCE_CONTRACT.json require checkpoint version 1 and allowed result vocabulary
changed_paths:
  - ai_platform/portal/web/components/surface-availability-notice.tsx
  - tests/ci/test_portal_surface_availability.py
  - docs/agents/tasks/active/FTAI-20260811-paper-g0-surface-availability.md
validation:
  - command: Risk-aware component CI run 31479176155 on parent head fc908158053fa8289829e8f0eaa9537a1ccd8e81
    result: FAIL
    evidence: strict getByRole(status) collisions in create-bot and risk-gate Chromium journeys
  - command: independent review thread PRRT_kwDOTdDTU86YLbnu on parent head fc908158053fa8289829e8f0eaa9537a1ccd8e81
    result: FAIL
    evidence: checkpoint version and validation fields were incompatible with the current governance contract
  - command: product/runtime E2E on parent head fc908158053fa8289829e8f0eaa9537a1ccd8e81
    result: FAIL
    evidence: routed Chromium journeys failed on duplicate status roles; product capability itself was not newly implemented
blockers: []
next_action: Review and validate the fresh isolation repair; if clean, squash-merge it into PR 1470 without resetting the parent repair counter, reply to and resolve the checkpoint P1, synchronize the parent branch with current develop while retaining exactly the seven owned paths, resolve the live parent head, then require fresh independent audit plus Freqtrade CI, Risk-aware component CI, CodeQL, zizmor and routed browser E2E for that exact head before parent merge and post-merge archival.
```
