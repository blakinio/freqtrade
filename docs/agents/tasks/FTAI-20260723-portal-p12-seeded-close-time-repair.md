---
task_id: FTAI-20260723-portal-p12-seeded-close-time-repair
status: active
branch: agent/ftai-20260723-portal-p12-seeded-close-time-repair-11111111
base_branch: feat/portal-p12-simulation-first-repair-clean-20260723
created: 2026-07-23
updated: 2026-07-23
related_pr: "#217"
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

Deterministic first failure:

`simulated trade did not close after opening`

P12 evidence identity:

- scenario_id: `profitable-btc-001`
- correlation_id: `11111111-1111-4111-8111-111111111111`
- stage: `scenario_assertion`
- reason_code: `simulated trade did not close after opening`
- evidence_kind: `simulated`

Diagnosis:

- classification: `product_defect`
- likely_layer: `simulator`
- confidence: `high`
- reproduced: `true`

## Non-negotiable boundaries

- The defect is seeded only on this isolated branch.
- The repair must not weaken or remove the existing close-time safety assertion.
- A dedicated regression test must be present before the product repair is applied.
- The final branch must restore `closed_at` to the manifest exit tick.
- No production deployment, secrets, live capital, external infrastructure or protected final holdout access.
- The branch is stacked on PR #216 only until the P12 foundation merges; it must be retargeted to current `develop` before final merge.

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
updated_at: 2026-07-23T18:05:00+02:00
head: 05b002fc715d926a481ea29f2a8debd08cb809c8
branch: agent/ftai-20260723-portal-p12-seeded-close-time-repair-11111111
pr: "#217"
status: repairing
context_routes:
  - docs/ai_platform/portal/AUTONOMOUS_REPAIR_SIMULATION_FIRST.md
  - docs/ai_platform/portal/DETERMINISTIC_SIMULATOR_E2E.md
  - ai_platform/portal/quality_agent/service.py
owned_paths:
  - ai_platform/portal/simulator/exchange.py
  - tests/ai_platform/portal/simulator/test_seeded_close_time_regression.py
  - docs/agents/tasks/FTAI-20260723-portal-p12-seeded-close-time-repair.md
proven:
  - PR #216 is the current P12 foundation merge candidate and this branch is stacked on its head until that foundation merges.
  - Seed commit 2c3b0245f855ab74eab73defa659546f67cca478 changed only the simulated TradeOutcome.closed_at value from the exit tick to the entry tick.
  - Regression commit 05b002fc715d926a481ea29f2a8debd08cb809c8 added a direct close-time regression test before the repair.
  - Draft PR #217 preserves the intentionally defective pre-repair state in commit history.
  - AI Platform CI run 30021875591 failed at the full AI Platform test step on the seeded head.
  - Portal Universal E2E run 30021875771 backend-scenario failed at the deterministic universal scenario step on the same seeded head.
  - With the seeded implementation, closed_at equals opened_at; UniversalScenarioRunner deterministically raises `simulated trade did not close after opening` when outcome.closed_at <= outcome.opened_at.
  - P12 foundation maps reason_code `simulated trade did not close after opening` to classification product_defect, likely_layer simulator and high confidence.
derived:
  - The failure is reproducible and caused by the isolated one-line simulator seed rather than external infrastructure or test-environment noise.
  - The minimal valid repair is to restore closed_at to manifest.exit_tick.occurred_at while preserving the existing runner assertion and the new regression test.
unknown: []
conflicts: []
first_failure:
  marker: simulated-trade-did-not-close-after-opening
  evidence: Seeded head 05b002fc715d926a481ea29f2a8debd08cb809c8 caused AI Platform CI 30021875591 to fail in tests and Portal Universal E2E backend-scenario 30021875771 to fail in the deterministic scenario; the seeded equality closed_at == opened_at satisfies the existing runner failure condition exactly.
rejected_hypotheses:
  - Weaken or delete the runner close-time assertion to make the exercise pass.
  - Remove the new regression test after reproducing the defect.
  - Seed or repair production execution code outside the deterministic simulator.
  - Use real staging or production execution as repair evidence.
changed_paths:
  - ai_platform/portal/simulator/exchange.py
  - tests/ai_platform/portal/simulator/test_seeded_close_time_regression.py
  - docs/agents/tasks/FTAI-20260723-portal-p12-seeded-close-time-repair.md
validation:
  - command: AI Platform CI 30021875591
    result: FAIL_EXPECTED
    evidence: Full AI Platform tests failed on the intentionally seeded head before repair.
  - command: Portal Universal E2E backend-scenario 30021875771
    result: FAIL_EXPECTED
    evidence: Deterministic universal scenario failed on the intentionally seeded head before repair.
blockers:
  - Final merge is blocked until PR #216 is merged and this exercise is retargeted to current develop.
next_action: Restore only TradeOutcome.closed_at to manifest.exit_tick.occurred_at, retain the regression test and safety assertion, then validate the repaired draft PR before retargeting it to develop after PR #216 merges.
```
