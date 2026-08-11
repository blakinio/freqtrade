# FTAI-20260811 — PAPER G0 Product Surface Availability Truth

```yaml
task_id: FTAI-20260811-paper-g0-surface-availability
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: product_truth_guardrail
phase: implementation
status: active
priority: high
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: develop
trusted_base_sha: 816aac5018b785f750ab9eaffd5de9033f988999
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
- Other disconnected surfaces can look like normal empty product state. Example: `/ai` renders `No insights yet` and explanatory normal-flow copy even though its overall ledger status is `DISCONNECTED` because trusted intelligence/learning producers and model lifecycle workflows are not composed.
- `AppShell` currently renders all canonical navigation items identically and has no completeness/availability projection.

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
- canonical navigation labels those routes `Unavailable` without pretending their useful read-only evidence is complete;
- direct navigation renders a visible warning that the capability is not connected end to end in the canonical product runtime;
- routes not classified `DISCONNECTED`/`MISSING` do not receive that warning;
- `navigation_matrix.py` and a focused CI test reject projection drift from the living ledger;
- a browser test proves both an unavailable route and a non-unavailable route in the real shell;
- no product capability, execution authority or LIVE path is added;
- exact-head CI, fresh independent audit and zero material review threads pass before merge.

## Coordination

- PR #1452 / PAPER G0 work item 6 is merged at `develop@816aac5018b785f750ab9eaffd5de9033f988999`.
- Lifecycle-only closeout PR #1466 is disjoint and waiting only on external aggregate CI; this task does not touch its task-record paths.
- #1396/#1450 and #1354/#1464 have separate active ownership and are not modified.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T09:12:00Z
head: 816aac5018b785f750ab9eaffd5de9033f988999
branch: feat/paper-g0-surface-availability-20260811
status: implementation
invocation_started_at: 2026-08-11T08:54:00Z
last_progress_at: 2026-08-11T09:12:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
stall_warnings: 0
proven:
  - living navigation ledger is CI-enforced status authority
  - 16 canonical surfaces are overall DISCONNECTED or MISSING
  - current shell does not project those statuses
  - at least /ai can represent a disconnected producer as ordinary empty state
  - Strategy Catalog already has a local unavailable failure state, so central shell truth can remain additive rather than replacing page-specific failure handling
unknown:
  - exact final implementation head and CI/audit disposition
conflicts: []
blockers: []
next_action: Implement the ledger-synchronized web availability projection, central shell notice/navigation marker, focused drift test and browser proof without changing ledger classifications or downstream product functionality.
```
