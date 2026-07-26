---
task_id: FTAI-20260726-residual-pytorch-data-target-audit
status: active
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
updated_at: 2026-07-26T20:53:00+02:00
head: 55d62a78737f3da6207e4cc7afa21f7c257d34cc
branch: feat/residual-pytorch-data-target-audit
pr: 376
status: validating
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
  - P2 uses only a deterministic synthetic close series and forbids market data, training, backtesting, consumed historical OOS, protected holdout and liquidation features.
  - The frozen development window is 2025-12-01T00:00:00Z through 2026-05-01T00:00:00Z exclusive.
  - Strategy target semantics use future offsets t+1 through t+12.
  - PR 376 contains exactly the six declared owned paths and the task Markdown is restored at its correct path.
  - Residual PyTorch Data Target Audit run 30215214117, AI Platform CI run 30215214118 and zizmor run 30215214124 passed on code head 55d62a78737f3da6207e4cc7afa21f7c257d34cc.
derived:
  - The only honest current audit outcome is audit_inconclusive because historical feature and label evidence is not authorized.
unknown:
  - Exact FreqAI-expanded feature count and historical NaN, outlier and label distributions.
  - Final Freqtrade CI outcome for the live checkpoint-updated PR head.
conflicts: []
first_failure:
  marker: CHECKPOINT_PATH_BLOB_MISMATCH
  evidence: Earlier reconstruction mapped the auditor blob into the task path, so checkpoint validation stopped before audit execution; the task Markdown was restored before run 30215214117 passed.
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
    evidence: Compact checkpoint validates locally against GOVERNANCE_CONTRACT v1 before publication.
  - command: Residual PyTorch Data Target Audit on code head 55d62a78737f3da6207e4cc7afa21f7c257d34cc
    result: PASS
    evidence: Workflow run 30215214117 completed successfully.
  - command: AI Platform CI on code head 55d62a78737f3da6207e4cc7afa21f7c257d34cc
    result: PASS
    evidence: Workflow run 30215214118 completed successfully.
  - command: GitHub Actions Security Analysis with zizmor on code head 55d62a78737f3da6207e4cc7afa21f7c257d34cc
    result: PASS
    evidence: Workflow run 30215214124 completed successfully.
  - command: Freqtrade CI on live checkpoint-updated PR head
    result: NOT_RUN
    evidence: Exact-head workflow must complete after this checkpoint-only update.
blockers: []
next_action: Verify all required workflows on the current live PR 376 head after this checkpoint-only update; if they pass and the PR remains mergeable, merge PR 376 with expected_head_sha, verify develop, and close the task record with a compact checkpoint update.
```
