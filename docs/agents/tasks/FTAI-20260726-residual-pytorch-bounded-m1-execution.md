---
task_id: FTAI-20260726-residual-pytorch-bounded-m1-execution
status: active
branch: run/residual-pytorch-bounded-m1-execution-v5
base_branch: develop
created: 2026-07-26
updated: 2026-07-27
related_pr: 456
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
updated_at: 2026-07-27T11:22:00Z
head: d08315fef3f4cd08c7d5c7bc5e1f4d75e7503f5b
branch: run/residual-pytorch-bounded-m1-execution-v5
pr: 456
status: validating
context_routes:
  - docs/agents/CONTEXT_HANDOFF.md
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
  - ai_platform/scripts/run_experiment.py
  - ai_platform/scripts/residual_pytorch_bounded_m1_execution.py
  - ai_platform/scripts/residual_pytorch_bounded_m1_run_request.py
owned_paths:
  - ai_platform/experimental_model_research/run-requests/residual-pytorch-bounded-m1-execution-v1.json
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
proven:
  - Exclusive-stop infrastructure merged through PR 409 as 185e6a5a8fc2c5d70d0ea2173f4c5cd4a5ca702c.
  - Unix-second experiment orchestration support merged through PR 423 as f21a258643d70b4387e366e8b466dbc56735f44f.
  - Exact-one-file PR 437 run 30248969155 passed request and contract validation, both Kraken acquisitions, per-pair exclusive-stop verification, cache publication and combined pre-fit data verification.
  - Run 30248969155 used no consumed historical OOS or protected final holdout; BTC and ETH latest 15m candles were 2026-04-30T23:45:00Z.
  - Run 30248969155 failed at `Audit exact expanded matrix before model execution` with backtest exit code 2; LightGBM, seeded MLP and residual MLP were skipped.
  - Diagnostic PR 447 closed without merge and confirmed the nested Freqtrade stderr was unavailable because `backtest.log` and the failed run directory were transient.
  - PR 450 removed the temporary bootstrap workflow and left only the bounded log-tail correction, its focused test and this checkpoint.
  - PR 450 exact-head AI Platform CI run 30257613527, Freqtrade CI run 30257613509 and zizmor run 30257613580 all completed successfully on 1617e4beb2ca2f498f5345552de10a276bd75936.
  - PR 450 merged by squash as f4e60476dc651388ed8f96663ab56defce88aa8f.
  - Fresh PR 456 head d08315fef3f4cd08c7d5c7bc5e1f4d75e7503f5b adds exactly the canonical run-request file and no other path.
  - Run 30258887950 passed exact-one-file scope, active checkpoint, canonical request and frozen-infrastructure validation.
  - Run 30258887950 BTC and ETH jobs reached only the authorized pre-May cache-miss download step; no matrix audit or model execution has started.
derived:
  - The merged bounded log-tail correction should expose the next nested Freqtrade failure without changing frozen geometry, market-data scope or model behavior.
  - Request-bound contract, strategy, instrumentation, config, manifest and model files did not change between the prior canonical request base and PR 456 base, so the regenerated canonical request remains byte-identical.
unknown:
  - The exact underlying Freqtrade error that caused matrix-audit backtest exit code 2.
  - The exact expanded feature count and historical NaN, outlier and target distributions.
  - Whether all three frozen models complete after the audit defect is identified and corrected.
conflicts: []
first_failure:
  marker: MATRIX_AUDIT_BACKTEST_EXIT_2_LOG_NOT_DURABLE
  evidence: Run 30248969155 passed all request, data and combined pre-fit gates, then the audit backtest exited 2 before matrix evidence; the nested stderr was redirected to a non-persisted `backtest.log`.
rejected_hypotheses:
  - Pre-May data coverage or exclusive-stop verification failed in run 30248969155; both pair jobs and combined data verification passed.
  - A frozen model caused the prior terminal failure; no model execution started.
  - Unix-second orchestration regressed; request and contract revalidation passed and failure moved into the audit backtest.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
validation:
  - command: Exact-head PR 450 AI Platform CI, Freqtrade CI and zizmor
    result: PASS
    evidence: Runs 30257613527, 30257613509 and 30257613580 completed successfully on 1617e4beb2ca2f498f5345552de10a276bd75936.
  - command: Merge PR 450 with expected head 1617e4beb2ca2f498f5345552de10a276bd75936
    result: PASS
    evidence: Squash merge produced f4e60476dc651388ed8f96663ab56defce88aa8f.
  - command: PR 456 exact-one-file and canonical request validation in run 30258887950
    result: PASS
    evidence: Job 89953854803 completed successfully before any market-data access.
  - command: PR 456 pair coverage, combined pre-fit verification, matrix audit and frozen model execution
    result: NOT_RUN
    evidence: BTC job 89953958214 and ETH job 89953958239 remain in the authorized pre-May cache-miss download step; downstream execution has not started.
blockers:
  - Run 30258887950 is nonterminal while both authorized pre-May data jobs remain in progress.
next_action: Observe run 30258887950 to its first terminal failure or completion, persist bounded evidence in PR 456, and close PR 456 without merge.
```
