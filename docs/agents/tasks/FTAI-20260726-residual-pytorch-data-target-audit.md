---
task_id: FTAI-20260726-residual-pytorch-data-target-audit
status: completed
branch: feat/residual-pytorch-data-target-audit
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: 376
owned_paths:
  - .github/workflows/residual-pytorch-data-target-audit.yml
  - ai_platform/experimental_model_research/residual-pytorch-data-target-audit-contract-v1.json
  - ai_platform/scripts/residual_pytorch_data_target_audit.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-data-target-audit.md
  - docs/ai_platform/RESIDUAL_PYTORCH_DATA_TARGET_AUDIT.md
  - tests/ai_platform/test_residual_pytorch_data_target_audit.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-runtime-smoke.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - docs/ai_platform/RESIDUAL_PYTORCH_DATA_TARGET_AUDIT.md
context_routes:
  - ai_platform/configs/freqai-residual-pytorch-research.example.json
  - ai_platform/experiments/residual-pytorch-research-v1.json
  - ai_platform/strategies/AiFrozenCandidateStrategy.py
---

# Residual PyTorch P2 data and target audit

## Goal

Freeze the development-only temporal and data geometry, prove the exact target look-forward semantics and define the historical feature/label evidence required before bounded model execution.

## Boundaries

This package used a deterministic synthetic close series only. It performed no exchange access, historical market-data read, FreqAI feature-matrix generation, training, model comparison, backtest, Hyperopt, historical-OOS reuse, protected-holdout access, liquidation-feature use, deployment, promotion or profitability scoring.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T21:07:00+02:00
head: 68faf30253d5670c4ab88c0b70abf7275aace96b
merge_commit: fee90dce7fadd5320d7279a51e45dc91026e903f
branch: feat/residual-pytorch-data-target-audit
pr: 376
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-runtime-smoke.md
  - docs/ai_platform/RESIDUAL_PYTORCH_RESEARCH_ARCHITECTURE.md
  - ai_platform/configs/freqai-residual-pytorch-research.example.json
  - ai_platform/experiments/residual-pytorch-research-v1.json
  - ai_platform/strategies/AiFrozenCandidateStrategy.py
owned_paths:
  - .github/workflows/residual-pytorch-data-target-audit.yml
  - ai_platform/experimental_model_research/residual-pytorch-data-target-audit-contract-v1.json
  - ai_platform/scripts/residual_pytorch_data_target_audit.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-data-target-audit.md
  - docs/ai_platform/RESIDUAL_PYTORCH_DATA_TARGET_AUDIT.md
  - tests/ai_platform/test_residual_pytorch_data_target_audit.py
proven:
  - P1 implementation merged as b51b8850db32e0050b9fa876dd141a49c0cf68c5 and its closeout merged as 41c04518cdb67bb2f7d70916ab4dd396d233a8a9.
  - P2 used only a deterministic synthetic close series and forbade market data, training, backtesting, consumed historical OOS, protected holdout and liquidation features.
  - The frozen development window is 2025-12-01T00:00:00Z through 2026-05-01T00:00:00Z exclusive.
  - Strategy target semantics use future offsets t+1 through t+12.
  - PR 376 squash-merged as fee90dce7fadd5320d7279a51e45dc91026e903f from exact head 68faf30253d5670c4ab88c0b70abf7275aace96b with exactly the six declared owned paths and no review blocker.
  - Final exact-head Residual PyTorch Data Target Audit 30215725189, AI Platform CI 30215725190, zizmor 30215725208 and Freqtrade CI 30215725203 succeeded.
derived:
  - The honest P2 audit outcome is audit_inconclusive because historical feature and label evidence was not authorized.
  - P3 remains request-gated and cannot infer the unresolved historical evidence from this synthetic audit.
unknown:
  - Exact FreqAI-expanded feature count and historical NaN, outlier and label distributions.
conflicts: []
first_failure:
  marker: CHECKPOINT_PATH_BLOB_MISMATCH
  evidence: Earlier reconstruction mapped the auditor blob into the task path, so checkpoint validation stopped before audit execution; the task Markdown was restored before successful exact-head validation.
rejected_hypotheses:
  - Infer the expanded feature count from static source declarations.
  - Download exchange candles or reuse historical data without separate authorization.
  - Use consumed historical OOS or the protected holdout for inspection.
  - Train, compare or promote models during P2.
  - Treat skipped runtime steps after the earlier checkpoint failure as an audit-model failure.
changed_paths:
  - .github/workflows/residual-pytorch-data-target-audit.yml
  - ai_platform/experimental_model_research/residual-pytorch-data-target-audit-contract-v1.json
  - ai_platform/scripts/residual_pytorch_data_target_audit.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-data-target-audit.md
  - docs/ai_platform/RESIDUAL_PYTORCH_DATA_TARGET_AUDIT.md
  - tests/ai_platform/test_residual_pytorch_data_target_audit.py
validation:
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-residual-pytorch-data-target-audit.md --require-checkpoint
    result: PASS
    evidence: Compact checkpoint validated locally against GOVERNANCE_CONTRACT v1 before implementation publication.
  - command: Residual PyTorch Data Target Audit 30215725189
    result: PASS
    evidence: Exact-head run 17 completed contract, synthetic target semantics and fail-closed checks with audit_inconclusive.
  - command: AI Platform CI 30215725190
    result: PASS
    evidence: Exact-head run 1668 completed successfully.
  - command: Freqtrade CI 30215725203
    result: PASS
    evidence: Exact-head run 2016 passed pre-commit, documentation, Python 3.11 through 3.14, coverage, distribution build and CI Gate.
  - command: zizmor 30215725208
    result: PASS
    evidence: Exact-head run 1879 completed successfully.
blockers: []
next_action: Start a separate request-gated P3 bounded M1 execution task only after explicit authorization; keep feature, target, strategy, pair universe, timeframes, fees, training windows and evaluation windows identical across LightGBM, seeded MLP and residual MLP.
```
