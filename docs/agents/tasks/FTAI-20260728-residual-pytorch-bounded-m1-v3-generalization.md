---
task_id: FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization
status: active
branch: docs/residual-pytorch-m1-v3-checkpoint-contract-20260728
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 648
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
updated_at: 2026-07-28T21:29:00+02:00
head: 5b0c66a1167fbcf84aef95908234ea35451d9ebf
branch: docs/residual-pytorch-m1-v3-checkpoint-contract-20260728
pr: 648
status: ready
context_routes:
  - .github/workflows/residual-pytorch-bounded-m1-v3-request-generator.yml
  - .github/workflows/residual-pytorch-bounded-m1-v3-generalization.yml
  - ai_platform/scripts/residual_pytorch_bounded_m1_v3_generalization.py
  - tests/ai_platform/test_residual_pytorch_bounded_m1_v3_generalization.py
owned_paths:
  - docs/agents/tasks/FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization.md
  - ai_platform/scripts/residual_pytorch_bounded_m1_v3_generalization.py
  - tests/ai_platform/test_residual_pytorch_bounded_m1_v3_generalization.py
proven:
  - PR 627 merged the guarded v3 request generator as 31c61fdab351521c275687e4751682ef935407f9.
  - Marker PR 628 generated the canonical exact-one-file request and closed without merge.
  - Request PR 629 triggered guarded run 30360316606 and closed without merge after the fail-closed result.
  - Request validation and exact authorized pre-May Kraken coverage passed for SOL/USDT and XRP/USDT on 15m, 1h and 4h.
  - The matrix audit passed with 272 finite transformed features and terminal-v2 role-normalized hash c65ec5f29963f1bb541f1c5416b52a4be8bfe2a1328a04577c17eea197d2945c.
  - Audit artifact 8689818122 has digest sha256:faa63b0dc0688540e73909c88abdbff6a672cb38a0c72280325018d75dc56a3a.
  - LightGBM artifact 8689818655 has digest sha256:66e031ae1989364c4d877c259196c9c5fd6d1ecaa8457e1897934a3367bc1dbd and contains non-empty per-pair lightgbm_evals_result evidence.
  - Job 90288767489 failed because v3 delegated to a version-coupled validator branch that treated the v3 LightGBM track as PyTorch.
  - PR 648 merged the v3 model-identity evidence fix as 5b0c66a1167fbcf84aef95908234ea35451d9ebf.
  - Final PR 648 head f9dd925685887c0d0259ee60156253e142697e25 passed AI Platform CI 30390614107.
  - Final PR 648 head f9dd925685887c0d0259ee60156253e142697e25 passed zizmor 30390611913.
  - Final PR 648 head f9dd925685887c0d0259ee60156253e142697e25 passed Freqtrade CI 30390612276, including Python 3.11-3.14, coverage, distributions and CI Gate.
  - Marker PR 655 run 30391885196 stopped before request generation because the checkpoint used non-canonical enum values.
derived:
  - The failed model-evidence classification did not invalidate data coverage, matrix geometry or actual LightGBM execution evidence.
  - V3-specific evidence validation remains fail-closed while selecting the required evidence shape from frozen model identity.
  - Normalizing checkpoint enum values changes governance metadata only and does not change experimental authorization.
unknown:
  - Whether a fresh exact-one-file request completes LightGBM, seeded MLP and residual MLP exactly once.
  - Terminal descriptive v3 diagnostics remain unknown and unauthorized for winner selection or promotion.
conflicts: []
first_failure:
  marker: V3_CHECKPOINT_ENUM_CONTRACT
  evidence: Marker run 30391885196 rejected status ready_to_merge and validation result FAIL_CLOSED before request generation.
rejected_hypotheses:
  - The request generator changed model or data scope; it stopped before installing numeric dependencies or writing a request.
  - The request branch contains a generated request; it remains reset to merge commit 5b0c66a1167fbcf84aef95908234ea35451d9ebf.
changed_paths:
  - docs/agents/tasks/FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization.md
validation:
  - command: guarded run 30360316606
    result: FAIL
    evidence: Request, data and matrix audit passed; model evidence validation failed closed on version-coupled LightGBM classification.
  - command: AI Platform CI 30390614107
    result: PASS
    evidence: Compile, AI platform tests, Ruff lint, Ruff format, codespell and JSON validation passed on final PR 648 head.
  - command: zizmor 30390611913
    result: PASS
    evidence: GitHub Actions security analysis passed on final PR 648 head.
  - command: Freqtrade CI 30390612276
    result: PASS
    evidence: Pre-commit, docs, Python 3.11-3.14, coverage, distributions and CI Gate passed on final PR 648 head.
  - command: request generator 30391885196
    result: FAIL
    evidence: Exact marker scope passed; checkpoint enum validation failed before request generation.
blockers: []
next_action: Merge the documentation-only checkpoint normalization, reset the request branch to that merge SHA and open a fresh exact-one-file marker PR.
```
