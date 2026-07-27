---
task_id: FTAI-20260726-residual-pytorch-bounded-m1-execution
status: active
branch: fix/residual-pytorch-epoch-timerange-orchestration
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: 423
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
updated_at: 2026-07-27T07:15:00Z
head: 8bb2a2a8424e9e35bfc14e8f52fff571f42c3ba4
merge_commit: null
branch: fix/residual-pytorch-epoch-timerange-orchestration
pr: 423
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-data-target-audit.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - ai_platform/scripts/run_experiment.py
  - ai_platform/scripts/protected_final_holdout.py
owned_paths:
  - ai_platform/experiments/schema-v1.json
  - ai_platform/scripts/protected_final_holdout.py
  - ai_platform/scripts/run_experiment.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
  - tests/ai_platform/test_protected_final_holdout.py
  - tests/ai_platform/test_run_experiment.py
proven:
  - Exclusive-stop infrastructure merged through PR 409 as 185e6a5a8fc2c5d70d0ea2173f4c5cd4a5ca702c.
  - Exact-one-file PR 419 and run 30224752320 passed request validation, both Kraken downloads, per-pair exclusive-stop verification, cache publication and combined pre-fit data verification.
  - BTC coverage ended at 2026-04-30T23:45:00Z on 15m with 26164 rows; ETH ended at the same boundary with 26132 rows; consumed historical OOS and protected holdout were not used.
  - Run 30224752320 failed closed before matrix creation with `Experiment failed: timerange must use YYYYMMDD-YYYYMMDD format`.
  - Matrix audit artifacts were not created and LightGBM, seeded MLP and residual MLP executions were skipped.
derived:
  - The frozen epoch-second geometry is accepted by Freqtrade and the dedicated data verifier but rejected by the generic experiment-manifest orchestration layer.
  - Supporting both existing date-form and 10-digit Unix-second ranges in one shared parser preserves holdout isolation without changing research geometry.
unknown:
  - Exact FreqAI-expanded feature count and historical NaN, outlier and target distributions.
  - Whether all three frozen models complete after orchestration accepts the authorized epoch-second timeranges.
conflicts: []
first_failure:
  marker: EPOCH_TIMERANGE_ORCHESTRATION_REJECTED
  evidence: The audit command exited before creating a run directory because run_experiment schema validation accepted only YYYYMMDD-YYYYMMDD while all frozen M1 manifests use verified 10-digit Unix-second ranges.
rejected_hypotheses:
  - The exclusive-stop correction failed; both pair and combined data verification passed.
  - Kraken data or cache restoration failed; both dedicated caches were saved and restored successfully.
  - A model or matrix-quality defect caused the failure; no matrix artifact or model fit was created.
changed_paths:
  - ai_platform/experiments/schema-v1.json
  - ai_platform/scripts/protected_final_holdout.py
  - ai_platform/scripts/run_experiment.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
  - tests/ai_platform/test_protected_final_holdout.py
  - tests/ai_platform/test_run_experiment.py
validation:
  - command: pytest -q tests/ai_platform/test_run_experiment.py tests/ai_platform/test_protected_final_holdout.py tests/ai_platform/test_residual_pytorch_bounded_m1_execution.py
    result: PASS
    evidence: Date-form and epoch-second manifests, protected-holdout overlap detection and bounded M1 contract tests pass without market access.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md --require-checkpoint
    result: PASS
    evidence: Compact checkpoint is governance-valid with exactly one next action.
  - command: python -m ai_platform.scripts.residual_pytorch_bounded_m1_execution contract
    result: PASS
    evidence: Frozen bounded contract and manifests remain valid without execution.
blockers: []
next_action: Validate and merge the exact-head epoch-timerange orchestration correction, then generate one fresh canonical exact-one-file request and resume the guarded M1 run from verified caches without changing frozen geometry.
```
