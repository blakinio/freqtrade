---
task_id: FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation
status: active
branch: develop
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
updated_at: 2026-07-28T07:47:00Z
head: a7add1dd079ee59a209f0eb41502a734def976f9
branch: develop
pr: 566
status: ready
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
  - PR 540 merged finite bounded v2 infrastructure as 7ce6f1ff20a59eff9d6ac904e20a15655f27d200.
  - Run 30310204713 passed request, pair data and combined coverage gates before model fit.
  - Both v2 pair audits produced 272 finite expanded features, 8628 eligible rows and 12 trailing target-null rows.
  - Run 30310204713 failed closed only because raw pair-qualified feature-name hashes were compared directly.
  - Neither consumed May-June historical OOS nor the protected final holdout was used.
  - PR 566 added primary/correlated pair-role normalization while preserving raw hashes and semantic drift checks.
  - PR 566 AI Platform CI 30338073583 passed tests, Ruff, format, codespell and JSON validation.
  - PR 566 Freqtrade CI 30338073595 passed Python 3.11-3.14, coverage, distributions and CI Gate.
  - PR 566 zizmor 30338073594 passed.
  - PR 566 merged as a7add1dd079ee59a209f0eb41502a734def976f9.
  - Marker PR 575 changed exactly one marker file and was closed without merge.
  - Generator run 30339476205 failed before dependencies because the checkpoint used governance-invalid result FAIL_LINT_ONLY.
  - Generator run 30339476205 performed no request generation, data access, training or backtesting.
derived:
  - Pair-qualified feature names must be normalized by primary/correlated role before cross-pair identity comparison.
  - Role normalization preserves feature ordering and semantics while allowing the primary pair symbol to differ.
  - A fresh request must bind the merged validator SHA and must not reuse the request from PR 554.
unknown:
  - Whether the fresh exact-one-file run passes the corrected cross-pair audit.
  - Whether LightGBM, seeded MLP and residual MLP each complete exactly once.
  - The terminal descriptive diagnostics for the three comparator tracks.
conflicts: []
first_failure:
  marker: CHECKPOINT_VALIDATION_ENUM_DRIFT
  evidence: Generator run 30339476205 rejected validation result FAIL_LINT_ONLY; governance permits only PASS, FAIL, BLOCKED or NOT_RUN.
rejected_hypotheses:
  - Generator run 30339476205 accessed market data or trained a model; it stopped at checkpoint validation.
  - PR 566 changed feature values, targets, thresholds or model parameters; it changed evidence validation only.
  - The v2 matrices remained non-finite; both pair audit reports recorded zero non-finite feature rows.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-residual-pytorch-bounded-m1-v2-remediation.md
validation:
  - command: guarded run 30310204713
    result: FAIL
    evidence: Pair matrices passed, but raw pair-qualified cross-pair hashes caused a false-negative before model fit.
  - command: AI Platform CI 30338073583
    result: PASS
    evidence: Tests, Ruff, format, codespell and JSON validation passed on the final PR 566 head.
  - command: Freqtrade CI 30338073595
    result: PASS
    evidence: Python 3.11-3.14, full coverage, distributions and CI Gate passed on the final PR 566 head.
  - command: zizmor 30338073594
    result: PASS
    evidence: Workflow security analysis passed on the final PR 566 head.
  - command: request generator 30339476205
    result: FAIL
    evidence: Checkpoint validation rejected FAIL_LINT_ONLY before dependencies or request generation.
blockers: []
next_action: Merge this checkpoint correction, reset the request branch to its merge SHA, generate a fresh canonical request, run the guarded v2 comparison to terminal, close the trigger PR without merge, and record final evidence.
```
