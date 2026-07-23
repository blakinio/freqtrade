---
task_id: FTAI-20260723-portal-p12-seeded-close-time-repair
status: active
branch: agent/ftai-20260723-portal-p12-seeded-close-time-repair-11111111
base_branch: feat/portal-p12-simulation-first-repair-clean-20260723
created: 2026-07-23
updated: 2026-07-23
related_pr: null
owned_paths:
  - ai_platform/portal/simulator/exchange.py
  - tests/ai_platform/portal/simulator/test_seeded_close_time_regression.py
  - docs/agents/tasks/FTAI-20260723-portal-p12-seeded-close-time-repair.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/AUTONOMOUS_REPAIR_SIMULATION_FIRST.md
  - docs/ai_platform/portal/DETERMINISTIC_SIMULATOR_E2E.md
  - ai_platform/portal/quality_agent/service.py
  - ai_platform/portal/simulator/exchange.py
search_first:
  - current develop and P12 foundation PR state
  - overlapping simulator tasks or PRs
optional_reads: []
---

# P12 Seeded Non-Security Repair Acceptance — Simulator Close Time

## Goal

Prove the simulation-first P12 repair loop on a deliberately seeded, non-security deterministic simulator defect: capture the first reproducible failure, diagnose it from P10-compatible evidence, add a regression test before the repair, restore the minimal correct behavior, and produce a passing isolated PR with attributable evidence.

## Seeded defect

Temporarily set the simulated `TradeOutcome.closed_at` timestamp to the entry tick rather than the declared exit tick. This is confined to the isolated exercise branch and must never merge in the defective state.

Expected deterministic first failure:

`simulated trade did not close after opening`

P12 evidence identity:

- scenario_id: `profitable-btc-001`
- correlation_id: `11111111-1111-4111-8111-111111111111`
- stage: `scenario_assertion`
- reason_code: `simulated trade did not close after opening`
- evidence_kind: `simulated`

## Non-negotiable boundaries

- The defect is seeded only on this isolated branch.
- The repair must not weaken or remove the existing close-time safety assertion.
- A dedicated regression test must be present before the product repair is applied.
- The final branch must restore `closed_at` to the manifest exit tick.
- No production deployment, secrets, live capital, external infrastructure or protected final holdout access.
- The branch is stacked on PR #216 only until the P12 foundation merges; it must be rebased/retargeted to current `develop` before final merge.

## Acceptance criteria

1. Seed commit creates the deterministic close-time defect on the isolated branch only.
2. CI or targeted deterministic validation records the first reproducible failure.
3. P12 diagnosis classifies the known reason as a high-confidence simulator product defect.
4. A direct regression test asserts that `closed_at == manifest.exit_tick.occurred_at` and `closed_at > opened_at`.
5. Minimal repair restores exactly the correct close timestamp without weakening assertions.
6. Targeted simulator/P12 tests and required repository CI pass after repair.
7. PR history and this checkpoint preserve seed, failure, diagnosis, regression and repair provenance.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T17:55:00+02:00
head: 65b0cb7d90b0e2298a2c0731a04807fd26749256
branch: agent/ftai-20260723-portal-p12-seeded-close-time-repair-11111111
pr: pending
status: seeding
context_routes:
  - docs/ai_platform/portal/AUTONOMOUS_REPAIR_SIMULATION_FIRST.md
  - docs/ai_platform/portal/DETERMINISTIC_SIMULATOR_E2E.md
  - ai_platform/portal/quality_agent/service.py
owned_paths:
  - ai_platform/portal/simulator/exchange.py
  - tests/ai_platform/portal/simulator/test_seeded_close_time_regression.py
  - docs/agents/tasks/FTAI-20260723-portal-p12-seeded-close-time-repair.md
proven:
  - PR #216 is the current P12 foundation merge candidate and this branch is stacked on its head only to avoid waiting on the unrelated long Freqtrade matrix.
  - The current simulator correctly uses manifest.exit_tick.occurred_at for TradeOutcome.closed_at before seeding.
  - P12 foundation maps reason_code `simulated trade did not close after opening` to a high-confidence product_defect in layer `simulator`.
derived:
  - Setting closed_at to the entry tick will deterministically trigger the existing UniversalScenarioRunner close-time assertion without touching security or real execution paths.
unknown: []
conflicts: []
first_failure:
  marker: not-yet-seeded
  evidence: The acceptance exercise has been declared but the isolated defect has not yet been committed.
rejected_hypotheses:
  - Weaken or delete the runner close-time assertion to make the exercise pass.
  - Seed the defect on develop or in the P12 foundation PR.
  - Use real staging or production execution as repair evidence.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-portal-p12-seeded-close-time-repair.md
validation: []
blockers:
  - Final merge is blocked until PR #216 is merged and this exercise is retargeted to current develop.
next_action: Seed the one-line close-time defect on the isolated branch, add the direct regression test while the defect remains, open a stacked draft PR and capture the deterministic failing evidence before applying the minimal repair.
```
