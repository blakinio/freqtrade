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
delivery_pr: 1470
paper_gate: G0
paper_work_item: 7
live_capital_authorized: false
protected_production_deployment_authorized: false
repair_cycles_for_current_gate: 2
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
- `AppShell` adds a visible `Unavailable` marker to projected navigation routes while keeping the existing accessible link name stable; projected links also receive an `aria-describedby` relationship to a hidden `Capability unavailable` description so assistive technology receives the status before navigation.
- `navigation_matrix.py` validates the committed web projection exactly against the living ledger, so a ledger/status/reason/blocker change cannot silently drift from Portal presentation.
- `tests/ci/test_portal_surface_availability.py` independently reconstructs the projection from raw ledger rows and verifies the shell/notice/accessibility contract.
- `ai_platform/portal/web/e2e/specs/surface-availability.spec.ts` is inside the configured Playwright `testDir`, tagged `@critical` and `@regression`, and proves `/ai` receives navigation/direct-route warnings plus an accessible unavailable description while `/market/liquidations` does not.

## Scope

Owned paths:

- `ai_platform/portal/web/lib/product-surface-availability.json`
- `ai_platform/portal/web/components/surface-availability-notice.tsx`
- `ai_platform/portal/web/components/app-shell.tsx`
- `tools/portal_audit/navigation_matrix.py`
- `tests/ci/test_portal_surface_availability.py`
- `ai_platform/portal/web/e2e/specs/surface-availability.spec.ts`
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
- canonical navigation visibly labels those routes `Unavailable` without pretending their useful read-only evidence is complete;
- assistive technology receives `Capability unavailable` as an accessible description while established accessible link names remain stable;
- direct navigation renders a visible warning that the capability is not connected end to end in the canonical product runtime;
- routes not classified `DISCONNECTED`/`MISSING` do not receive that warning or accessible unavailable description;
- `navigation_matrix.py` and a focused CI test reject projection drift from the living ledger;
- the browser proof is inside the configured Playwright `testDir` and selected by ordinary PR `@critical` routing;
- no product capability, execution authority or LIVE path is added;
- exact-head CI, fresh independent audit and zero material review threads pass before merge.

## Coordination

- PR #1452 / PAPER G0 work item 6 and lifecycle closeout #1466 are merged. Trusted base is `develop@6577ae896ed5910f82f9e736fe4a007b6dc10e6e`.
- Branch synchronization overlaid only owned paths on the current develop tree; no stale #1452 active record is reintroduced.
- #1396/#1450 and #1354/#1464 have separate ownership and are not modified.

## Context checkpoint

```yaml
checkpoint_version: 4
updated_at: 2026-08-11T09:34:00Z
head_before_checkpoint: 6c19962d0b261e1f1d25d652e9ecdfaa0f5651b7
branch: feat/paper-g0-surface-availability-20260811
pr: 1470
status: validating
invocation_started_at: 2026-08-11T08:54:00Z
last_progress_at: 2026-08-11T09:34:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 2
stall_warnings: 0
proven:
  - living navigation ledger is CI-enforced status authority
  - 16 canonical surfaces are overall DISCONNECTED or MISSING
  - branch remains bounded to the seven logical owned paths
  - ordinary PR Portal Web CI executes the @critical subset
  - playwright.config.ts discovers tests only under ./e2e/specs
first_failure:
  marker: initial browser proof was outside configured Playwright testDir and only @regression, so it could remain green without executing
  evidence: Codex P1 discussion_r3756725179 plus playwright.config.ts testDir and portal-web/package routing
repair_cycle_1:
  head: ff5bbdb320c802d47b188ed289ed4ab5801303ab
  result: INCOMPLETE
  evidence: added @critical tag, but stale-head Codex proved the file itself remained outside testDir
repair_cycle_2:
  result: APPLIED
  evidence:
    - moved browser proof to ai_platform/portal/web/e2e/specs/surface-availability.spec.ts
    - preserved @critical and @regression tags
    - added aria-describedby accessible status relation while preserving link name
    - added browser assertion for accessible description and focused static accessibility contract checks
  addressed_findings:
    - Codex P1 discussion_r3756725179
    - Codex P2 discussion_r3756725187
unknown:
  - fresh independent audit disposition for final successor head
  - exact-head CI/browser result for final successor head
conflicts: []
validation:
  - command: develop-to-branch compare after synchronization
    result: PASS
    evidence: behind_by=0 before repair; no conflicting ownership paths
  - command: browser discovery/routing audit
    result: PASS_AFTER_REPAIR_CYCLE_2
    evidence: spec now resides below configured testDir and carries @critical
  - command: assistive navigation-status audit
    result: PASS_AFTER_REPAIR_CYCLE_2
    evidence: visible marker is paired with aria-describedby -> hidden Capability unavailable description
  - command: exact-head runtime/browser acceptance
    result: PENDING
blockers: []
next_action: Resolve final successor head, update PR metadata, reply/resolve remediated review threads, request fresh Codex audit, and accept only final-head CI/browser evidence.
```
