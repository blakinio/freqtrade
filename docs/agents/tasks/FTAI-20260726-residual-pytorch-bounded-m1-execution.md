---
task_id: FTAI-20260726-residual-pytorch-bounded-m1-execution
status: active
branch: fix/residual-pytorch-bounded-m1-exclusive-stop
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: 409
owned_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_EXECUTION.md
  - ai_platform/experimental_model_research/residual-pytorch-bounded-m1-execution-contract-v1.json
  - ai_platform/scripts/residual_pytorch_bounded_m1_execution.py
  - ai_platform/scripts/residual_pytorch_bounded_m1_run_request.py
  - ai_platform/configs/freqai-residual-pytorch-m1-data-audit.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-lightgbm.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-seeded-mlp.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-residual-mlp.example.json
  - ai_platform/experiments/residual-pytorch-m1-data-audit-v1.json
  - ai_platform/experiments/residual-pytorch-m1-lightgbm-v1.json
  - ai_platform/experiments/residual-pytorch-m1-seeded-mlp-v1.json
  - ai_platform/experiments/residual-pytorch-m1-residual-mlp-v1.json
  - ai_platform/freqaimodels/residual_pytorch_m1_instrumentation.py
  - ai_platform/freqaimodels/ResidualPyTorchM1DataAuditRegressor.py
  - ai_platform/freqaimodels/M1LightGBMRegressor.py
  - ai_platform/freqaimodels/M1SeededPyTorchMLPRegressor.py
  - ai_platform/freqaimodels/M1ResidualPyTorchRegressor.py
  - ai_platform/experimental_model_research/run-requests/residual-pytorch-bounded-m1-execution-v1.json
  - tests/ai_platform/test_residual_pytorch_bounded_m1_execution.py
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-data-target-audit.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - docs/ai_platform/RESIDUAL_PYTORCH_DATA_TARGET_AUDIT.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
search_first:
  - current develop and open ownership on residual PyTorch P3
  - existing guarded historical execution and market-data cache contracts
context_routes:
  - ai_platform/configs/freqai-residual-pytorch-research.example.json
  - ai_platform/experiments/residual-pytorch-research-v1.json
  - ai_platform/strategies/AiFrozenCandidateStrategy.py
  - ai_platform/scripts/run_experiment.py
---

# Residual PyTorch P3 bounded M1 execution

## Goal

Build and use one fail-closed, one-shot historical-development execution path that compares `LightGBMRegressor`, `SeededPyTorchMLPRegressor` and `ResidualPyTorchRegressor` on exactly the same frozen feature, target, strategy, pair, timeframe, fee, training and evaluation geometry.

## Authorization and boundaries

The user explicitly authorized autonomous continuation into P3 on 2026-07-26. This authorization is limited to the bounded research package below.

The package must:

- use Kraken spot `BTC/USDT` and `ETH/USDT` at `15m`, `1h` and `4h`;
- use `AiFrozenCandidateStrategy`, target `&-future_return`, future offsets `t+1` through `t+12`, entry threshold `0.006`, exit threshold `-0.009` and fee ratio `0.002` unchanged;
- use one frozen 90-day training window ending before March 2026;
- use historical-development prediction/evaluation coverage `20260301-20260430`, encoded as Freqtrade timerange `1772323200-1777593599` so its inclusive stop is exactly `2026-04-30T23:59:59Z`;
- use download coverage `1754006400-1777593599`, ending one second before the exclusive `2026-05-01T00:00:00Z` boundary, and never read consumed May-June historical OOS;
- use seed `42` for every stochastic model or library setting that exposes a seed;
- execute at most once per declared model after a separate exact-one-file run-request PR;
- measure the exact FreqAI-expanded feature count plus historical feature NaN, outlier and label distributions before model execution and fail closed if this evidence is absent or non-finite;
- label all outputs historical development evidence only.

The package must not:

- access consumed historical OOS `20260501-20260630` or the protected final holdout `20260801-20260930`;
- change features, targets, strategy thresholds, pair universe, timeframes, fees or temporal geometry between models;
- tune from execution outcomes, run Hyperopt, add liquidation features or alter model architecture defaults;
- change completed Phase 6 candidates, policy, evidence or `selected_model = null`;
- select or promote a winner, deploy, trade live, or claim profitability, superiority or production readiness.

The infrastructure PR must not contain the canonical run-request file and must not execute market-data acquisition, training or backtesting. Real execution requires a later pull request adding exactly the canonical request path and must be closed without merge after terminal evidence collection.

## Required evidence

