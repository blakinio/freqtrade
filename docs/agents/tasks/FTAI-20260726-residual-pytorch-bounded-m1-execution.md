---
task_id: FTAI-20260726-residual-pytorch-bounded-m1-execution
status: active
branch: fix/residual-pytorch-audit-failure-artifact
base_branch: develop
created: 2026-07-26
updated: 2026-07-27
related_pr: 463
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
updated_at: 2026-07-27T11:52:00Z
head: 1f6398cdf6c15bc84ba5a69c603a8c45ac9cb035
branch: fix/residual-pytorch-audit-failure-artifact
pr: 463
status: validating
context_routes:
  - docs/agents/CONTEXT_HANDOFF.md
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
  - ai_platform/scripts/run_experiment.py
  - tests/ai_platform/test_residual_pytorch_bounded_m1_failure_artifact.py
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_EXECUTION.md
owned_paths:
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
  - tests/ai_platform/test_residual_pytorch_bounded_m1_failure_artifact.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
proven:
  - Exclusive-stop infrastructure merged through PR 409 as 185e6a5a8fc2c5d70d0ea2173f4c5cd4a5ca702c.
  - Unix-second experiment orchestration support merged through PR 423 as f21a258643d70b4387e366e8b466dbc56735f44f.
  - PR 450 exact-head AI Platform CI run 30257613527, Freqtrade CI run 30257613509 and zizmor run 30257613580 passed, then PR 450 merged as f4e60476dc651388ed8f96663ab56defce88aa8f.
  - Exact-one-file PR 456 run 30258887950 passed request and contract validation, both Kraken acquisitions, per-pair exclusive-stop verification, cache publication and restoration, and combined pre-fit data verification.
  - Run 30258887950 used no consumed historical OOS or protected final holdout.
  - BTC coverage was 26164 rows at 15m, 6545 at 1h and 1637 at 4h; ETH coverage was 26132, 6546 and 1637 respectively; both latest 15m candles were 2026-04-30T23:45:00Z.
  - Run 30258887950 failed at `Audit exact expanded matrix before model execution`; LightGBM, seeded MLP and residual MLP were skipped.
  - Run 30258887950 published request and pair-coverage artifacts but no matrix-audit or model artifact; the always-run upload steps failed on missing evidence paths.
  - PR 456 was closed without merge after terminal evidence was recorded.
derived:
  - The bounded `run_experiment` tail is insufficiently durable when it exists only in a GitHub job log and the audit evidence directory is empty at command failure.
  - Copying immutable request, contract and combined coverage before the command, teeing bounded stderr into the audit directory and recording stdout plus exit code preserves failure evidence without changing research behavior.
  - Model artifact uploads must not create unrelated missing-path failures when model execution is skipped by the mandatory audit gate.
unknown:
  - The exact underlying Freqtrade error that caused matrix-audit backtest exit code 2.
  - The exact expanded feature count and historical NaN, outlier and target distributions.
  - Whether all three frozen models complete after the audit defect is identified and corrected.
conflicts: []
first_failure:
  marker: MATRIX_AUDIT_EXIT_2_NO_AUDIT_ARTIFACT
  evidence: Run 30258887950 passed all request, data, cache and combined pre-fit gates, then the audit command failed before producing raw matrix evidence; the audit upload found no files and no model execution started.
rejected_hypotheses:
  - Pre-May data coverage or exclusive-stop verification failed; both pair jobs and combined pre-fit verification passed.
  - A frozen model caused the terminal failure; all three model executions were skipped.
  - The request, contract or cache identity drifted; all corresponding validation and restoration steps passed.
changed_paths:
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
  - tests/ai_platform/test_residual_pytorch_bounded_m1_failure_artifact.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
validation:
  - command: GitHub Actions run 30258887950 on PR 456
    result: FAIL
    evidence: Required pre-May gates passed; audit failed before matrix evidence; all models were skipped and PR 456 was closed without merge.
  - command: Static durable-failure workflow contract tests on PR 463
    result: NOT_RUN
    evidence: Exact-head CI has not completed on the checkpoint commit.
blockers:
  - Exact-head AI Platform CI, Freqtrade CI and zizmor must pass before PR 463 can merge.
next_action: Validate and merge PR 463 only if exact-head AI Platform CI, Freqtrade CI and zizmor are green, then create a fresh canonical exact-one-file request to capture the durable audit failure artifact.
```
