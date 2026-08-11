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
trusted_base_sha: 6577ae896ed5910f82f9e736fe4a007b6dc10e6e
delivery_branch: feat/paper-g0-surface-availability-20260811
paper_gate: G0
paper_work_item: 7
live_capital_authorized: false
protected_production_deployment_authorized: false
repair_cycles_for_current_gate: 0
```

## Objective

Close PAPER G0 work item 7 without implementing later-gate product functionality: every canonical left-navigation surface whose living exact-head completeness ledger classifies overall as `DISCONNECTED` or `MISSING` must be explicitly presented as unavailable in the Portal shell and on direct navigation. The web projection must be CI-checked against the canonical ledger so status cannot drift silently.

## Proven residual

- `tools/portal_audit/ledger/navigation.json` is the living exact-head implementation-status authority for navigation completeness and currently contains 16 surfaces with overall `DISCONNECTED` or `MISSING`.
- Some pages already fail closed visibly, for example Strategy Catalog renders `Strategy Catalog unavailable` when its missing backend producer fails.
- Other disconnected surfaces can look like normal empty product state. Example: `/ai` renders `No insights yet` and normal-flow copy even though its overall ledger status is `DISCONNECTED` because trusted intelligence/learning producers and model lifecycle workflows are not composed.
- Before this task, `AppShell` rendered all canonical navigation items identically and had no completeness/availability projection.

## Implementation

- `ai_platform/portal/web/lib/product-surface-availability.json` projects exactly the living-ledger rows whose overall status is `DISCONNECTED` or `MISSING`, preserving route, label, status, linked issues/boundary and canonical reason.
- `SurfaceAvailabilityNotice` uses the current pathname to show a visible shell-level warning on direct navigation without suppressing useful bounded read-only evidence that a page may still provide.
- `AppShell` adds a visible `Unavailable` marker to projected navigation routes while keeping the existing accessible link name stable via an `aria-hidden` marker.
- `navigation_matrix.py` now validates the committed web projection exactly against the living ledger, so a ledger/status/reason/blocker change cannot silently drift from Portal presentation.
- `tests/ci/test_portal_surface_availability.py` independently reconstructs the projection from raw ledger rows and verifies the shell/notice contract.
- `surface-availability.spec.ts` proves a disconnected route (`/ai`) receives both navigation and direct-route warnings and a non-disconnected route (`/market/liquidations`) does not.

## Scope

Owned paths:

- `ai_platform/portal/web/lib/product-surface-availability.json`
- `ai_platform/portal/web/components/surface-availability-notice.tsx`
- `ai_platform/portal/web/components/app-shell.tsx`
- `tools/portal_audit/navigation_matrix.py`
- `tests/ci/test_portal_surface_availability.py`
- `ai_platform/portal/web/e2e/surface-availability.spec.ts`
- `docs/agents/tasks/active/FTAI-20260811-paper-g0-surface-availability.md`

Forbidden scope:

- implementation of any linked disconnected feature;
- changes to `tools/portal_audit/ledger/*` classifications merely to make this task pass;
- runtime isolation/Supervisor/Gateway paths owned by #1464/#1354 or future #1355 work;
- WickHunter/Liquid20 paths owned by #1450/#1396;
- credentials, protected deployment, real exchange execution, LIVE or live capital.

## Acceptance

- one committed web projection contains exactly the ledger surfaces whose overall status is `DISCONNECTED` or `MISSING`;
- the projection carries route, label, status, linked blocker/boundary and ledger reason;
- canonical navigation visibly labels those routes `Unavailable` without pretending their useful read-only evidence is complete and without changing accessible link names;
- direct navigation renders a visible warning that the capability is not connected end to end in the canonical product runtime;
- routes not classified `DISCONNECTED`/`MISSING` do not receive that warning;
- `navigation_matrix.py` and a focused CI test reject projection drift from the living ledger;
- a browser test proves both an unavailable route and a non-unavailable route in the real shell;
- no product capability, execution authority or LIVE path is added;
- exact-head CI, fresh independent audit and zero material review threads pass before merge.

## Coordination

- PR #1452 / PAPER G0 work item 6 is merged; its lifecycle closeout PR #1466 is also merged. Current trusted base is `develop@6577ae896ed5910f82f9e736fe4a007b6dc10e6e`.
- Branch synchronization used the current `develop` tree as the base and overlaid only the seven owned paths; compare is `behind_by: 0`, and no stale #1452 active record is reintroduced.
- #1396/#1450 and #1354/#1464 have separate active ownership and are not modified.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-11T09:24:00Z
head_before_checkpoint: 391b4209f9ce4855e49ccb039fe1a21b1bc0080b
branch: feat/paper-g0-surface-availability-20260811
status: validating
invocation_started_at: 2026-08-11T08:54:00Z
last_progress_at: 2026-08-11T09:24:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
stall_warnings: 0
proven:
  - living navigation ledger is CI-enforced status authority
  - 16 canonical surfaces are overall DISCONNECTED or MISSING
  - pre-change shell did not project those statuses
  - at least /ai can represent a disconnected producer as ordinary empty state
  - Strategy Catalog already has a local unavailable failure state, so central shell truth remains additive rather than replacing page-specific handling
  - branch is synchronized with develop@6577ae896ed5910f82f9e736fe4a007b6dc10e6e and final compare contains exactly seven owned paths
  - visible navigation markers preserve existing accessible link names
unknown:
  - fresh independent audit disposition
  - exact-head CI and browser acceptance result
conflicts: []
validation:
  - command: develop-to-branch compare after tree-overlay synchronization
    result: PASS
    evidence: behind_by=0; exactly seven intended changed paths; no #1452/#1466 lifecycle path drift
  - command: runtime/browser acceptance
    result: PENDING
    evidence: focused Playwright regression spec added; final routed CI pending
blockers: []
next_action: Open the single bounded delivery PR, request fresh Codex review, collect exact-head routed CI/browser evidence, and repair only evidence-backed material findings.
```
