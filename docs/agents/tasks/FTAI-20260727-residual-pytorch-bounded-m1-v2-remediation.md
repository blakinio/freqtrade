---
task_id: FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation
status: active
branch: fix/residual-pytorch-bounded-m1-v2-volume-change
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: 540
owned_paths:
  - docs/agents/tasks/FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation.md
  - ai_platform/strategies/AiFrozenCandidateStrategyV2.py
  - ai_platform/experimental_model_research/residual-pytorch-bounded-m1-execution-contract-v2.json
  - ai_platform/scripts/residual_pytorch_bounded_m1_v2_execution.py
  - ai_platform/scripts/residual_pytorch_bounded_m1_v2_run_request.py
  - ai_platform/experiments/residual-pytorch-m1-data-audit-v2.json
  - ai_platform/experiments/residual-pytorch-m1-lightgbm-v2.json
  - ai_platform/experiments/residual-pytorch-m1-seeded-mlp-v2.json
  - ai_platform/experiments/residual-pytorch-m1-residual-mlp-v2.json
  - tests/ai_platform/test_residual_pytorch_bounded_m1_execution.py
  - tests/ai_platform/test_residual_pytorch_bounded_m1_v2_remediation.py
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
  - .github/workflows/residual-pytorch-bounded-m1-v2-request-generator.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
  - docs/ai_platform/RESIDUAL_PYTORCH_BOUNDED_M1_EXECUTION.md
search_first:
  - current develop and open ownership on residual PyTorch bounded M1
  - guarded exact-one-file execution and verified pre-May cache contracts
---

# Residual PyTorch bounded M1 v2 finite-volume remediation

## Goal

Retire the failed v1 feature contract and complete the same bounded development-only matrix audit and three-model comparison under a versioned v2 contract that changes only `%-volume-change`.

## Authorization

The user explicitly authorized autonomous continuation to completion on 2026-07-27. V2 may replace the undefined prior-volume percentage change with the finite symmetric formula `2*(current-previous)/(abs(current)+abs(previous))`, using `0` when the denominator is zero or the result is non-finite. For non-negative market volume the result is bounded to `[-2, 2]`.

All targets, thresholds, models, model parameters, pairs, timeframes, fees, seeds, temporal boundaries, execution counts, the consumed May-June historical OOS prohibition, protected final holdout prohibition, Phase 6 isolation, no-winner-selection rule and no-profitability/superiority claims remain unchanged.

V1 is retired and must not be modified or rerun. Real v2 execution still requires a separate PR adding exactly the canonical v2 request file, and that trigger PR must be closed without merge after terminal evidence collection.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T22:00:00Z
head: 8d0cc85d06edb8dd003dcbea47f406b01a5bdb3b
branch: fix/residual-pytorch-bounded-m1-v2-volume-change
pr: 540
status: validating
context_routes:
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
  - .github/workflows/residual-pytorch-bounded-m1-v2-request-generator.yml
owned_paths:
  - docs/agents/tasks/FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation.md
  - ai_platform/strategies/AiFrozenCandidateStrategyV2.py
  - ai_platform/experimental_model_research/residual-pytorch-bounded-m1-execution-contract-v2.json
  - ai_platform/scripts/residual_pytorch_bounded_m1_v2_execution.py
  - ai_platform/scripts/residual_pytorch_bounded_m1_v2_run_request.py
  - ai_platform/experiments/residual-pytorch-m1-data-audit-v2.json
  - ai_platform/experiments/residual-pytorch-m1-lightgbm-v2.json
  - ai_platform/experiments/residual-pytorch-m1-seeded-mlp-v2.json
  - ai_platform/experiments/residual-pytorch-m1-residual-mlp-v2.json
  - tests/ai_platform/test_residual_pytorch_bounded_m1_execution.py
  - tests/ai_platform/test_residual_pytorch_bounded_m1_v2_remediation.py
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
  - .github/workflows/residual-pytorch-bounded-m1-v2-request-generator.yml
proven:
  - V1 run 30299203871 passed request and data gates but failed closed because %-volume-change contained infinity for both pairs.
  - PR 540 versions only the finite volume feature and its bounded infrastructure; no canonical request is present.
  - The finite zero-volume regression and the complete lightweight AI platform suite passed with 792 tests and 66 skips.
  - AI Platform CI 30308972544 passed tests, Ruff, format, codespell and JSON validation after applying its exact reported fixes.
  - The standard AI Platform workflow was restored byte-for-byte with read-only permissions after diagnostics.
derived:
  - Symmetric volume change avoids division by prior volume alone and is finite at zero-volume transitions.
  - The verified pre-May cache is data-only and may be reused because pair universe, timeframes and temporal geometry are unchanged; coverage gates still rerun before fit.
unknown:
  - Whether the final exact-head infrastructure CI passes after the restored workflow and checkpoint update.
  - Whether the exact expanded v2 matrix passes all finite, target and cross-pair identity gates.
  - Whether all three unchanged comparator models complete exactly once.
conflicts: []
first_failure:
  marker: EXPANDED_VOLUME_CHANGE_INFINITY
  evidence: V1 artifact 8667673779 preserved the exact BTC/USDT and ETH/USDT training exceptions.
rejected_hypotheses:
  - Missing or late pre-May data caused v1 failure; pair and combined coverage verification passed.
  - A comparator model caused v1 failure; all three were skipped before fit.
  - The v2 lightweight suite requires NumPy or Pandas; the regression was rewritten dependency-light and the full suite passed.
changed_paths:
  - versioned v2 strategy, contract, manifests, validators, tests and guarded workflows; no canonical request
validation:
  - command: AI Platform CI 30308972544
    result: PASS
    evidence: Tests, Ruff, format, codespell and JSON validation all passed before restoring the standard workflow.
  - command: final exact-head PR 540 CI
    result: NOT_RUN
    evidence: The final checkpoint commit has not completed its CI yet.
blockers: []
next_action: Validate the final exact head of PR 540 with AI Platform CI, Freqtrade CI and zizmor; merge only if all pass, then generate and execute the separate exact-one-file v2 request.
```
