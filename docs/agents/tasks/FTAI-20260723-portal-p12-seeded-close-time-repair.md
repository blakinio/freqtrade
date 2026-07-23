---
task_id: FTAI-20260723-portal-p12-seeded-close-time-repair
status: done
branch: develop
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "#222"
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
  - current develop and P12 foundation state
  - seeded provenance PR #217
optional_reads: []
---

# P12 Seeded Non-Security Repair Acceptance — Simulator Close Time

## Goal

Prove the simulation-first P12 repair loop on a deliberately seeded, non-security deterministic simulator defect and land only durable regression/evidence outputs after the temporary defect is repaired.

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

Closed provenance PR #217 intentionally changed `TradeOutcome.closed_at` from the exit tick to the entry tick. A direct regression test was committed before repair. The seeded head failed both full AI Platform tests and the deterministic Universal E2E backend scenario. The minimal repair restored only the exit-tick timestamp and preserved the existing close-time assertion plus the new regression test.

P12 foundation recovery PR #221 restored the bounded P12 foundation to live `develop` and squash-merged as `4f4389c103eb51de2a63f368815b6dea2d38546d`. Final clean acceptance PR #222 contained exactly the durable regression test and this evidence record, passed all required final-head CI, and squash-merged as `1e724be35ce856d93b590415b9bb3860634d8993`.

## Non-negotiable boundaries

- The temporary defect never entered `develop`.
- Existing close-time safety assertions remain intact.
- No production deployment, secrets, live capital, external infrastructure or protected final holdout access.
- Simulated evidence is not real P11 Cloudflare acceptance evidence.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T19:15:00+02:00
head: 1e724be35ce856d93b590415b9bb3860634d8993
branch: develop
pr: "#222"
status: ready
context_routes:
  - docs/ai_platform/portal/AUTONOMOUS_REPAIR_SIMULATION_FIRST.md
  - docs/ai_platform/portal/DETERMINISTIC_SIMULATOR_E2E.md
  - ai_platform/portal/quality_agent/service.py
owned_paths:
  - tests/ai_platform/portal/simulator/test_seeded_close_time_regression.py
  - docs/agents/tasks/FTAI-20260723-portal-p12-seeded-close-time-repair.md
proven:
  - P12 foundation recovery PR #221 squash-merged to live develop as 4f4389c103eb51de2a63f368815b6dea2d38546d after Portal P12 Simulation-First Validation 30024638442, AI Platform CI 30024638754, zizmor 30024638500 and Freqtrade CI 30024638000 passed.
  - Provenance PR #217 seeded the defect in commit 2c3b0245f855ab74eab73defa659546f67cca478 and is closed unmerged.
  - Regression commit 05b002fc715d926a481ea29f2a8debd08cb809c8 added close-time regression coverage before repair.
  - Seeded AI Platform CI 30021875591 and seeded Portal Universal E2E 30021875771 failed as expected before repair.
  - P12 foundation maps reason `simulated trade did not close after opening` to product_defect, simulator and high confidence.
  - Repair commit 5343139caeb223858454df8b68c622753b98dabc restored only closed_at = manifest.exit_tick.occurred_at.
  - Repaired AI Platform CI 30022275563 and Portal Universal E2E 30022275787 passed.
  - Final clean PR #222 had live develop base 4f4389c103eb51de2a63f368815b6dea2d38546d and exactly two changed files.
  - PR #222 passed AI Platform CI 30025621176, Portal Universal E2E 30025621171, zizmor 30025621161 and Freqtrade CI 30025621399.
  - PR #222 squash-merged as 1e724be35ce856d93b590415b9bb3860634d8993.
derived:
  - The seeded non-security defect was reproduced, diagnosed and minimally repaired without weakening a safety assertion or touching production paths.
  - P12 seeded-repair acceptance is complete and only durable regression/evidence outputs entered develop.
unknown: []
conflicts: []
first_failure:
  marker: simulated-trade-did-not-close-after-opening
  evidence: Seeded PR #217 failed AI Platform CI 30021875591 and Portal Universal E2E backend scenario 30021875771 before repair.
rejected_hypotheses:
  - Weaken or delete the existing close-time assertion.
  - Merge the intentionally defective provenance branch.
  - Reintroduce P12 foundation files through divergent squash ancestry.
  - Treat simulated evidence as real P11 staging acceptance.
changed_paths:
  - tests/ai_platform/portal/simulator/test_seeded_close_time_regression.py
  - docs/agents/tasks/FTAI-20260723-portal-p12-seeded-close-time-repair.md
validation:
  - command: seeded AI Platform CI 30021875591
    result: FAIL
    evidence: Intentionally seeded head failed full AI Platform tests before repair as expected by the acceptance exercise.
  - command: seeded Portal Universal E2E 30021875771
    result: FAIL
    evidence: Intentionally seeded deterministic backend scenario failed before repair as expected by the acceptance exercise.
  - command: repaired AI Platform CI 30022275563
    result: PASS
    evidence: Full AI Platform tests and lint passed after repair.
  - command: repaired Portal Universal E2E 30022275787
    result: PASS
    evidence: Deterministic backend and Chromium journey passed after repair.
  - command: AI Platform CI 30025621176
    result: PASS
    evidence: Final clean acceptance head passed full AI Platform tests and lint.
  - command: Portal Universal E2E 30025621171
    result: PASS
    evidence: Final clean acceptance passed deterministic backend and Chromium journey.
  - command: GitHub Actions Security Analysis with zizmor 30025621161
    result: PASS
    evidence: Final acceptance workflow security analysis passed.
  - command: Freqtrade CI 30025621399
    result: PASS
    evidence: Final acceptance required repository CI gate passed.
blockers: []
next_action: Keep the regression test durable and require any future close-time behavior change to preserve the declared exit-tick and strictly-after-open assertions.
```
