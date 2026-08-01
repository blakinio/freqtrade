---
task_id: FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1
project_lane: freqtrade-wickhunter
status: validating
branch: feat/wickhunter-wh04-lightgbm-scorer-v1-clean
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: 961
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
updated_at: 2026-08-01T21:42:00+02:00
project_lane: freqtrade-wickhunter
phase: validate
session_id: wh04-20260801-001
session_role: implementer
execution_mode: chat
execution_reason: direct GitHub implementation with deterministic LightGBM seam verification and exact-head CI
status: validating
branch: feat/wickhunter-wh04-lightgbm-scorer-v1-clean
head: d1886f4620978704886df889dba034b12c113e55
base_branch: develop
related_pr: 961
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: trainer, artifact, scorer and comparison report share one frozen feature and model identity
validation_level: repository
heavy_validation_runs: 5
proven:
  - WH-03 merged to develop as 03810d0c82072d642946ce1d274c86a577ec5349 after final exact-head checks passed
  - PR 961 changes exactly the four declared WH-04 owned paths and has no comments, reviews or unresolved threads
  - LightGBM model_to_string is reproducible with deterministic=true, force_col_wise=true, num_threads=1 and fixed seeds
  - the frozen feature schema contains only decision-time liquidation, market, source, side and hypothesis values
  - leakage-prone feature names, future data, protected holdout splits and mismatched replay identities fail closed
  - training, calibration and validation splits are explicit and disjoint
  - candidate targets and expected-return values are bound to exact matching-side WH-02 net labels
  - raw probabilities receive deterministic monotonic calibration and an explicit no-trade threshold
  - model decisions and model-versus-baseline summaries use the WH-03 evaluation interface without redefining costs
  - model registry state is candidate/advisory only and all promotion, execution, order and live-capital authority remains disabled
  - stale WickHunterCandidate reconstruction was aligned to the current contract without changing model behavior
  - AI Platform CI run 3665 passed 1059 tests with 71 skips; Ruff, Ruff format, codespell and JSON validations passed
  - Freqtrade CI run 4767 passed pre-commit, documentation, Python 3.11, 3.12 coverage, 3.13 and 3.14 paths
  - security analysis run 4427 passed on d1886f4620978704886df889dba034b12c113e55
derived:
  - WH-05 model-aware phase may train and compare bounded candidate artifacts only through this immutable advisory interface
  - WH-07 may consume candidate scores but cannot treat candidate promotion state as live authority
unknown: []
conflicts: []
first_relevant_error: null
changed_paths:
  - ai_platform/wickhunter/lightgbm_scorer.py
  - tests/ai_platform_integration/test_wickhunter_lightgbm_scorer.py
  - docs/ai_platform/WICKHUNTER_LIGHTGBM_SCORER.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1.md
validation:
  - command: isolated deterministic LightGBM model-string experiment
    result: PASS
    evidence: repeated fixed-seed one-thread training produced identical predictions and SHA-256 model hash
  - command: AI Platform CI run 3665
    result: PASS, 1059 tests and 71 skips
    evidence: compile, tests, Ruff, formatting, codespell and JSON validations all passed
  - command: Freqtrade CI run 4767
    result: PASS
    evidence: pre-commit, documentation, Python 3.11, Python 3.12 coverage, Python 3.13, Python 3.14, generated files, smoke tests and mypy passed
  - command: GitHub Actions Security Analysis run 4427
    result: PASS
    evidence: exact head d1886f4620978704886df889dba034b12c113e55
blockers: []
next_action: validate the checkpoint-only head and merge PR 961 with expected-head protection
```
