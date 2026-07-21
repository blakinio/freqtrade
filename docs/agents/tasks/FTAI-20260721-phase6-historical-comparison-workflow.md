---
task_id: FTAI-20260721-phase6-historical-comparison-workflow
status: active
branch: feat/phase6-historical-comparison-workflow-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: null
owned_paths:
  - .github/workflows/ai-platform-phase6-historical-comparison.yml
  - ai_platform/model_comparison/historical-comparison-run-request-schema-v1.json
  - ai_platform/scripts/model_comparison_execution_request.py
  - tests/ai_platform/test_model_comparison_execution_request.py
  - docs/ai_platform/PHASE6_HISTORICAL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-historical-comparison-workflow.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/PHASE6_HISTORICAL_COMPARISON_EXECUTION.md
  - ai_platform/scripts/model_comparison_execution_request.py
search_first:
  - .github/workflows/ai-platform-phase6-historical-comparison.yml
  - ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json
  - ai_platform/scripts/model_comparison_harness.py
  - ai_platform/scripts/model_comparison_provenance_binding.py
  - ai_platform/scripts/model_comparison_result_assembler.py
optional_reads:
  - ai_platform/validation/final-holdout-v2-declaration.json
---

# Phase 6 historical comparison execution workflow

## Goal

Add guarded one-shot historical LightGBM-versus-XGBoost execution infrastructure without adding or triggering the run request in the same work package.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T07:30:00Z
head: 14207f2004e5632d630f1d455a1f7af3028b20df
branch: feat/phase6-historical-comparison-workflow-v1
pr: null
status: active
context_routes:
  - docs/ai_platform/PHASE6_HISTORICAL_COMPARISON_EXECUTION.md
  - ai_platform/scripts/model_comparison_execution_request.py
owned_paths:
  - .github/workflows/ai-platform-phase6-historical-comparison.yml
  - ai_platform/model_comparison/historical-comparison-run-request-schema-v1.json
  - ai_platform/scripts/model_comparison_execution_request.py
  - tests/ai_platform/test_model_comparison_execution_request.py
  - docs/ai_platform/PHASE6_HISTORICAL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-historical-comparison-workflow.md
proven:
  - develop was 8be21011678da596ad20f0415c58698e7dacc92a when this bounded task branched.
  - The previous Phase 6 hash-parity checkpoint requires workflow infrastructure before a separate actual run-request PR.
  - Open PRs #61 and #62 are isolated PyTorch/RL heavy-runtime work and do not modify this task's owned paths.
  - The infrastructure branch does not contain ai_platform/model_comparison/run-requests/historical-comparison-v1.json, so it cannot trigger the historical comparison workflow.
  - The run request is exact-match validated before dependency installation, cache restore, or market-data access.
  - Historical download coverage is pinned to 20250801-20260630 and strict scoring to consumed historical OOS 20260501-20260630.
  - Protected final holdout 20260801-20260930 remains unused and forbidden for model comparison.
  - Frozen thresholds remain entry_prediction_threshold=0.006 and exit_prediction_threshold=-0.009.
derived:
  - A later request-only PR can safely be the sole trigger for materialization, both frozen backtests, strict-OOS extraction, deterministic selection, provenance binding, and final result assembly.
unknown:
  - Full GitHub Actions validation result for the infrastructure branch.
conflicts: []
first_failure:
  marker: none-yet
  evidence: No branch CI has run yet.
rejected_hypotheses:
  - The actual historical comparison should be triggered from the infrastructure PR itself.
  - A generic or shared final-holdout data cache should be restored for this historical comparison.
changed_paths:
  - .github/workflows/ai-platform-phase6-historical-comparison.yml
  - ai_platform/model_comparison/historical-comparison-run-request-schema-v1.json
  - ai_platform/scripts/model_comparison_execution_request.py
  - tests/ai_platform/test_model_comparison_execution_request.py
  - docs/ai_platform/PHASE6_HISTORICAL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-historical-comparison-workflow.md
validation: []
blockers: []
next_action: Open the infrastructure PR against develop, fix only concrete CI/review failures, and merge only after the exact final head passes required gates; do not add the run-request file in this PR.
```
