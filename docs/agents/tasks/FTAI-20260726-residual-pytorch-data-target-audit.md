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
updated_at: 2026-07-26T20:45:00+02:00
head: b48a7bd778d4a659de88c8a66ab33a2ecc76b15e
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
  - P2 architecture requires a development-only window, target alignment, feature count, NaN/outlier and label-distribution evidence, and liquidation exclusion.
  - Existing geometry defines training 20251201-20260228 and tuning/prediction-only coverage 20260301-20260430.
  - Consumed historical OOS 20260501-20260630 and protected holdout 20260801-20260930 remain forbidden.
  - Strategy target source uses shift(-12) followed by rolling(12), producing future offsets t+1 through t+12.
  - Current authorization permits deterministic synthetic target validation but not historical market-data access.
  - PR 376 is reconstructed as a six-file single commit on develop 11ad81870c0b199b0739af9dcfa239cb32d455cc.
derived:
  - The bounded P2 window is 2025-12-01T00:00:00Z through 2026-05-01T00:00:00Z exclusive.
  - Actual FreqAI feature count and historical distributions cannot be honestly reported from static source alone.
  - The only valid current outcome is audit_inconclusive even when synthetic semantics pass.
unknown:
  - Exact FreqAI-expanded feature count on the frozen historical matrix.
  - Historical feature NaN and outlier distributions.
  - Historical target distribution and pair/timeframe coverage.
conflicts: []
first_failure:
  marker: CHECKPOINT_PATH_BLOB_MISMATCH
  evidence: Final reconstruction mapped the auditor blob into the task path, so checkpoint validation stopped before any audit execution.
  correction: Restore the task Markdown, retain the six-file scope, and rerun exact-head governance and CI validation.
rejected_hypotheses:
  - Infer the expanded feature count from source declarations.
  - Download exchange candles or reuse local historical data without a separate authorization.
  - Use consumed historical OOS or the protected holdout for data-quality inspection.
  - Train or compare models during P2.
  - Treat skipped runtime steps after checkpoint failure as model or audit failures.
changed_paths:
  - .github/workflows/residual-pytorch-data-target-audit.yml
  - ai_platform/experimental_model_research/residual-pytorch-data-target-audit-contract-v1.json
  - ai_platform/scripts/residual_pytorch_data_target_audit.py
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-data-target-audit.md
  - docs/ai_platform/RESIDUAL_PYTORCH_DATA_TARGET_AUDIT.md
  - tests/ai_platform/test_residual_pytorch_data_target_audit.py
validation:
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-residual-pytorch-data-target-audit.md --require-checkpoint
    result: NOT_RUN
    evidence: Awaiting the corrected exact-head workflow after task Markdown restoration.
  - command: Residual PyTorch Data Target Audit exact-head workflow
    result: NOT_RUN
    evidence: Awaiting corrected task checkpoint validation before audit execution.
blockers:
  - Historical feature count and distributions remain intentionally unavailable under the current authorization.
next_action: Publish the corrected six-file tree, require exact-head checkpoint, audit, Ruff, format, mypy, documentation, core tests and CI Gate success, then update this checkpoint with final evidence.
```
