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
repair_cycles_for_current_gate: 4
repair_budget_exhausted: true
repair_budget_exception_authorized: true
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
- branch remains bounded to seven logical owned paths and does not touch #1396/#1450 or #1354/#1464 ownership.
- the owner explicitly authorized repair cycle 4 on 2026-08-11 after the exhausted three-cycle budget, limited to restoring the checkpoint governance contract and its required revalidation.

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
repair_cycle_4:
  result: APPLIED
  authorization: explicit owner continuation after exhausted standard repair budget
  first_failure:
    review_thread: PRRT_kwDOTdDTU86YLbnu
    severity: P1
    marker: context checkpoint violated shared checkpoint contract and could not be consumed by checkpoint.py/resume.py
  remediation:
    change: re-encoded Context checkpoint as shared checkpoint contract version 1 with all required fields and supported validation results
repair_budget_exhausted: true
repair_budget_exception_authorized: true
```

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T17:45:00Z
head: fc908158053fa8289829e8f0eaa9537a1ccd8e81
branch: feat/paper-g0-surface-availability-20260811
pr: 1470
status: validating
context_routes:
  - docs/agents/GOVERNANCE_CONTRACT.json
  - tools/agents/checkpoint.py
  - tools/agents/resume.py
  - docs/agents/PROMPTING_HANDOVER.md
owned_paths:
  - ai_platform/portal/web/lib/product-surface-availability.json
  - ai_platform/portal/web/components/surface-availability-notice.tsx
  - ai_platform/portal/web/components/app-shell.tsx
  - tools/portal_audit/navigation_matrix.py
  - tests/ci/test_portal_surface_availability.py
  - ai_platform/portal/web/e2e/specs/surface-availability.spec.ts
  - docs/agents/tasks/active/FTAI-20260811-paper-g0-surface-availability.md
proven:
  - living navigation ledger is the CI-enforced status authority for product-surface completeness
  - 16 canonical surfaces are classified overall DISCONNECTED or MISSING
  - delivery diff is bounded to seven owned paths
  - browser proof is under configured Playwright testDir and carries critical routing
  - unavailable navigation status is exposed visually and through an accessible description
  - all pre-cycle-4 material review threads were resolved
  - owner explicitly authorized repair cycle 4 after the standard repair budget was exhausted
derived:
  - cycle-4 mutation is governance-only and does not change product or LIVE execution behavior
unknown:
  - exact-head CI result after cycle-4 checkpoint repair
  - fresh exact-head Codex disposition after cycle-4 checkpoint repair
conflicts: []
first_failure:
  marker: final-head Codex P1 found the Context checkpoint was incompatible with the shared checkpoint contract
  evidence: review thread PRRT_kwDOTdDTU86YLbnu reported wrong checkpoint_version, missing required fields and unsupported validation encoding on fc908158053fa8289829e8f0eaa9537a1ccd8e81
rejected_hypotheses:
  - product logic requires another repair; cycle-4 finding is confined to governance checkpoint encoding
changed_paths:
  - docs/agents/tasks/active/FTAI-20260811-paper-g0-surface-availability.md
validation:
  - command: python tools/agents/checkpoint.py docs/agents/tasks/active/FTAI-20260811-paper-g0-surface-availability.md --require-checkpoint
    result: NOT_RUN
    evidence: cycle-4 content was encoded directly from docs/agents/GOVERNANCE_CONTRACT.json and tools/agents/checkpoint.py; exact-head CI must execute the repository validator
  - command: python tools/agents/resume.py docs/agents/tasks/active/FTAI-20260811-paper-g0-surface-availability.md
    result: NOT_RUN
    evidence: continuation consumer must be verified on the exact cycle-4 head before merge
  - command: Codex exact-head review
    result: NOT_RUN
    evidence: fresh review must target the successor commit created by this checkpoint repair
blockers: []
next_action: Run the repository checkpoint and resume validation through exact-head CI, obtain a fresh Codex review of the cycle-4 successor head, resolve the remediated checkpoint thread, then merge PR #1470 only if every required exact-head gate is terminally green.
```