Before any model fit, the workflow must persist exact matrix dimensions, per-column finite/NaN coverage, declared outlier diagnostics and target distribution/edge-null counts for the authorized pre-May data only. Each model execution must persist hashes, config, manifest, strategy/model identity, runtime provenance, prediction diagnostics and trading-level development metrics. Cross-model presentation may be descriptive but must contain no winner-selection rule.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T22:10:00Z
head: d8aa4453d64a2cadefc9cf00ed74c8416904f7ab
merge_commit: null
branch: fix/residual-pytorch-bounded-m1-exclusive-stop
pr: 409
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-data-target-audit.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EXECUTION.md
  - ai_platform/scripts/run_experiment.py
owned_paths:
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
  - ai_platform/experimental_model_research/residual-pytorch-bounded-m1-execution-contract-v1.json
  - ai_platform/experiments/residual-pytorch-m1-data-audit-v1.json
  - ai_platform/experiments/residual-pytorch-m1-lightgbm-v1.json
  - ai_platform/experiments/residual-pytorch-m1-residual-mlp-v1.json
  - ai_platform/experiments/residual-pytorch-m1-seeded-mlp-v1.json
  - ai_platform/scripts/residual_pytorch_bounded_m1_execution.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_EXECUTION.md
  - tests/ai_platform/test_residual_pytorch_bounded_m1_execution.py
proven:
  - P2 implementation and closeout are merged, and P3 infrastructure merged through PR 395 as fc210dd68f0998176e3bf2da3bd29b231a511ae7.
  - Exact-one-file trigger PRs 400, 401 and 402 each passed request validation and completed both authorized Kraken trade downloads without starting any model.
  - Runs 30220022577, 30220023431 and 30220063748 all failed closed during pair coverage verification; cache publication, matrix audit, training and backtesting were skipped.
  - Exact terminal evidence from run 30220022577 reported `Post-development candle was loaded for ETH/USDT 15m` and the same failure for BTC/USDT 15m.
  - Freqtrade `trim_dataframe` applies date-form stop boundaries inclusively with `<=`, while the frozen P3 contract requires an exclusive stop at `2026-05-01T00:00:00Z`.
derived:
  - Encoding both acquisition and backtest timeranges with Unix-second stop `1777593599` preserves the frozen March-April geometry and excludes the first consumed-OOS second.
  - The failed executions provide no feature-count, matrix-distribution, training, prediction or backtest evidence.
unknown:
  - Exact FreqAI-expanded feature count and historical NaN, outlier and target distributions.
  - Whether all three frozen models complete the bounded historical-development lifecycle after the boundary correction.
conflicts: []
first_failure:
  marker: POST_DEVELOPMENT_BOUNDARY_CANDLE
  evidence: All three guarded attempts downloaded data but failed before cache publication because the inclusive 15m load admitted the `2026-05-01T00:00:00Z` candle for both pairs.
rejected_hypotheses:
  - Kraken history was unavailable; both pair downloads completed successfully.
  - A model or matrix-audit defect caused the run; those stages were never entered.
  - Consumed May-June OOS or the protected holdout may be used to repair the run.
changed_paths:
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
  - ai_platform/experimental_model_research/residual-pytorch-bounded-m1-execution-contract-v1.json
  - ai_platform/experiments/residual-pytorch-m1-data-audit-v1.json
  - ai_platform/experiments/residual-pytorch-m1-lightgbm-v1.json
  - ai_platform/experiments/residual-pytorch-m1-residual-mlp-v1.json
  - ai_platform/experiments/residual-pytorch-m1-seeded-mlp-v1.json
  - ai_platform/scripts/residual_pytorch_bounded_m1_execution.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_EXECUTION.md
  - tests/ai_platform/test_residual_pytorch_bounded_m1_execution.py
validation:
  - command: python -m unittest discover -s tests/ai_platform -p test_residual_pytorch_bounded_m1_execution.py
    result: PASS
    evidence: Bootstrap validation exercises frozen contract, exact timerange encoding, matrix and diagnostic guards without market access.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md --require-checkpoint
    result: PASS
    evidence: Active compact checkpoint remains governance-valid with exactly one next action.
  - command: python -m ai_platform.scripts.residual_pytorch_bounded_m1_execution contract
    result: PASS
    evidence: Corrected contract and all frozen manifests validate without market-data access or execution.
blockers: []
next_action: Validate the exact-head exclusive-stop correction in CI, merge it, then open one fresh canonical exact-one-file request PR and collect terminal guarded evidence without changing the frozen research geometry.
```
