---
task_id: FTAI-20260723-portal-p12-seeded-close-time-repair
status: active
branch: test/portal-p12-seeded-close-time-repair-final-20260723
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: null
owned_paths:
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
  - current develop and merged P12 foundation
  - seeded provenance PR #217
optional_reads: []
---

# P12 Seeded Non-Security Repair Acceptance — Simulator Close Time

## Goal

Prove the simulation-first P12 repair loop on a deliberately seeded, non-security deterministic simulator defect: preserve first reproducible failure evidence, diagnose it from P10-compatible evidence, add regression coverage before repair, restore minimal correct behavior, and land durable regression/evidence without carrying the temporary defect into `develop`.

## Evidence identity

- scenario_id: `profitable-btc-001`
- correlation_id: `11111111-1111-4111-8111-111111111111`
- stage: `scenario_assertion`
- reason_code: `simulated trade did not close after opening`
- evidence_kind: `simulated`
- classification: `product_defect`
- likely_layer: `simulator`
- confidence: `high`
- reproduced: `true`

## Acceptance result

The isolated provenance branch in draft PR #217 intentionally changed `TradeOutcome.closed_at` from the exit tick to the entry tick. A direct regression test was committed before repair. The seeded head failed both full AI Platform tests and the deterministic Universal E2E backend scenario. The minimal repair restored only the exit-tick timestamp and preserved the existing close-time assertion plus the new regression test.

Because P12 foundation PR #216 was squash-merged, retargeting the provenance branch would reintroduce foundation history into the final diff. The final acceptance branch therefore replays only the two durable outputs from exact merge SHA `26c9c9e2ec41797c9fdc180cad7f89a7ad5f6b7c`: this evidence record and the regression test. PR #217 remains provenance for the seed/failure/repair commit history and must not be merged.

## Non-negotiable boundaries

- The temporary defect never enters `develop`.
- Existing close-time safety assertions remain intact.
- No production deployment, secrets, live capital, external infrastructure or protected final holdout access.
- Simulated evidence is not real P11 Cloudflare acceptance evidence.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T18:25:00+02:00
head: 46996ecc7a0daddf81ec54bd62de8a1cbbea4588
branch: test/portal-p12-seeded-close-time-repair-final-20260723
pr: pending
status: validating
context_routes:
  - docs/ai_platform/portal/AUTONOMOUS_REPAIR_SIMULATION_FIRST.md
  - docs/ai_platform/portal/DETERMINISTIC_SIMULATOR_E2E.md
  - ai_platform/portal/quality_agent/service.py
owned_paths:
  - tests/ai_platform/portal/simulator/test_seeded_close_time_regression.py
  - docs/agents/tasks/FTAI-20260723-portal-p12-seeded-close-time-repair.md
proven:
  - P12 foundation PR #216 merged as 26c9c9e2ec41797c9fdc180cad7f89a7ad5f6b7c after Portal P12 Simulation-First Validation 30021450688, AI Platform CI 30021449136, zizmor 30021449172 and Freqtrade CI 30021449103 passed.
  - Provenance PR #217 seeded the defect in commit 2c3b0245f855ab74eab73defa659546f67cca478.
  - Regression commit 05b002fc715d926a481ea29f2a8debd08cb809c8 added close-time regression coverage before repair.
  - Seeded AI Platform CI 30021875591 failed during tests.
  - Seeded Portal Universal E2E 30021875771 failed in the deterministic backend scenario.
  - The seeded equality closed_at == opened_at satisfies the existing UniversalScenarioRunner failure condition and yields reason `simulated trade did not close after opening`.
  - P12 foundation deterministically maps that reason to product_defect, simulator, high confidence.
  - Repair commit 5343139caeb223858454df8b68c622753b98dabc restored only closed_at = manifest.exit_tick.occurred_at.
  - Repaired Portal Universal E2E 30022275787 passed.
  - Repaired AI Platform CI 30022275563 passed after the regression-test signature was formatted in commit 98bb20e08f30fcabe52c5bf0e74c7af076397032.
  - Final branch starts from exact P12 foundation merge SHA 26c9c9e2ec41797c9fdc180cad7f89a7ad5f6b7c and contains no simulator product-code modification.
derived:
  - The seeded non-security defect was reproduced, diagnosed and minimally repaired without weakening a safety assertion or touching production paths.
  - PR #217 is evidence provenance, while this exact-merge-SHA branch is the only merge candidate for durable acceptance artifacts.
unknown: []
conflicts: []
first_failure:
  marker: simulated-trade-did-not-close-after-opening
  evidence: Seeded PR #217 failed AI Platform CI 30021875591 and Portal Universal E2E backend scenario 30021875771 before repair.
rejected_hypotheses:
  - Weaken or delete the existing close-time assertion.
  - Merge the intentionally defective provenance branch.
  - Reintroduce squash-merged P12 foundation files into the final acceptance diff.
  - Treat simulated evidence as real P11 staging acceptance.
changed_paths:
  - tests/ai_platform/portal/simulator/test_seeded_close_time_regression.py
  - docs/agents/tasks/FTAI-20260723-portal-p12-seeded-close-time-repair.md
validation:
  - command: seeded AI Platform CI 30021875591
    result: FAIL_EXPECTED
    evidence: Intentionally seeded head failed full AI Platform tests before repair.
  - command: seeded Portal Universal E2E 30021875771
    result: FAIL_EXPECTED
    evidence: Intentionally seeded deterministic backend scenario failed before repair.
  - command: repaired AI Platform CI 30022275563
    result: PASS
    evidence: Full AI Platform tests, Ruff, Ruff format and remaining validation passed after repair and regression formatting.
  - command: repaired Portal Universal E2E 30022275787
    result: PASS
    evidence: Deterministic backend and Chromium journey passed after repair.
  - command: clean final acceptance validation
    result: NOT_RUN
    evidence: Final clean PR has not yet been opened.
blockers: []
next_action: Open the exact-merge-SHA final acceptance PR against develop, validate required CI, merge only the durable regression/evidence outputs, then close provenance PR #217 unmerged.
```
