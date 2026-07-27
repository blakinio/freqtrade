---
task_id: FTAI-20260726-residual-pytorch-bounded-m1-execution
status: active
branch: fix/residual-pytorch-model-import-path
base_branch: develop
created: 2026-07-26
updated: 2026-07-27
related_pr: 481
owned_paths:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_EXECUTION.md
  - ai_platform/experimental_model_research/residual-pytorch-bounded-m1-execution-contract-v1.json
  - ai_platform/scripts/residual_pytorch_bounded_m1_execution.py
  - ai_platform/scripts/residual_pytorch_bounded_m1_run_request.py
  - ai_platform/scripts/run_experiment.py
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
  - tests/ai_platform/test_run_experiment.py
  - tests/ai_platform/test_residual_pytorch_bounded_m1_execution.py
  - tests/ai_platform/test_residual_pytorch_bounded_m1_failure_artifact.py
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
updated_at: 2026-07-27T13:50:00Z
head: f3a298e1eb7e755fb527eb85a790eae49fc6128f
branch: fix/residual-pytorch-model-import-path
pr: 481
status: validating
context_routes:
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_platform/scripts/run_experiment.py
  - tests/ai_platform/test_run_experiment.py
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
owned_paths:
  - ai_platform/scripts/run_experiment.py
  - tests/ai_platform/test_run_experiment.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
proven:
  - Exclusive-stop infrastructure merged through PR 409 as 185e6a5a8fc2c5d70d0ea2173f4c5cd4a5ca702c.
  - Unix-second experiment orchestration support merged through PR 423 as f21a258643d70b4387e366e8b466dbc56735f44f.
  - Bounded M1 infrastructure merged through PR 450 as f4e60476dc651388ed8f96663ab56defce88aa8f after exact-head CI passed.
  - Durable audit-failure evidence support merged through PR 463 as ef6a3f31ebbcf5bbdfae2ce51ece762f2a425c93 after exact-head AI Platform CI, Freqtrade CI and zizmor passed.
  - Exact-one-file PR 469 run 30266002127 passed request validation, both Kraken pre-May acquisitions, per-pair exclusive-stop verification, cache publication and restoration, and combined pre-fit verification.
  - Run 30266002127 used no consumed historical OOS or protected final holdout and published durable audit artifact residual-pytorch-bounded-m1-audit-469 with digest sha256:821507fb73beb555164a686699e33f78026a702d7fbb500728be2fac75bce417.
  - Run 30266002127 failed before matrix audit because the Freqtrade console subprocess could not import ai_platform while resolving ResidualPyTorchM1DataAuditRegressor; all three frozen model executions were skipped.
  - PR 469 was closed without merge after terminal evidence collection.
derived:
  - Running the Python orchestrator from the repository root does not guarantee that a console-script child process has the repository root on sys.path.
  - The narrow fix is to prepend the resolved repository root to the child PYTHONPATH while preserving all existing child environment variables and existing PYTHONPATH entries.
  - The correction changes import reachability only; it does not alter data, features, targets, model defaults, thresholds, temporal geometry or execution authorization.
unknown:
  - The exact expanded feature count and historical NaN, outlier and target distributions.
  - Whether the mandatory matrix audit passes after the import correction.
  - Whether all three frozen models complete exactly once after the audit passes.
conflicts: []
first_failure:
  marker: FREQAI_MODEL_IMPORT_REPO_ROOT_MISSING
  evidence: Run 30266002127 audit artifact recorded `No module named 'ai_platform'` and `Impossible to load FreqaiModel 'ResidualPyTorchM1DataAuditRegressor'` before any matrix audit or model fit.
rejected_hypotheses:
  - Pre-May data coverage or exclusive-stop verification failed; both pair jobs and combined pre-fit verification passed.
  - A frozen model fit caused the failure; no audit fit or model fit started.
  - The canonical request, contract or cache identity drifted; all corresponding gates passed.
changed_paths:
  - ai_platform/scripts/run_experiment.py
  - tests/ai_platform/test_run_experiment.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
validation:
  - command: Local Python compile validation of the reconstructed changed source and test files
    result: PASS
    evidence: Both changed Python files compiled successfully before repository writes; exact-head CI remains authoritative.
blockers:
  - Exact-head AI Platform CI, Freqtrade CI and zizmor must pass on PR 481 before merge.
next_action: Validate and merge PR 481 only if exact-head AI Platform CI, Freqtrade CI and zizmor are green, then create a fresh canonical exact-one-file request from the resulting develop head.
```
