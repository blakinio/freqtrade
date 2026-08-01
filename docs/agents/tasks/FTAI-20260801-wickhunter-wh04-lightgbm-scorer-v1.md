---
task_id: FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1
project_lane: freqtrade-wickhunter
status: validating
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
  - docs/ai_platform/WICKHUNTER_BASELINE_STRATEGY.md
---

# WH-04 deterministic LightGBM scorer

## Objective

Train and validate one deterministic candidate-level LightGBM scorer on the immutable WH-01/WH-02 evidence and the WH-03 shared evaluation interface without accessing the protected holdout or authorizing automatic promotion.

## Phases

1. `WH04-DESIGN` — freeze decision-time feature, split, calibration, no-trade, registry and comparison contracts.
2. `WH04-IMPLEMENT` — deterministic trainer, immutable artifact, advisory scorer and WH-03-compatible report.
3. `WH04-VALIDATE` — fresh exact-head repository validation.

## Acceptance

- one LightGBM binary candidate scorer;
- deterministic seeds, one thread and forced column-wise training;
- decision-time leakage audit and protected-holdout refusal;
- dedicated training, calibration and validation splits;
- calibrated confidence and explicit no-trade threshold;
- expected return derived from exact WH-02 after-cost labels;
- reproducible model text/hash and immutable registry record;
- comparison through the WH-03 interface and summaries;
- no automatic promotion, execution, order or live-capital authority.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T20:18:00+02:00
project_lane: freqtrade-wickhunter
phase: validate
session_id: wh04-20260801-001
session_role: implementer
execution_mode: chat
execution_reason: direct GitHub implementation with deterministic local LightGBM seam verification and exact-head CI
status: validating
branch: feat/wickhunter-wh04-lightgbm-scorer-v1
base_branch: develop
related_pr: null
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: trainer, artifact, scorer and comparison report share one frozen feature and model identity
validation_level: focused
heavy_validation_runs: 0
proven:
  - WH-03 merged to develop as 03810d0c82072d642946ce1d274c86a577ec5349 after final exact-head checks passed
  - live ownership preflight found no WH-04 branch, PR or overlapping writer
  - LightGBM model_to_string is reproducible with deterministic=true, force_col_wise=true, num_threads=1 and fixed seeds
  - the frozen feature schema contains only decision-time liquidation, market, source, side and hypothesis values
  - feature names associated with labels, returns, outcomes, future/exit data, costs and excursions are refused
  - training, calibration and validation splits are explicit and disjoint; protected holdout splits fail closed
  - candidate targets and expected-return values are bound to exact matching-side WH-02 net labels
  - raw probabilities receive deterministic binned monotonic calibration and an explicit no-trade threshold
  - model decisions and model-versus-baseline summaries use the WH-03 evaluation interface without redefining costs
  - model registry state is candidate/advisory only and all promotion, execution, order and live-capital authority remains disabled
derived:
  - WH-05 can compare bounded parameter candidates against this immutable artifact without mutating model or replay contracts
unknown:
  - exact-head repository CI and formatter findings
conflicts: []
first_relevant_error: null
changed_paths:
  - ai_platform/wickhunter/lightgbm_scorer.py
  - tests/ai_platform_integration/test_wickhunter_lightgbm_scorer.py
  - docs/ai_platform/WICKHUNTER_LIGHTGBM_SCORER.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1.md
validation:
  - command: isolated LightGBM deterministic model-string experiment
    result: PASS
    evidence: repeated fixed-seed one-thread training produced identical predictions and SHA-256 model hash
blockers: []
next_action: open the exact four-path PR, run focused and repository CI, repair only concrete failures, then perform fresh exact-head validation and merge
```
