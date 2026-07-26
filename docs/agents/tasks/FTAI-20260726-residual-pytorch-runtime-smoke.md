---
task_id: FTAI-20260726-residual-pytorch-runtime-smoke
status: active
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

This task authorizes bounded synthetic fitting only. It performs no exchange download, market-data training, backtest, Hyperopt, feature search, historical-OOS use, protected-holdout use, deployment, promotion or profitability scoring.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T14:20:00+02:00
head: d633f6e943d95856c1049e700aa7eaaf924e7cb8
branch: test/residual-pytorch-runtime-smoke
pr: 355
status: validating
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
  - P0 merged as 1ed82158374684aa9a01b3d98e172fcca84ee88d.
  - Official FreqaiModelResolver loading succeeded for ResidualPyTorchRegressor.
  - CPU construct, forward, fit, predict, save, load and repeated predict succeeded.
  - Runtime outcome is runtime_supported on Python 3.12.13 and torch 2.13.0+cu130.
  - The frozen residual network contains 199561 parameters.
  - Same-seed repeated training produced identical parameters and predictions.
  - Predictions before and after checkpoint restoration were identical.
  - Checkpoint metadata bound architecture, input dimension, output dimension, parameter count and seed.
  - Multiple targets, zero features, row mismatch, missing checkpoint, invalid learning rate and continual learning failed closed.
  - CUDA was not available and was explicitly reported as skipped.
  - Synthetic rows began on 2025-01-01 and remained before all protected windows.
  - No market data, backtest, historical OOS or protected holdout was used.
  - AI Platform CI 30201260440 run 1526 succeeded.
  - Residual PyTorch Runtime Smoke 30201260452 run 17 succeeded.
  - Experimental Model Runtime Smoke 30201260450 run 126 and zizmor 30201260449 run 1707 succeeded.
  - Freqtrade CI 30201260454 run 1842 including pre-commit, mypy, Python 3.11-3.14 and CI Gate succeeded.
derived:
  - ResidualPyTorchRegressor is technically supported for the bounded P1 lifecycle only.
  - P1 provides no evidence about model quality, trading performance or production readiness.
  - P2 data and target audit must remain a separate development-only task.
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
  - Treat unavailable CUDA as a failed CPU lifecycle.
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
  - command: Residual PyTorch Runtime Smoke 30201260452
    result: PASS
    evidence: Run 17 completed resolver, CPU lifecycle, reproducibility, save-load and fail-closed checks with runtime_supported.
  - command: AI Platform CI 30201260440
    result: PASS
    evidence: Run 1526 passed tests, Ruff, format, codespell and JSON validation.
  - command: Experimental Model Runtime Smoke 30201260450
    result: PASS
    evidence: Run 126 passed the canonical heavy-runtime smoke.
  - command: Freqtrade CI 30201260454
    result: PASS
    evidence: Run 1842 passed pre-commit, mypy, documentation, Python 3.11-3.14 matrices, distribution build and CI Gate.
  - command: zizmor 30201260449
    result: PASS
    evidence: Run 1707 completed successfully.
blockers:
  - Final exact-head CI is required after checkpoint refresh and reconstruction on current develop.
next_action: Reconstruct the exact eight-path P1 diff on current develop, run final exact-head workflows, and squash-merge PR 355 only if mergeable, review-clean and fully green.
```
