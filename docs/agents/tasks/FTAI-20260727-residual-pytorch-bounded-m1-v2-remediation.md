---
task_id: FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation
status: active
branch: fix/residual-pytorch-bounded-m1-v2-cross-pair-identity
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: 566
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

The user explicitly authorized autonomous continuation to completion on 2026-07-27 and repeated that authorization on 2026-07-28. V2 may replace the undefined prior-volume percentage change with the finite symmetric formula `2*(current-previous)/(abs(current)+abs(previous))`, using `0` when the denominator is zero or the result is non-finite. For non-negative market volume the result is bounded to `[-2, 2]`.

All targets, thresholds, models, model parameters, pairs, timeframes, fees, seeds, temporal boundaries, execution counts, the consumed May-June historical OOS prohibition, protected final holdout prohibition, Phase 6 isolation, no-winner-selection rule and no-profitability/superiority claims remain unchanged.

V1 is retired and must not be modified or rerun. Real v2 execution requires a separate PR adding exactly the canonical v2 request file, and every trigger PR must be closed without merge after terminal evidence collection.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T07:10:00Z
head: 627b97369198fdfe8194091fcf7c97da7f31d551
branch: fix/residual-pytorch-bounded-m1-v2-cross-pair-identity
pr: 566
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
  - tests/ai_platform/test_residual_pytorch_bounded_m1_v2_cross_pair_identity.py
  - .github/workflows/residual-pytorch-bounded-m1-execution.yml
  - .github/workflows/residual-pytorch-bounded-m1-v2-request-generator.yml
proven:
  - V1 run 30299203871 failed closed because %-volume-change contained infinity for both pairs; no model executed.
  - PR 540 merged finite bounded v2 infrastructure as 7ce6f1ff20a59eff9d6ac904e20a15655f27d200 after AI Platform CI, full Freqtrade CI and zizmor passed.
  - Generator run 30310070831 produced the canonical v2 request; marker PR 551 was closed without merge.
  - Exact-one-file PR 554 ran guarded execution 30310204713 and was closed without merge.
  - Run 30310204713 passed request validation plus fresh BTC/USDT and ETH/USDT pre-May data acquisition, pair coverage and combined pre-fit coverage.
  - Both raw v2 audits completed with 272 expanded features, 8640 raw rows, 8628 eligible rows, zero non-finite feature rows, finite train/test matrices and 12 trailing target-null rows per pair.
  - Neither consumed May-June historical OOS nor the protected final holdout was used.
  - All three comparator models were skipped before fit because cross-pair validation failed closed.
  - BTC and ETH raw feature hashes differ only because feature names are pair-qualified; normalizing names to PRIMARY_PAIR and CORRELATED_PAIR roles yields identical feature identity.
  - Focused AI platform tests passed after the role-normalized validator and regression were added.
  - Temporary Ruff diagnostics identified exactly one 103-character assertion line; it was wrapped and the standard read-only workflow was restored byte-for-byte.
derived:
  - Pair-qualified feature-name hashes must not be compared directly across primary pairs.
  - Role normalization preserves primary-versus-correlated structure while still detecting semantic feature-name, ordering or count drift.
  - The existing verified data cache remains data-only; every fresh execution must rerun pair and combined coverage before fit.
unknown:
  - Whether exact-head CI for PR 566 passes after the lint-only correction and workflow restoration.
  - Whether a fresh exact-one-file run passes cross-pair audit after role normalization.
  - Whether all three unchanged comparator models complete exactly once.
conflicts: []
first_failure:
  marker: CROSS_PAIR_PAIR_QUALIFIED_HASH_FALSE_NEGATIVE
  evidence: Run 30310204713 produced two audit-supported matrices but validate-audit rejected different raw hashes caused by BTC/USDT versus ETH/USDT tokens.
rejected_hypotheses:
  - V2 feature values remained non-finite; both audit reports show zero non-finite feature rows and finite transformed splits.
  - Missing or late pre-May data caused the failure; all pair and combined coverage gates passed.
  - A comparator model caused the failure; all three model executions were skipped before fit.
  - The pair matrices have different semantic feature geometry; role-normalized ordered feature names are identical.
changed_paths:
  - ai_platform/scripts/residual_pytorch_bounded_m1_v2_execution.py
  - tests/ai_platform/test_residual_pytorch_bounded_m1_v2_cross_pair_identity.py
  - docs/agents/tasks/FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation.md
validation:
  - command: guarded run 30310204713
    result: FAIL_CLOSED
    evidence: Data and both matrix audits passed; cross-pair raw-hash comparison failed before any model fit.
  - command: AI Platform CI 30337143750
    result: FAIL_LINT_ONLY
    evidence: Tests passed; Ruff identified one long assertion line, now corrected.
  - command: final exact-head PR 566 CI
    result: NOT_RUN
    evidence: Standard workflow is restored and final checkpoint head has just been created.
blockers: []
next_action: Validate and merge PR 566 only if exact-head AI Platform CI, Freqtrade CI and zizmor pass, then generate a fresh exact-one-file v2 request, execute guarded run to terminal, close its PR without merge, and record final evidence.
```
