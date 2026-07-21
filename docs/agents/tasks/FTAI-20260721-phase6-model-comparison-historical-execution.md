---
task_id: FTAI-20260721-phase6-model-comparison-historical-execution
status: implementing
branch: run/phase6-model-comparison-historical-execution-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
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
search_first:
  - ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json
  - ai_platform/scripts/model_comparison_run_request.py
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
updated_at: 2026-07-21T10:10:00Z
head: 5f1dbd81e85f586b77b5a424f49080ca7e385a8c
branch: develop
pr: none
status: implementing
context_routes:
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - ai_platform/scripts/model_comparison_run_request.py
  - .github/workflows/ai-platform-phase6-model-comparison.yml
owned_paths:
  - ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-historical-execution.md
proven:
  - Phase 6 execution workflow infrastructure merged through PR #72 as a62f6ad02c68c006e660358ae304debaaf403419 and its durable checkpoint merged through PR #74 as 5f1dbd81e85f586b77b5a424f49080ca7e385a8c.
  - The trigger workflow accepts only a same-repository pull request targeting develop whose diff adds exactly ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json.
  - The canonical current Phase 6 contract exact-byte SHA-256 is 77f62b396123c32ac98ab12c68dbc9acf6cb6b5b4f1a3167dcc0e2ac21c0132b; this was independently verified by reconstructing the exact contract bytes and matching their Git blob SHA-1 to repository blob e1317cdfc9ec7b7f76111955e1fd0682d613c09a before taking SHA-256.
  - Historical execution windows remain training 20251201-20260228, tuning 20260301-20260430, scoring 20260501-20260630, prediction 20260301-20260630, and download 20250801-20260630.
  - Frozen thresholds remain entry_prediction_threshold 0.006 and exit_prediction_threshold -0.009.
  - Protected final holdout 20260801-20260930 remains forbidden and outside every market-data and scoring range authorized by the request.
  - All request authorization flags for final-holdout use, retuning, model-parameter changes, feature changes, promotion, live trading, and profitability claims must remain false.
  - The trigger pull request itself must not be merged merely to obtain execution evidence; workflow output is historical evidence only and must be reviewed before any separate durable evidence or later decision work package.
derived:
  - The task record must be merged before opening the execution trigger PR because adding it to the trigger PR would violate the workflow's exact-one-file diff gate.
unknown:
  - Whether the configured Kraken historical data ranges are fully available to the workflow cache/download path at execution time.
  - Whether both frozen model backtests complete successfully in the GitHub Actions runtime.
  - The historical strict-OOS metrics and deterministic selection result remain unknown until execution completes.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - Add the task record, workflow edits, contract edits, or any other file to the execution trigger PR.
  - Access the protected final holdout to improve or validate the historical comparison.
  - Retune thresholds, model parameters, or features based on execution results.
  - Treat historical comparison output as automatic promotion or a profitability claim.
changed_paths:
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-historical-execution.md
validation:
  - command: canonical contract exact-byte identity
    result: PASS
    evidence: Reconstructed bytes with final newline produce repository Git blob e1317cdfc9ec7b7f76111955e1fd0682d613c09a and SHA-256 77f62b396123c32ac98ab12c68dbc9acf6cb6b5b4f1a3167dcc0e2ac21c0132b.
blockers: []
next_action: Merge this task-record-only prerequisite, then create branch run/phase6-model-comparison-historical-execution-v1 from current develop and open a pull request adding exactly ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json with the canonical request payload. Do not modify any other path in the trigger pull request. Observe the dedicated Phase 6 workflow through completion and collect its exact evidence artifact if successful; on failure, inspect only concrete workflow diagnostics and fix infrastructure defects in a separate work package rather than broadening the trigger PR.
```
