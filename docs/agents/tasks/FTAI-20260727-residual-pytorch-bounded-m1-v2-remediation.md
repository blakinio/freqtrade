---
task_id: FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation
status: completed
branch: docs/residual-pytorch-bounded-m1-v2-complete
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: 0
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
  - tests/ai_platform/test_residual_pytorch_bounded_m1_v2_cross_pair_identity.py
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

The user explicitly authorized autonomous continuation to completion on 2026-07-27 and repeated that authorization on 2026-07-28. V2 replaces the undefined prior-volume percentage change with the finite symmetric formula `2*(current-previous)/(abs(current)+abs(previous))`, using `0` when the denominator is zero or the result is non-finite. For non-negative market volume the result is bounded to `[-2, 2]`.

All targets, thresholds, models, model parameters, pairs, timeframes, fees, seeds, temporal boundaries, execution counts, the consumed May-June historical OOS prohibition, protected final holdout prohibition, Phase 6 isolation, no-winner-selection rule and no-profitability/superiority claims remained unchanged.

V1 is retired and must not be modified or rerun. The terminal v2 trigger PR was closed without merge after evidence collection. Any future pair expansion, retuning, protected evaluation or promotion requires a separate versioned task and contract.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T10:15:00Z
head: be8b86aa332dd6ef0813698a41e4cc33bfdc0f80
branch: docs/residual-pytorch-bounded-m1-v2-complete
pr: 0
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
  - tests/ai_platform/test_residual_pytorch_bounded_m1_v2_cross_pair_identity.py
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
proven:
  - V1 run 30299203871 failed closed on infinite %-volume-change values before any model fit.
  - PR 540 merged finite bounded v2 infrastructure as 7ce6f1ff20a59eff9d6ac904e20a15655f27d200.
  - PR 566 merged role-normalized cross-pair feature identity as a7add1dd079ee59a209f0eb41502a734def976f9.
  - PR 576 merged the governance-valid execution checkpoint as a5a03db4bf9ff0934d45c7e953162acf4302c685.
  - Generator run 30340077443 produced the canonical request; marker PR 579 was closed without merge.
  - PR 580 added exactly one request file at head be8b86aa332dd6ef0813698a41e4cc33bfdc0f80.
  - Guarded run 30340242201 passed exact request, checkpoint, infrastructure and BTC/ETH pre-May coverage gates.
  - The matrix audit passed with 272 expanded and transformed features, 8628 eligible rows per pair and finite train/test matrices.
  - Consumed May-June historical OOS and the protected final holdout were not used.
  - LightGBM, seeded MLP and residual MLP each executed exactly once and completed successfully.
  - Audit artifact 8682440939 has digest sha256:b51a1cf3f064e2e93ba12e04691b01f6a10b93bdb5f2d3bf4f3e9af32b63909e.
  - LightGBM artifact 8682442473 has digest sha256:7a009c31282ecb1a157f0d63f2173d2e2c0e6083a0d56ceb974f1eb038141ab5.
  - Seeded MLP artifact 8682444015 has digest sha256:401fab4dadeadc9b16b2c0b5a2bc4eeaed3c9eceed57a09a63db8d13a54e8289.
  - Residual MLP artifact 8682445619 has digest sha256:6d79b20f3353707a156e39f52ff7a23eb556312aed5ea1283c0ba0aab43bc208.
  - Descriptive results were LightGBM 51 trades and +13.57805253 USDT, seeded MLP 3 trades and +0.23606185 USDT, residual MLP 1 trade and +0.00008796 USDT.
  - PR 580 was closed without merge after terminal evidence collection.
derived:
  - The finite symmetric volume feature resolved the v1 non-finite matrix blocker under the authorized v2 contract.
  - Role-normalized feature identity preserved semantic and ordered cross-pair equality while retaining raw hashes.
  - Development-only metrics are descriptive evidence and do not authorize winner selection, promotion or profitability claims.
  - Expanding beyond BTC/USDT and ETH/USDT would introduce a new experimental variable and requires a separate versioned task.
unknown:
  - Performance on pairs other than BTC/USDT and ETH/USDT remains untested.
  - Performance on consumed May-June historical OOS and the protected final holdout remains intentionally unknown.
  - Live-trading behavior remains untested and unauthorized.
conflicts: []
first_failure:
  marker: NONE_IN_TERMINAL_V2_RUN
  evidence: Every job in guarded run 30340242201 completed successfully and all required artifacts were preserved.
rejected_hypotheses:
  - V2 still produces non-finite matrices; both pair reports and transformed splits are finite.
  - Cross-pair feature geometry differs semantically; role-normalized ordered identities match.
  - One comparator was skipped or repeated; all three executed exactly once.
  - The terminal request was merged into develop; PR 580 was closed without merge.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation.md
  - .github/workflows/residual-pytorch-bounded-m1-v2-request-generator.yml deleted after its one-shot purpose completed
validation:
  - command: guarded run 30340242201
    result: PASS
    evidence: Request, data, audit and all three exactly-once comparator executions completed successfully.
  - command: terminal artifact inspection
    result: PASS
    evidence: Audit and three model archives were downloaded, their digests matched GitHub metadata and their JSON evidence was finite and internally consistent.
  - command: close trigger PR 580 without merge
    result: PASS
    evidence: PR 580 is closed, merged false, and its terminal body preserves descriptive results and artifact digests.
  - command: final cleanup PR CI
    result: NOT_RUN
    evidence: Final checkpoint and one-shot generator removal have not yet completed repository CI.
blockers: []
next_action: Validate and merge the final cleanup PR, reset the request branch to the cleanup merge SHA, disable the completed run monitor, and treat this task as complete.
```
