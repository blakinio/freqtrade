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
repair_cycles_for_current_gate: 3
repair_budget_exhausted: true
```

## Objective

Close PAPER G0 work item 7 without implementing later-gate product functionality: every canonical left-navigation surface whose living exact-head completeness ledger classifies overall as `DISCONNECTED` or `MISSING` must be explicitly presented as unavailable in the Portal shell and on direct navigation. The web projection must be CI-checked against the canonical ledger so status cannot drift silently.

## Implementation

- `ai_platform/portal/web/lib/product-surface-availability.json` projects exactly the living-ledger `DISCONNECTED`/`MISSING` rows, preserving route, label, status, linked issues/boundary and canonical reason.
- `SurfaceAvailabilityNotice` shows a visible shell-level warning on projected direct routes without suppressing useful bounded read-only evidence.
- `AppShell` shows `Unavailable` while preserving the established accessible link name; projected links expose `Capability unavailable` through `aria-describedby`.
- `navigation_matrix.py` exact-compares the committed web projection with the living ledger so status/reason/blocker drift fails closed.
- `tests/ci/test_portal_surface_availability.py` independently reconstructs the projection and verifies shell/notice/accessibility contracts.
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
- non-projected routes receive neither warning nor unavailable accessible description;
- ledger projection drift fails CI;
- focused Playwright proof is discovered and selected by ordinary PR critical routing;
- no product capability or execution/LIVE authority is added;
- final exact-head CI, fresh independent audit and review hygiene pass before merge;
- task remains active until delivery merge is real.

## Coordination

- #1452 and closeout #1466 are merged; trusted base is `develop@6577ae896ed5910f82f9e736fe4a007b6dc10e6e`.
- branch remains `behind_by: 0` before this final formatting repair and bounded to seven logical owned paths.
- #1396/#1450 and #1354/#1464 are untouched.

## Repair history

```yaml
repair_cycle_1:
  result: INCOMPLETE
  evidence: added @critical, but the browser spec remained outside configured Playwright testDir
repair_cycle_2:
  result: PASS_AT_REVIEW
  evidence:
    - moved proof to ai_platform/portal/web/e2e/specs/surface-availability.spec.ts
    - kept @critical and @regression
    - added aria-describedby accessible unavailable description
    - resolved Codex P1/P2 threads
  audit:
    reviewed_head: bbbbbf606ca6fcb62d2533190fb7f84959286182
    comment_id: 5251459936
    result: PASS
    note: became stale after repair cycle 3 formatting commit
repair_cycle_3:
  result: APPLIED
  first_failure:
    workflow: Freqtrade CI
    run_id: 31478064443
    job_id: 93736368185
    hook: ruff-format
    marker: tests/ci/test_portal_surface_availability.py required one deterministic quote-style reformat
  remediation:
    commit: 667ff0d352c46bb67d8478bd130a64a906a5a56b
    change: applied exactly the ruff-format diff emitted by the failing hook; no semantic product/test behavior changed
repair_budget_exhausted: true
```

## Context checkpoint

```yaml
checkpoint_version: 5
updated_at: 2026-08-11T09:38:00Z
head_before_checkpoint: 667ff0d352c46bb67d8478bd130a64a906a5a56b
branch: feat/paper-g0-surface-availability-20260811
pr: 1470
status: validating
invocation_started_at: 2026-08-11T08:54:00Z
last_progress_at: 2026-08-11T09:38:00Z
repair_cycles_for_current_gate: 3
repair_budget_exhausted: true
proven:
  - living ledger is the CI-enforced status authority
  - 16 canonical surfaces are DISCONNECTED or MISSING
  - final logical diff remains seven owned paths
  - browser proof is discoverable and critical-routed
  - accessible unavailable description is present
  - Codex on semantic repair head bbbbbf606c found no major issues
unknown:
  - fresh audit disposition for successor exact head containing cycle-3 formatting/checkpoint
  - exact-head CI/browser result for successor exact head
conflicts: []
validation:
  - result: PASS
    evidence: all prior material Codex threads resolved after cycle 2
  - result: FAIL_THEN_REPAIRED
    evidence: Freqtrade CI 31478064443 / job 93736368185 failed only because ruff-format changed one quote style; emitted diff applied exactly
blockers: []
next_action: Freeze the successor head. Request one fresh exact-head Codex audit and collect successor-head CI. Because the three-cycle repair budget is exhausted, any new material code/test failure is a terminal blocker requiring owner-authorized fresh isolation; do not perform a fourth repair cycle.
```
