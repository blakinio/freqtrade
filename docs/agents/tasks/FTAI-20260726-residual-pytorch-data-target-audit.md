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

This package uses a deterministic synthetic close series only. It performs no exchange access, historical market-data read, FreqAI feature-matrix generation, training, model comparison, backtest, Hyperopt, historical-OOS reuse, protected-holdout access, liquidation-feature use, deployment, promotion or profitability scoring.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T21:08:00+02:00
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
  - PR 376 merged exact head 68faf30253d5670c4ab88c0b70abf7275aace96b as fee90dce7fadd5320d7279a51e45dc91026e903f with exactly six intended paths.
  - P2 used only a deterministic synthetic close series and no market data, exchange download, training, backtest, historical OOS, protected holdout or liquidation features.
  - The frozen development window is 2025-12-01T00:00:00Z through 2026-05-01T00:00:00Z exclusive.
  - Target semantics are mean(close[t+1] through close[t+12]) divided by close[t] minus one.
  - Synthetic alignment error was 0.0 with 11 leading and 12 trailing unavailable rows.
  - Only future offsets t+1 through t+12 influenced the numerator; past close and t+13 did not.
  - The bounded result is audit_inconclusive because historical feature-matrix and label-distribution evidence was deliberately unavailable.
  - Final exact-head Residual PyTorch Data Target Audit 30215725189 run 17 succeeded.
  - Final exact-head AI Platform CI 30215725190 run 1668, zizmor 30215725208 run 1879 and Freqtrade CI 30215725203 run 2016 succeeded.
derived:
  - P2 proves the static contract and synthetic target geometry only; it provides no market-data quality, predictive-quality, trading-performance or promotion evidence.
  - Any historical feature-matrix measurement must be a separately authorized development-only task that excludes consumed OOS and the protected holdout.
unknown:
  - Exact FreqAI-expanded feature count and historical NaN, outlier, coverage and label distributions.
conflicts: []
first_failure:
  marker: CHECKPOINT_PATH_BLOB_MISMATCH
  evidence: An earlier reconstruction mapped the auditor blob into the task path, so checkpoint validation stopped before audit execution.
  correction: Restored the task Markdown, retained the six-file scope and reran checkpoint, audit and full exact-head CI successfully.
rejected_hypotheses:
  - Infer the expanded feature count from static source declarations.
  - Download exchange candles or reuse historical data without separate authorization.
  - Use consumed historical OOS or the protected holdout for inspection.
  - Train, compare, backtest or promote models during P2.
  - Treat unavailable historical evidence as audit_supported.
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
    evidence: Exact-head workflow run 30215725189 validated the compact checkpoint before executing the audit.
  - command: Residual PyTorch Data Target Audit 30215725189
    result: PASS
    evidence: Run 17 passed four focused tests, Ruff, format and the bounded audit with audit_inconclusive and all forbidden evidence flags false.
  - command: AI Platform CI 30215725190
    result: PASS
    evidence: Run 1668 passed compile, tests, Ruff, format, codespell and JSON validation.
  - command: Freqtrade CI 30215725203
    result: PASS
    evidence: Run 2016 passed pre-commit, documentation, Python 3.11 through 3.14, coverage, distribution build and CI Gate.
  - command: zizmor 30215725208
    result: PASS
    evidence: Run 1879 completed successfully.
blockers: []
next_action: Prepare a separate authorization-only task for development-window historical feature-matrix measurement; do not access market data, train or backtest until that task is explicitly approved.
```
