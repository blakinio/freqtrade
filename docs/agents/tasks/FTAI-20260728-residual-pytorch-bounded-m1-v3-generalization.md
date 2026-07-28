---
task_id: FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization
status: completed
branch: docs/close-residual-pytorch-m1-v3-20260728
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 660
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
  - .github/workflows/residual-pytorch-bounded-m1-v3-request-generator.yml
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
updated_at: 2026-07-28T22:22:00+02:00
head: 33c52fdd226c4bfcb54bc4278faf2629cb83c72f
branch: docs/close-residual-pytorch-m1-v3-20260728
pr: 660
status: ready
context_routes:
  - .github/workflows/residual-pytorch-bounded-m1-v3-generalization.yml
  - ai_platform/scripts/residual_pytorch_bounded_m1_v3_generalization.py
  - ai_platform/experimental_model_research/residual-pytorch-bounded-m1-generalization-contract-v3.json
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_V3_GENERALIZATION.md
owned_paths:
  - docs/agents/tasks/FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization.md
proven:
  - PR 627 merged the one-shot v3 request generator as 31c61fdab351521c275687e4751682ef935407f9.
  - PR 648 merged model-identity evidence validation as 5b0c66a1167fbcf84aef95908234ea35451d9ebf.
  - PR 656 merged checkpoint enum normalization as 6b7d3d9ea95104618f636ad4f08227c9c890324b.
  - Marker PR 658 generated the canonical request and closed without merge.
  - Request PR 660 used exact one-file head 33c52fdd226c4bfcb54bc4278faf2629cb83c72f and closed without merge.
  - Guarded workflow 30392428273 completed successfully.
  - AI Platform CI 30392428418, Freqtrade CI 30392428230 and zizmor 30392428590 passed on the request head.
  - Authorized Kraken coverage passed for SOL/USDT and XRP/USDT on 15m, 1h and 4h with exclusive stop 2026-05-01T00:00:00Z.
  - Matrix audit passed with 272 expanded and transformed features and normalized hash c65ec5f29963f1bb541f1c5416b52a4be8bfe2a1328a04577c17eea197d2945c.
  - LightGBM, seeded MLP and residual MLP each completed exactly once for both pairs with 6902 train rows, 1726 test rows and 272 features per pair.
  - Model-specific evidence passed using LightGBM evaluation history or PyTorch train and test scalar histories.
  - Each model produced 11126 valid development predictions from 11712 raw rows.
  - Consumed historical OOS and the protected final holdout were not used; winner selection and profitability claims remained disabled.
  - Request artifact 8701449950 has digest sha256:72fe5032ce7f1c7a416abf7457bb89e09117e37a1688450efc07910033ce8c01.
  - Audit artifact 8702664937 has digest sha256:ff5999071dcae21a67d58a4d59780c9425a5ecd249c82d6bef2b65bac76e9f9b.
  - Model artifacts 8702665878, 8702666748 and 8702667672 have recorded immutable SHA-256 digests in closed PR 660.
derived:
  - The authorized v3 pair-generalization execution objective is complete.
  - The remediation corrected evidence classification without changing data, feature, model, threshold or temporal scope.
  - Terminal diagnostics are descriptive development evidence and cannot support comparator selection, superiority or promotion.
unknown: []
conflicts: []
first_failure:
  marker: V3_RESOLVED_GUARD_FAILURES
  evidence: Initial LightGBM evidence classification and checkpoint enum failures were corrected by merged PRs 648 and 656 before successful run 30392428273.
rejected_hypotheses:
  - The validator remediation changed model or experimental scope.
  - The successful run consumed May-June historical OOS or the protected final holdout.
  - Successful completion authorized winner selection, retuning, promotion or live execution.
changed_paths:
  - docs/agents/tasks/FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization.md
validation:
  - command: Residual PyTorch Bounded M1 V3 Generalization
    result: PASS
    evidence: Run 30392428273 passed request, data, matrix audit and all three frozen model jobs.
  - command: AI Platform CI
    result: PASS
    evidence: Run 30392428418 passed on exact request head 33c52fdd226c4bfcb54bc4278faf2629cb83c72f.
  - command: Freqtrade CI
    result: PASS
    evidence: Run 30392428230 passed on exact request head 33c52fdd226c4bfcb54bc4278faf2629cb83c72f.
  - command: GitHub Actions Security Analysis with zizmor
    result: PASS
    evidence: Run 30392428590 passed on exact request head 33c52fdd226c4bfcb54bc4278faf2629cb83c72f.
  - command: terminal artifact inspection
    result: PASS
    evidence: Audit and all three model packages contain successful summaries, model-specific training evidence and bounded development diagnostics.
blockers: []
next_action: Do not continue under this completed task; any winner selection, retuning, protected-holdout evaluation, promotion or live execution requires a separately authorized task.
```
