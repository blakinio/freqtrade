---
task_id: FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization
status: active
branch: fix/residual-pytorch-m1-v3-lightgbm-evidence-20260728
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
updated_at: 2026-07-28T21:08:00+02:00
head: 3da7dd224cc9245d21dda671f36ac2c3079fc9fd
branch: fix/residual-pytorch-m1-v3-lightgbm-evidence-20260728
pr: 648
status: ready_to_merge
context_routes:
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
  - PR 648 validates v3 training evidence by frozen freqai_model identity and adds a regression for empty PyTorch scalar events with valid LightGBM history.
  - Exact implementation head 3da7dd224cc9245d21dda671f36ac2c3079fc9fd passed AI Platform CI 30389439298.
  - Exact implementation head 3da7dd224cc9245d21dda671f36ac2c3079fc9fd passed zizmor 30389438503.
  - Exact implementation head 3da7dd224cc9245d21dda671f36ac2c3079fc9fd passed Freqtrade CI 30389438607, including pre-commit, docs, Python 3.11-3.14, coverage, distributions and CI Gate.
derived:
  - The failed evidence classification did not invalidate data coverage, matrix geometry or the actual LightGBM execution evidence.
  - V3-specific evidence validation remains fail-closed while selecting the required evidence shape from frozen model identity.
  - The checkpoint commit changes documentation only; the validated implementation and regression-test bytes remain those from head 3da7dd224cc9245d21dda671f36ac2c3079fc9fd.
unknown:
  - Whether a fresh exact-one-file request completes LightGBM, seeded MLP and residual MLP exactly once.
  - Terminal descriptive v3 diagnostics remain unknown and unauthorized for winner selection or promotion.
conflicts: []
first_failure:
  marker: V3_LIGHTGBM_EVIDENCE_CLASSIFICATION
  evidence: Run 30360316606 emitted SOL/USDT PyTorch train/test loss history is absent after valid LightGBM evaluation history had been written.
rejected_hypotheses:
  - LightGBM produced no evaluation history; artifact 8689818655 contains non-empty lightgbm_evals_result for both pairs.
  - Data coverage or feature identity failed; all prerequisite gates passed before model evidence validation.
changed_paths:
  - ai_platform/scripts/residual_pytorch_bounded_m1_v3_generalization.py
  - tests/ai_platform/test_residual_pytorch_bounded_m1_v3_generalization.py
  - docs/agents/tasks/FTAI-20260728-residual-pytorch-bounded-m1-v3-generalization.md
validation:
  - command: guarded run 30360316606
    result: FAIL_CLOSED
    evidence: Request, data and matrix audit passed; model evidence validation failed on version-coupled LightGBM classification.
  - command: AI Platform CI 30389439298
    result: PASS
    evidence: Compile, AI platform tests, Ruff lint, Ruff format, codespell and JSON validation passed.
  - command: zizmor 30389438503
    result: PASS
    evidence: GitHub Actions security analysis passed.
  - command: Freqtrade CI 30389438607
    result: PASS
    evidence: Pre-commit, docs, Python 3.11-3.14, coverage, distributions and CI Gate passed.
blockers: []
next_action: Merge PR 648, reset the request branch to the remediation merge SHA, generate a fresh canonical exact-one-file v3 request and execute it under the unchanged development-only guardrails.
```
