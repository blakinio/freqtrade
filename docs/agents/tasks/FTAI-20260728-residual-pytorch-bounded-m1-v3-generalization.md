---
task_id: FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization
status: active
branch: feat/residual-pytorch-bounded-m1-v3-generalization
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 0
owned_paths:
  - docs/agents/tasks/FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization.md
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_V3_GENERALIZATION.md
  - ai_platform/experimental_model_research/residual-pytorch-bounded-m1-generalization-contract-v3.json
  - ai_platform/configs/freqai-residual-pytorch-m1-generalization-v3-data-audit.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-generalization-v3-lightgbm.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-generalization-v3-seeded-mlp.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-generalization-v3-residual-mlp.example.json
  - ai_platform/experiments/residual-pytorch-m1-generalization-v3-data-audit.json
  - ai_platform/experiments/residual-pytorch-m1-generalization-v3-lightgbm.json
  - ai_platform/experiments/residual-pytorch-m1-generalization-v3-seeded-mlp.json
  - ai_platform/experiments/residual-pytorch-m1-generalization-v3-residual-mlp.json
  - ai_platform/freqaimodels/ResidualPyTorchM1V3DataAuditRegressor.py
  - ai_platform/scripts/residual_pytorch_bounded_m1_v3_generalization.py
  - ai_platform/scripts/residual_pytorch_bounded_m1_v3_run_request.py
  - .github/workflows/residual-pytorch-bounded-m1-v3-generalization.yml
  - tests/ai_platform/test_residual_pytorch_bounded_m1_v3_generalization.py
required_reads:
  - AGENTS.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_EXECUTION.md
  - docs/agents/tasks/FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation.md
search_first:
  - current develop and open ownership for bounded M1 or pair-generalization work
  - current v2 terminal evidence and exact role-normalized feature identity
---

# Residual PyTorch bounded M1 v3 pair generalization

## Goal

Execute one separately versioned, development-only SOL/XRP cohort using the exact v2
strategy geometry and the three unchanged frozen comparator models.

## Authorization

The user authorized autonomous continuation on 2026-07-28 after v2 terminal closure.
This task may add only the fixed `SOL/USDT` + `XRP/USDT` cohort and the infrastructure
needed to audit and execute it.

Consumed May-June historical OOS and the protected August-September final holdout remain
forbidden. Hyperopt, retuning, threshold changes, feature changes, liquidation features,
winner selection, promotion, profitability/superiority claims and live trading remain
forbidden.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T12:30:00+02:00
head: c0fba2ddf90d145211ca42fdea61ffbfe73d7185
branch: feat/residual-pytorch-bounded-m1-v3-generalization
pr: 0
status: implementing
context_routes:
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_V3_GENERALIZATION.md
  - docs/agents/tasks/FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation.md
owned_paths:
  - docs/agents/tasks/FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization.md
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_V3_GENERALIZATION.md
  - ai_platform/experimental_model_research/residual-pytorch-bounded-m1-generalization-contract-v3.json
  - ai_platform/configs/freqai-residual-pytorch-m1-generalization-v3-data-audit.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-generalization-v3-lightgbm.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-generalization-v3-seeded-mlp.example.json
  - ai_platform/configs/freqai-residual-pytorch-m1-generalization-v3-residual-mlp.example.json
  - ai_platform/experiments/residual-pytorch-m1-generalization-v3-data-audit.json
  - ai_platform/experiments/residual-pytorch-m1-generalization-v3-lightgbm.json
  - ai_platform/experiments/residual-pytorch-m1-generalization-v3-seeded-mlp.json
  - ai_platform/experiments/residual-pytorch-m1-generalization-v3-residual-mlp.json
  - ai_platform/freqaimodels/ResidualPyTorchM1V3DataAuditRegressor.py
  - ai_platform/scripts/residual_pytorch_bounded_m1_v3_generalization.py
  - ai_platform/scripts/residual_pytorch_bounded_m1_v3_run_request.py
  - .github/workflows/residual-pytorch-bounded-m1-v3-generalization.yml
  - tests/ai_platform/test_residual_pytorch_bounded_m1_v3_generalization.py
proven:
  - V2 guarded run 30340242201 completed request, data, audit and all three model jobs successfully.
  - V2 used BTC/USDT and ETH/USDT with 272 expanded and transformed features.
  - V2 role-normalized feature-name SHA-256 is c65ec5f29963f1bb541f1c5416b52a4be8bfe2a1328a04577c17eea197d2945c.
  - V2 trigger PR 580 was closed without merge.
  - V2 cleanup PR 602 merged as 856dbfcc0dea1d5e39fdddf0d65da2e24bb6adbb.
  - Current develop preflight head is c0fba2ddf90d145211ca42fdea61ffbfe73d7185.
  - No open bounded-M1 or pair-generalization PR owns the v3 paths.
derived:
  - A fixed two-pair cohort preserves one-primary/one-correlated feature geometry.
  - SOL/USDT and XRP/USDT isolate pair-cohort generalization from feature-count growth.
  - Exact equality to the v2 role-normalized feature hash can fail closed before model fitting.
unknown:
  - Whether exact authorized pre-May Kraken coverage exists for both v3 pairs and all three timeframes.
  - Whether both v3 matrices retain exactly 272 finite features and the v2 normalized identity.
  - Whether each frozen model completes exactly once on the v3 cohort.
  - The terminal descriptive diagnostics and trading outcomes for the v3 cohort.
conflicts: []
first_failure:
  marker: NONE
  evidence: No v3 execution has been requested.
rejected_hypotheses:
  - Add BTC, ETH, SOL and XRP to one correlation list; that would increase feature geometry and confound the test.
  - Reuse May-June historical OOS or the protected final holdout; both remain forbidden.
  - Select LightGBM from v2 descriptive profit; v2 did not authorize winner selection.
changed_paths: []
validation:
  - command: implementation PR exact-head CI
    result: NOT_RUN
    evidence: Infrastructure has not yet been committed.
blockers: []
next_action: Commit the v3 infrastructure, open its PR, complete exact-head CI and merge before creating the separate exact-one-file execution request.
```
