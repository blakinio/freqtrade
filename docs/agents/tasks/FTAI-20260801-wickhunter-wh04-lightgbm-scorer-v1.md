---
task_id: FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1
project_lane: freqtrade-wickhunter
status: waiting
branch: feat/wickhunter-wh04-lightgbm-scorer-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: null
depends_on:
  - FTAI-20260801-wickhunter-wh03-baseline-strategy-v1
owned_paths:
  - ai_platform/wickhunter/lightgbm_scorer.py
  - tests/ai_platform_integration/test_wickhunter_lightgbm_scorer.py
  - docs/ai_platform/WICKHUNTER_LIGHTGBM_SCORER.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1.md
required_reads:
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh03-baseline-strategy-v1.md
---

# WH-04 LightGBM candidate scorer

## Objective

Train and calibrate one advisory LightGBM candidate scorer against the frozen WH-02/WH-03 contracts, with identical-data baseline comparison and auditable candidate registry evidence.

## Phases

1. `WH04-IMPLEMENT` — dataset adapter, training, calibration, registry evidence and comparison.
2. `WH04-VALIDATE` — fresh exact-head validator session.

## Acceptance

- supervised dataset adapter consumes immutable replay labels;
- feature and leakage audit passes;
- calibration and no-trade confidence are explicit;
- model artifacts and identities are reproducible and hashed;
- comparison uses the exact WH-03 evaluation interface and costs;
- model outputs remain advisory;
- no order adapter, automatic promotion or live-capital authority.

## Invocation

`Uruchom WickHunter WH-04.` starts only after WH-03 is terminal and merged. `Zweryfikuj WickHunter WH-04.` validates only the exact candidate head recorded below.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T15:23:00+02:00
project_lane: freqtrade-wickhunter
phase: implement
session_id: unclaimed
session_role: implementer
execution_mode: codex
execution_reason: model training adapter, artifacts and focused test loop require a checkout
status: waiting
branch: feat/wickhunter-wh04-lightgbm-scorer-v1
base_branch: develop
related_pr: null
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: one model package owns training, calibration, evidence and validation
validation_level: not_started
heavy_validation_runs: 0
proven:
  - WH-04 depends on the frozen WH-03 evaluation interface
derived:
  - WH-04 and WH-05 may run in parallel only after WH-03, on non-overlapping owned paths
unknown:
  - final WH-03 interface and exact model activity
conflicts: []
first_relevant_error: null
changed_paths: []
validation: []
blockers:
  - WH-03 is not yet terminal
next_action: after WH-03 merges, verify its exact evaluation contract and claim WH-04 paths before implementing the advisory LightGBM package
```
