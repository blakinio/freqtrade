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
updated_at: 2026-07-27T21:30:00Z
head: 2e6fc23f5f88008186403c8fff704ad3a7dbb1a0
branch: fix/residual-pytorch-bounded-m1-v2-volume-change
pr: 540
status: validating
context_routes:
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-residual-pytorch-bounded-m1-execution.md
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
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
proven:
  - V1 guarded run 30299203871 passed request and data gates but failed closed because %-volume-change contained infinity for both pairs.
  - V1 PR 517 was closed without merge and terminal evidence was merged through PR 534 as 351567d57760305b992fb1e441205dc32890dc2a.
  - No open pull request owned the v2 remediation paths at task start.
  - PR 540 versions the strategy, contract, manifests, validators, tests and guarded workflow without adding a run request.
derived:
  - Symmetric volume change avoids division by prior volume alone and is finite at zero-volume transitions.
  - The verified pre-May cache is data-only and may be reused because pair universe, timeframes and temporal geometry are unchanged; coverage gates still rerun before fit.
unknown:
  - Whether exact-head infrastructure CI passes.
  - Whether the exact expanded v2 matrix passes all finite, target and cross-pair identity gates.
  - Whether all three unchanged comparator models complete exactly once.
conflicts: []
first_failure:
  marker: EXPANDED_VOLUME_CHANGE_INFINITY
  evidence: V1 artifact 8667673779 preserved the exact BTC/USDT and ETH/USDT training exceptions.
rejected_hypotheses:
  - Missing or late pre-May data caused v1 failure; pair and combined coverage verification passed.
  - A comparator model caused v1 failure; all three were skipped before fit.
changed_paths:
  - versioned v2 infrastructure only; no canonical request
validation:
  - command: exact-head PR 540 CI
    result: NOT_RUN
    evidence: Final infrastructure head is still being assembled.
blockers: []
next_action: Remove temporary bootstrap files, validate and merge PR 540 only if exact-head AI Platform CI, Freqtrade CI and zizmor pass, then generate a separate exact-one-file v2 request and collect terminal evidence.
```
