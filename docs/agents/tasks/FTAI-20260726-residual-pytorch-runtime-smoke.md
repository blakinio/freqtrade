---
task_id: FTAI-20260726-residual-pytorch-runtime-smoke
status: completed
branch: test/residual-pytorch-runtime-smoke
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: 355
owned_paths:
  - .github/workflows/residual-pytorch-runtime-smoke.yml
  - ai_platform/experimental_model_research/residual-pytorch-runtime-smoke-contract-v1.json
  - ai_platform/freqaimodels/ResidualPyTorchRegressor.py
  - ai_platform/scripts/residual_pytorch_runtime_smoke.py
  - ai_platform/scripts/residual_pytorch_runtime_smoke_contract.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-runtime-smoke.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RUNTIME_SMOKE.md
  - tests/ai_platform/test_residual_pytorch_runtime_smoke_contract.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-research-foundation.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RUNTIME_SMOKE.md
context_routes:
  - ai_platform/experimental_model_research/residual-pytorch-research-contract-v1.json
  - ai_platform/freqaimodels/ResidualPyTorchRegressor.py
  - freqtrade/resolvers/freqaimodel_resolver.py
  - freqtrade/freqai/base_models/BasePyTorchRegressor.py
  - freqtrade/freqai/torch/PyTorchModelTrainer.py
---

# Residual PyTorch P1 runtime smoke

## Goal

Prove or reject technical lifecycle support for `ResidualPyTorchRegressor` using only deterministic synthetic data and the official FreqAI resolver.

## Boundaries

This task authorized bounded synthetic fitting only. It performed no exchange download, market-data training, backtest, Hyperopt, feature search, historical-OOS use, protected-holdout use, deployment, promotion or profitability scoring.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T16:05:00+02:00
head: 23ab72fe99bffe2d5d1869ae666346250c452a7d
merge_commit: b51b8850db32e0050b9fa876dd141a49c0cf68c5
branch: test/residual-pytorch-runtime-smoke
pr: 355
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-research-foundation.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - ai_platform/experimental_model_research/residual-pytorch-research-contract-v1.json
  - ai_platform/experimental_model_research/residual-pytorch-runtime-smoke-contract-v1.json
  - ai_platform/scripts/residual_pytorch_runtime_smoke.py
owned_paths:
  - .github/workflows/residual-pytorch-runtime-smoke.yml
  - ai_platform/experimental_model_research/residual-pytorch-runtime-smoke-contract-v1.json
  - ai_platform/freqaimodels/ResidualPyTorchRegressor.py
  - ai_platform/scripts/residual_pytorch_runtime_smoke.py
  - ai_platform/scripts/residual_pytorch_runtime_smoke_contract.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-runtime-smoke.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RUNTIME_SMOKE.md
  - tests/ai_platform/test_residual_pytorch_runtime_smoke_contract.py
proven:
  - P0 implementation merged as 1ed82158374684aa9a01b3d98e172fcca84ee88d and its closeout merged as 002dda9990592854ccdbad65aa72d59c647c83cf.
  - PR 355 merged head as b51b8850db32e0050b9fa876dd141a49c0cf68c5 with exactly eight intended paths and no review blocker.
  - Official FreqaiModelResolver loading and CPU construct, forward, fit, predict, save, load and repeated predict succeeded.
  - Runtime outcome is runtime_supported on Python 3.12.13 and torch 2.13.0+cu130 for a frozen 199561-parameter network.
  - Same-seed repeated training produced identical parameters and predictions.
  - Predictions before and after checkpoint restoration were identical and metadata bound architecture, dimensions, parameter count and seed.
  - Multiple targets, zero features, row mismatch, missing checkpoint, invalid learning rate and continual learning failed closed.
  - CUDA was unavailable and was explicitly reported as skipped rather than inferred as supported.
  - Synthetic rows began on 2025-01-01 and remained before all protected windows.
  - No exchange access, market data, market training, backtest, historical OOS or protected holdout was used.
  - Final exact-head AI Platform CI 30201896876 run 1536 succeeded.
  - Final exact-head Residual PyTorch Runtime Smoke 30201896916 run 19 succeeded with runtime_supported.
  - Final exact-head Experimental Model Runtime Smoke 30201896871 run 129 succeeded.
  - Final exact-head zizmor 30201896894 run 1721 succeeded.
  - Final exact-head Freqtrade CI 30201896868 run 1856 succeeded, including pre-commit, mypy, documentation, Python 3.11 through 3.14, coverage, distribution build and CI Gate.
derived:
  - ResidualPyTorchRegressor is technically supported for the bounded P1 lifecycle only.
  - P1 provides no evidence about market-data quality, target quality, predictive quality, trading performance or production readiness.
  - P2 data and target audit must remain a separate development-only task and PR.
unknown:
  - CUDA lifecycle behavior on an actual CUDA-capable runner.
  - Market-data quality, target quality, predictive quality and trading performance.
conflicts: []
first_failure:
  marker: INCOMPLETE_RUNTIME_DEPENDENCY_PROFILE
  evidence: Initial workflow installed only .[freqai], so torch and pytest were unavailable before model import.
  correction: Installed .[freqai,freqai_rl,develop], preserved diagnostics, and fixed only confirmed contract, Ruff and mypy errors.
rejected_hypotheses:
  - Use exchange or historical market data for a runtime smoke.
  - Add backtesting or profitability metrics to P1.
  - Change frozen architecture, seed or training parameters.
  - Treat unavailable CUDA as a failed CPU lifecycle or as proof of CUDA support.
changed_paths:
  - .github/workflows/residual-pytorch-runtime-smoke.yml
  - ai_platform/experimental_model_research/residual-pytorch-runtime-smoke-contract-v1.json
  - ai_platform/freqaimodels/ResidualPyTorchRegressor.py
  - ai_platform/scripts/residual_pytorch_runtime_smoke.py
  - ai_platform/scripts/residual_pytorch_runtime_smoke_contract.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-runtime-smoke.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RUNTIME_SMOKE.md
  - tests/ai_platform/test_residual_pytorch_runtime_smoke_contract.py
validation:
  - command: Residual PyTorch Runtime Smoke 30201896916
    result: PASS
    evidence: Run 19 completed checkpoint validation, tests, Ruff, formatting, full pre-commit, resolver lifecycle, reproducibility, save-load and fail-closed checks with runtime_supported.
  - command: AI Platform CI 30201896876
    result: PASS
    evidence: Run 1536 passed tests, Ruff, format, codespell and JSON validation.
  - command: Experimental Model Runtime Smoke 30201896871
    result: PASS
    evidence: Run 129 passed the canonical heavy-runtime smoke.
  - command: Freqtrade CI 30201896868
    result: PASS
    evidence: Run 1856 passed pre-commit, mypy, documentation, Python 3.11-3.14 matrices, coverage, distribution build and CI Gate.
  - command: zizmor 30201896894
    result: PASS
    evidence: Run 1721 completed successfully.
blockers: []
next_action: Start bounded task FTAI-20260726-residual-pytorch-data-target-audit from merge_commit on a separate branch and PR. Audit development-only data and target contracts without training, model comparison, backtest, historical-OOS reuse or protected-holdout access.
```
