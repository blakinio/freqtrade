---
task_id: FTAI-20260721-phase6-model-comparison-historical-execution
status: done
branch: run/phase6-model-comparison-historical-execution-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#77 closed unmerged; #79 evidence merged"
owned_paths:
  - ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-historical-execution.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-execution-workflow.md
  - ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json
  - ai_platform/scripts/model_comparison_run_request.py
  - .github/workflows/ai-platform-phase6-model-comparison.yml
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
search_first:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json
optional_reads:
  - docs/ai_platform/PHASE6_PROVENANCE_BINDING.md
  - docs/ai_platform/PHASE6_FINAL_RESULT_ASSEMBLER.md
---

# Phase 6 one-shot historical model comparison execution

## Goal

Request exactly one execution of the frozen Phase 6 LightGBM-versus-XGBoost historical comparison through the merged fail-closed workflow. The trigger pull request must add exactly one canonical run-request file and no other path.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T11:50:00Z
head: 8c8f7f0869bb218d8c6b9a61c94f4fee86ee6302
branch: develop
pr: "#77 closed unmerged; #79 evidence merged"
status: ready
context_routes:
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-evidence.md
owned_paths:
  - ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-historical-execution.md
proven:
  - Phase 6 execution workflow infrastructure merged through PR #72 as a62f6ad02c68c006e660358ae304debaaf403419 and its durable checkpoint merged through PR #74 as 5f1dbd81e85f586b77b5a424f49080ca7e385a8c.
  - The canonical Phase 6 contract exact-byte SHA-256 used by the request was 77f62b396123c32ac98ab12c68dbc9acf6cb6b5b4f1a3167dcc0e2ac21c0132b.
  - Trigger PR #77 added exactly ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json and no other path.
  - Trigger commit 38d83e6d22f63a5234458e7c85453b90536b7590 passed AI Platform CI run 29821473481, zizmor run 29821473548, Freqtrade CI run 29821473564, and dedicated Phase 6 workflow run 29821473503; Pre-commit Types update 29821473524 was skipped rather than failed.
  - Dedicated workflow job 88604850782 completed all fail-closed gates, historical Kraken data preparation, both frozen backtests, strict-OOS extraction, deterministic selection, provenance binding, final result assembly, and evidence upload successfully.
  - Workflow artifact phase6-model-comparison-evidence-77 has artifact id 8493443451 and digest sha256:012ff27b73f2a0944ed19689c993a9021237dff1bf7859c48aa3177d4c7739f4.
  - Deterministic selection returned selected_model null with basis no_model_passed_predeclared_eligibility_gates.
  - LightGBMRegressor strict-OOS metrics were profit -0.00147892571, drawdown 0.0018957532099999298, trades 17, and stability 0.0; minimum-profit and minimum-stability gates failed.
  - XGBoostRegressor strict-OOS metrics were profit -0.0015392486680000002, drawdown 0.0021411325816178377, trades 25, and stability 0.0; minimum-profit and minimum-stability gates failed.
  - Historical execution windows remained training 20251201-20260228, tuning 20260301-20260430, scoring 20260501-20260630, prediction 20260301-20260630, and download 20250801-20260630.
  - Frozen thresholds remained entry_prediction_threshold 0.006 and exit_prediction_threshold -0.009.
  - Protected final holdout 20260801-20260930 was not used; retuning, final validation, promotion, live trading, and profitability claims remained unauthorized.
  - Trigger PR #77 was closed without merge after evidence collection.
  - Durable evidence PR #79 passed AI Platform CI run 29827175455, zizmor run 29827175402, and Freqtrade CI run 29827175443; Pre-commit Types update 29827175418 was skipped rather than failed.
  - Durable evidence PR #79 was squash-merged into develop as 8c8f7f0869bb218d8c6b9a61c94f4fee86ee6302.
derived:
  - Phase 6 completed without selecting an eligible LightGBM or XGBoost candidate under the predeclared policy.
  - The consumed historical OOS result cannot be used to retune the frozen Phase 6 comparison.
  - No model promotion, profitability claim, live-trading change, or protected-final-holdout access follows from this result.
unknown:
  - Whether a separate future governance work package will stop this candidate line or define a new independent research phase without reusing the consumed historical OOS for tuning.
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
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-historical-execution.md
validation:
  - command: AI Platform Phase 6 Model Comparison run 29821473503 / job 88604850782
    result: PASS
    evidence: All execution, extraction, selection, provenance-binding, assembly, and artifact-upload steps completed successfully.
  - command: trigger-head AI Platform CI 29821473481 / zizmor 29821473548 / Freqtrade CI 29821473564
    result: PASS
    evidence: All required trigger-head gates completed successfully; Pre-commit Types was skipped, not failed.
  - command: durable evidence PR #79 gates
    result: PASS
    evidence: AI Platform CI 29827175455, zizmor 29827175402, and Freqtrade CI 29827175443 completed successfully before merge.
blockers: []
next_action: Phase 6 historical execution and durable evidence preservation are complete. No candidate was selected. Continue only through a separate governance or independent research work package; do not reopen or merge trigger PR #77, do not retune from consumed historical OOS 20260501-20260630, and do not access protected final holdout 20260801-20260930 without a separately authorized future work package.
```
