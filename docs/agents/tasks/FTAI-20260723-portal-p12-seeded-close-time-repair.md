---
task_id: FTAI-20260723-portal-p12-seeded-close-time-repair
status: active
branch: test/portal-p12-seeded-close-time-repair-final-20260723
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "#220"
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

Because P12 foundation PR #216 was squash-merged, retargeting the provenance branch would reintroduce foundation history into the final diff. The final acceptance branch therefore replays only the two durable outputs from exact merge SHA `26c9c9e2ec41797c9fdc180cad7f89a7ad5f6b7c`: this evidence record and the regression test. PR #217 remains provenance for the seed/failure/repair commit history and is closed unmerged.

PR #220 is a temporary validation PR against `integration/p12-foundation-26c9-20260723`, whose base SHA is exactly `26c9c9e2ec41797c9fdc180cad7f89a7ad5f6b7c`. It exists only because the GitHub connector's `develop` ref is temporarily stale after the squash merge. PR #220 must be retargeted to `develop`, not merged into the integration branch, once the live `develop` ref visibly contains the P12 foundation.

## Non-negotiable boundaries

- The temporary defect never enters `develop`.
- Existing close-time safety assertions remain intact.
- No production deployment, secrets, live capital, external infrastructure or protected final holdout access.
- Simulated evidence is not real P11 Cloudflare acceptance evidence.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T18:35:00+02:00
head: f6f784c1150c7f524d83e11eaa0906b583fa4743
branch: test/portal-p12-seeded-close-time-repair-final-20260723
pr: "#220"
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
  - Temporary validation PR #220 reports base_sha 26c9c9e2ec41797c9fdc180cad7f89a7ad5f6b7c and exactly two changed files.
derived:
  - The seeded non-security defect was reproduced, diagnosed and minimally repaired without weakening a safety assertion or touching production paths.
  - PR #217 is evidence provenance, while PR #220 validates the exact two-file durable acceptance output until it can be retargeted to develop.
unknown:
  - When the GitHub connector's develop ref will reflect the already-confirmed squash merge #216.
conflicts: []
first_failure:
  marker: simulated-trade-did-not-close-after-opening
  evidence: Seeded PR #217 failed AI Platform CI 30021875591 and Portal Universal E2E backend scenario 30021875771 before repair.
rejected_hypotheses:
  - Weaken or delete the existing close-time assertion.
  - Merge the intentionally defective provenance branch.
  - Reintroduce squash-merged P12 foundation files into the final acceptance diff.
  - Merge PR #220 into the temporary integration base instead of retargeting it to develop.
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
  - command: final two-file validation PR #220
    result: PENDING
    evidence: PR #220 targets exact foundation merge SHA through the temporary integration base; required CI is pending before retargeting to develop.
blockers:
  - Final merge is blocked only until PR #220 can be retargeted to a develop ref that visibly includes foundation merge 26c9c9e2ec41797c9fdc180cad7f89a7ad5f6b7c.
next_action: Validate PR #220 on the exact foundation base, then retarget the same PR to develop once develop visibly includes 26c9c9e2ec41797c9fdc180cad7f89a7ad5f6b7c; verify the diff remains exactly two files and merge only after final required CI passes.
```
