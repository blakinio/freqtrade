---
task_id: FTAI-20260721-phase6-model-comparison-evidence
status: done
branch: research/ai-platform-phase6-model-comparison-evidence-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#79 merged"
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
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
search_first:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
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
updated_at: 2026-07-21T11:50:00Z
head: 8c8f7f0869bb218d8c6b9a61c94f4fee86ee6302
branch: develop
pr: "#79 merged"
status: ready
context_routes:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-historical-execution.md
owned_paths:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-evidence.md
proven:
  - One-shot trigger PR #77 added exactly ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json, executed commit 38d83e6d22f63a5234458e7c85453b90536b7590, and was closed without merge after evidence collection.
  - Dedicated workflow run 29821473503 and job 88604850782 completed successfully, including scope validation, canonical request validation, frozen-contract validation, materialization, historical Kraken data preparation, both frozen backtests, strict-OOS extraction, deterministic selection, provenance binding, final result assembly, and successful evidence upload.
  - Normal trigger-head gates completed successfully: AI Platform CI run 29821473481, zizmor run 29821473548, and Freqtrade CI run 29821473564; Pre-commit Types update 29821473524 was skipped rather than failed.
  - GitHub Actions artifact phase6-model-comparison-evidence-77 has artifact id 8493443451 and digest sha256:012ff27b73f2a0944ed19689c993a9021237dff1bf7859c48aa3177d4c7739f4.
  - The independently downloaded artifact ZIP hashes to 012ff27b73f2a0944ed19689c993a9021237dff1bf7859c48aa3177d4c7739f4, exactly matching the GitHub artifact digest.
  - Durable evidence at ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json records exact hashes for request, materialization, both run provenances and summaries, both strict-OOS extractions, both backtest archives, selection decision, result provenance, and final comparison result.
  - Deterministic selection is selected_model null with basis no_model_passed_predeclared_eligibility_gates.
  - LightGBMRegressor strict-OOS metrics are profit -0.00147892571, drawdown 0.0018957532099999298, trades 17, and stability 0.0; it failed minimum-profit and minimum-stability gates.
  - XGBoostRegressor strict-OOS metrics are profit -0.0015392486680000002, drawdown 0.0021411325816178377, trades 25, and stability 0.0; it failed minimum-profit and minimum-stability gates.
  - Exact materialization plan SHA-256 is 2ecd1eea136fd47e997838cc09e5b16804f863a0ee35df62071bbf2b5f99d176 and exact selection-decision SHA-256 is 56ca4282ed4df30fe2bc3cc8bcf9da5c0175f593018403cbaea2acf66861d47e.
  - Strict historical OOS remained 20260501-20260630 with source status consumed_historical_oos.
  - Protected final holdout 20260801-20260930 was not used; retuning, final validation, promotion, live trading, and profitability claims remain unauthorized.
  - Frozen thresholds remain entry_prediction_threshold 0.006 and exit_prediction_threshold -0.009.
  - Evidence PR #79 passed AI Platform CI run 29827175455, zizmor run 29827175402, and Freqtrade CI run 29827175443; Pre-commit Types update 29827175418 was skipped rather than failed.
  - Evidence PR #79 was squash-merged into develop as 8c8f7f0869bb218d8c6b9a61c94f4fee86ee6302.
derived:
  - Phase 6 completed without selecting an eligible LightGBM or XGBoost candidate under the predeclared policy.
  - The historical evidence does not authorize retuning, promotion, a profitability claim, or protected-final-holdout access.
  - Any future research or governance response must be a separate work package and must not retroactively change the frozen Phase 6 comparison.
unknown:
  - Whether a future governance work package will stop this candidate line or define a new independent research phase without reusing the consumed historical OOS for tuning.
conflicts: []
first_failure:
  marker: none
  evidence: The one-shot historical comparison, evidence chain, and durable evidence PR all completed successfully.
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
  - command: evidence PR #79 gates
    result: PASS
    evidence: AI Platform CI 29827175455, zizmor 29827175402, and Freqtrade CI 29827175443 completed successfully before squash merge as 8c8f7f0869bb218d8c6b9a61c94f4fee86ee6302.
blockers: []
next_action: Durable Phase 6 model-comparison evidence is merged and this work package is complete. No candidate was selected. Any further action requires a separate governance or independent research work package; do not retune from consumed historical OOS 20260501-20260630 and do not access protected final holdout 20260801-20260930 without separate authorization.
```
