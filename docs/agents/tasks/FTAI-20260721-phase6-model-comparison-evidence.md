---
task_id: FTAI-20260721-phase6-model-comparison-evidence
status: implementing
branch: research/ai-platform-phase6-model-comparison-evidence-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
owned_paths:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-evidence.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-historical-execution.md
  - ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json
  - ai_platform/evidence/phase5-exit-thresholds-v1.json
search_first:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json
optional_reads:
  - docs/ai_platform/PHASE6_PROVENANCE_BINDING.md
  - docs/ai_platform/PHASE6_FINAL_RESULT_ASSEMBLER.md
---

# Phase 6 historical model-comparison durable evidence

## Goal

Preserve the completed frozen Phase 6 LightGBM-versus-XGBoost historical comparison as durable, reviewable repository evidence. Bind the durable record to the exact successful workflow artifact and its provenance hashes without merging the one-shot trigger request or changing candidates, parameters, features, selection policy, or protected-final-holdout boundaries.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T11:40:00Z
head: 550766fc5e1fce065a0ddc7d8c3866f965e17393
branch: research/ai-platform-phase6-model-comparison-evidence-v1
pr: none
status: implementing
context_routes:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-historical-execution.md
owned_paths:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-evidence.md
proven:
  - One-shot trigger PR #77 added exactly ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json and executed commit 38d83e6d22f63a5234458e7c85453b90536b7590.
  - Dedicated workflow run 29821473503 and job 88604850782 completed successfully, including scope validation, canonical request validation, frozen-contract validation, materialization, historical Kraken data preparation, both frozen backtests, strict-OOS extraction, deterministic selection, provenance binding, final result assembly, and successful evidence upload.
  - Normal trigger-head gates also completed successfully: AI Platform CI run 29821473481, zizmor run 29821473548, and Freqtrade CI run 29821473564; Pre-commit Types update 29821473524 was skipped rather than failed.
  - GitHub Actions artifact phase6-model-comparison-evidence-77 has artifact id 8493443451 and digest sha256:012ff27b73f2a0944ed19689c993a9021237dff1bf7859c48aa3177d4c7739f4.
  - The downloaded artifact ZIP independently hashes to 012ff27b73f2a0944ed19689c993a9021237dff1bf7859c48aa3177d4c7739f4, exactly matching the GitHub artifact digest.
  - Comparison result status is completed and deterministic selection is selected_model null with basis no_model_passed_predeclared_eligibility_gates.
  - LightGBMRegressor strict-OOS metrics are profit -0.00147892571, drawdown 0.0018957532099999298, trades 17, and stability 0.0; it failed minimum-profit and minimum-stability gates.
  - XGBoostRegressor strict-OOS metrics are profit -0.0015392486680000002, drawdown 0.0021411325816178377, trades 25, and stability 0.0; it failed minimum-profit and minimum-stability gates.
  - Exact materialization plan SHA-256 is 2ecd1eea136fd47e997838cc09e5b16804f863a0ee35df62071bbf2b5f99d176 and exact selection-decision SHA-256 is 56ca4282ed4df30fe2bc3cc8bcf9da5c0175f593018403cbaea2acf66861d47e.
  - Result provenance binds both exact run provenances, backtest archives, OOS extractions, the selection decision, and execution git commit 38d83e6d22f63a5234458e7c85453b90536b7590.
  - Strict historical OOS remained 20260501-20260630 with source status consumed_historical_oos.
  - Protected final holdout 20260801-20260930 was not used; retuning, final validation, promotion, live trading, and profitability claims remain unauthorized.
  - Frozen thresholds remain entry_prediction_threshold 0.006 and exit_prediction_threshold -0.009.
  - Trigger PR #77 was closed without merge after evidence collection.
derived:
  - Phase 6 completed without selecting an eligible LightGBM or XGBoost candidate under the predeclared policy.
  - The historical evidence does not authorize retuning, promotion, a profitability claim, or protected-final-holdout access.
  - Any future research or governance response must be a separate work package and must not retroactively change the frozen Phase 6 comparison.
unknown:
  - Whether a future governance work package will stop this candidate line, define a new independent research phase, or make another decision that does not reuse the consumed historical OOS for tuning.
conflicts: []
first_failure:
  marker: none
  evidence: The one-shot historical comparison and evidence chain completed successfully.
rejected_hypotheses:
  - Merge trigger PR #77 merely because its workflow completed.
  - Select LightGBM solely because its historical profit was slightly less negative than XGBoost despite both failing the predeclared gates.
  - Retune thresholds, model parameters, features, candidates, or selection policy from the consumed historical OOS result.
  - Access the protected final holdout to break the no-selection outcome.
changed_paths:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-evidence.md
validation:
  - command: AI Platform Phase 6 Model Comparison run 29821473503 / job 88604850782
    result: PASS
    evidence: All execution, extraction, selection, provenance-binding, assembly, and artifact-upload steps completed successfully.
  - command: downloaded artifact SHA-256
    result: PASS
    evidence: Local SHA-256 012ff27b73f2a0944ed19689c993a9021237dff1bf7859c48aa3177d4c7739f4 exactly matches the GitHub Actions artifact digest.
  - command: artifact evidence SHA-256 inventory
    result: PASS
    evidence: Durable evidence records exact hashes for request, materialization, both run provenances and summaries, both OOS extractions, selection decision, result provenance, and final comparison result.
blockers: []
next_action: Open a separate durable evidence pull request adding the provenance-bound evidence JSON and this task record, require AI Platform CI, Freqtrade CI, and zizmor to pass, then merge it. After merge, close the historical-execution and evidence task checkpoints in a docs-only pull request. Do not reopen or merge trigger PR #77, do not retune from the consumed historical OOS result, and do not access the protected final holdout.
```
