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
repair_cycles_for_current_gate: 5
repair_budget_exhausted: true
repair_budget_exception_authorized: true
owner_continuous_repair_authorization: true
```

## Objective

Close PAPER G0 work item 7 without implementing later-gate product functionality: every canonical left-navigation surface whose living exact-head completeness ledger classifies overall as `DISCONNECTED` or `MISSING` must be explicitly presented as unavailable in the Portal shell and on direct navigation. The web projection must be CI-checked against the canonical ledger so status cannot drift silently.

## Implementation

- `ai_platform/portal/web/lib/product-surface-availability.json` projects exactly the living-ledger `DISCONNECTED`/`MISSING` rows, preserving route, label, status, linked issues/boundary and canonical reason.
- `SurfaceAvailabilityNotice` shows a visible shell-level warning on projected direct routes without suppressing useful bounded read-only evidence. It uses `role="note"` with an accessible label so it does not collide with application success/risk `role="status"` messages.
- `AppShell` shows `Unavailable` while preserving the established accessible link name; projected links expose `Capability unavailable` through `aria-describedby`.
- `navigation_matrix.py` exact-compares the committed web projection with the living ledger so status/reason/blocker drift fails closed.
- `tests/ci/test_portal_surface_availability.py` independently reconstructs the projection and verifies shell/notice/accessibility contracts, including the non-status role boundary.
- `ai_platform/portal/web/e2e/specs/surface-availability.spec.ts` is inside configured Playwright `testDir`, tagged `@critical` and `@regression`, and proves projected `/ai` versus non-projected `/market/liquidations` behavior plus the note semantics.

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
- availability notice semantics do not create an additional generic application `status` role;
- non-projected routes receive neither warning nor unavailable accessible description;
- ledger projection drift fails CI;
- focused Playwright proof is discovered and selected by ordinary PR critical routing;
- existing bot-finalization and terminal-risk browser journeys remain unambiguous and green;
- no product capability or execution/LIVE authority is added;
- final exact-head CI, fresh independent audit and review hygiene pass before merge;
- task remains active until delivery merge is real.

## Coordination

- #1452 and closeout #1466 are merged; trusted base is `develop@6577ae896ed5910f82f9e736fe4a007b6dc10e6e`.
- branch remains bounded to the seven logical owned paths and does not touch #1396/#1450 or #1354/#1464 ownership.
- repair cycle 4 was explicitly owner-authorized after the standard three-cycle budget.
- on 2026-08-11 the owner granted continuous authorization to continue further bounded PAPER-only repairs without asking again; this does not authorize LIVE, production, secrets, protected deployment or real capital.

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
  result: PASS_AT_REVIEW
  authorization: explicit owner continuation after exhausted standard repair budget
  first_failure:
    review_thread: PRRT_kwDOTdDTU86YLbnu
    severity: P1
    marker: context checkpoint violated shared checkpoint contract and could not be consumed by checkpoint.py/resume.py
  remediation:
    first_commit: 1c66dba4026f42b590f105f1edcc5d9280a9ad16
    final_head: 79180b53a7c2330364e2a951d0ec48df24315924
    change: re-encoded Context checkpoint as shared checkpoint contract version 1 with all required fields and supported validation results
  audit:
    reviewed_head: 79180b53a7c2330364e2a951d0ec48df24315924
    comment_id: 5256852073
    result: PASS
repair_cycle_5:
  result: APPLIED
  authorization: continuous owner authorization for bounded PAPER-only repairs
  first_failure:
    workflow: Risk-aware component CI
    run_id: 31519556246
    job_id: 93873243420
    marker: SurfaceAvailabilityNotice role=status made existing getByRole(status) locators ambiguous in create-bot and terminal-risk journeys
    evidence: 70 browser tests passed and 2 failed deterministically because each failing page contained the new availability status plus the intended application status
  remediation:
    component_commit: 92dac9ae88c867af2a96dbe81553cdb09f52a561
    browser_test_commit: e234f69701b0fcbb0227486c89717a700e0ec26d
    ci_guard_commit: 59f59831862cda66624b8930ffce226019a2ae33
    change: changed availability notice to role=note with an accessible label and added browser/static regression proof; no ledger, capability or LIVE behavior changed
repair_budget_exhausted: true
repair_budget_exception_authorized: true
owner_continuous_repair_authorization: true
```

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T17:56:00Z
head: 59f59831862cda66624b8930ffce226019a2ae33
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
  - browser proof is under configured Playwright testDir and carries critical routing
  - unavailable navigation status is exposed visually and through an accessible description
  - cycle-4 checkpoint contract finding is resolved and exact-head Codex review passed on 79180b53
  - cycle-5 browser failure was caused by duplicate generic status roles introduced by the availability notice
  - owner authorized continuing bounded PAPER-only repair cycles without further approval
derived:
  - role=note preserves an accessible direct-route advisory while avoiding collision with success/risk status messages
unknown:
  - exact-head CI result after cycle-5 semantic-role repair
  - fresh exact-head Codex disposition after cycle-5 semantic-role repair
conflicts: []
first_failure:
  marker: exact-head full Chromium regression found duplicate role=status semantics on projected unavailable routes
  evidence: Risk-aware run 31519556246 job 93873243420 failed create-bot.spec.ts and terminal/risk-gate.spec.ts because getByRole(status) resolved to both SurfaceAvailabilityNotice and the intended application result; surface-availability tests themselves passed
rejected_hypotheses:
  - surface availability projection is wrong; focused projection tests passed and failure was selector ambiguity
  - browser failure is infrastructure flake; both affected tests failed on retry with the same duplicate-role diagnostic
changed_paths:
  - ai_platform/portal/web/components/surface-availability-notice.tsx
  - ai_platform/portal/web/e2e/specs/surface-availability.spec.ts
  - tests/ci/test_portal_surface_availability.py
  - docs/agents/tasks/active/FTAI-20260811-paper-g0-surface-availability.md
validation:
  - command: Risk-aware component CI run 31519556246 job 93873243420
    result: FAIL
    evidence: predecessor exact head produced 70 PASS and 2 deterministic duplicate-role failures; this is the cycle-5 first failure being repaired
  - command: python tools/agents/checkpoint.py docs/agents/tasks/active/FTAI-20260811-paper-g0-surface-availability.md --require-checkpoint
    result: NOT_RUN
    evidence: cycle-5 successor must be validated by exact-head repository CI
  - command: npm run test:e2e
    result: NOT_RUN
    evidence: cycle-5 successor must prove both focused availability tests and existing full Chromium journeys on exact head
  - command: Codex exact-head review
    result: NOT_RUN
    evidence: fresh independent audit must target the cycle-5 successor head before merge
blockers: []
next_action: Freeze the cycle-5 successor head, obtain fresh exact-head Codex review and all required CI including full Portal Chromium regression, then merge PR #1470 only if every required gate is terminally green; after merge archive the task and continue the next READY PAPER gate.
```
