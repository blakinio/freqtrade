---
task_id: FTAI-20260721-phase6-historical-comparison-workflow
status: active
branch: feat/phase6-historical-comparison-workflow-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#63"
owned_paths:
  - .github/workflows/ai-platform-phase6-historical-comparison.yml
  - ai_platform/model_comparison/historical-comparison-run-request-schema-v1.json
  - ai_platform/scripts/model_comparison_execution_request.py
  - ai_platform/strategies/AiPhase52ExitStrategy.py
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
updated_at: 2026-07-21T08:45:00Z
head: f4c0592b3d86322e363767df8e61d21a7b693e90
branch: feat/phase6-historical-comparison-workflow-v1
pr: "#63 open"
status: active
context_routes:
  - docs/ai_platform/PHASE6_HISTORICAL_COMPARISON_EXECUTION.md
  - ai_platform/scripts/model_comparison_execution_request.py
owned_paths:
  - .github/workflows/ai-platform-phase6-historical-comparison.yml
  - ai_platform/model_comparison/historical-comparison-run-request-schema-v1.json
  - ai_platform/scripts/model_comparison_execution_request.py
  - ai_platform/strategies/AiPhase52ExitStrategy.py
  - tests/ai_platform/test_model_comparison_execution_request.py
  - docs/ai_platform/PHASE6_HISTORICAL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-historical-comparison-workflow.md
proven:
  - develop was 8be21011678da596ad20f0415c58698e7dacc92a when this bounded task branched; concurrent experimental runtime work later advanced develop without overlapping owned paths.
  - The previous Phase 6 hash-parity checkpoint requires workflow infrastructure before a separate actual run-request PR.
  - The infrastructure branch does not contain ai_platform/model_comparison/run-requests/historical-comparison-v1.json, so it cannot trigger the historical comparison workflow.
  - The run request is exact-match validated before dependency installation, cache restore, or market-data access.
  - Historical download coverage is pinned to 20250801-20260630 and strict scoring to consumed historical OOS 20260501-20260630.
  - Protected final holdout 20260801-20260930 remains unused and forbidden for model comparison.
  - Frozen thresholds remain entry_prediction_threshold=0.006 and exit_prediction_threshold=-0.009.
  - AiPhase52ExitStrategy runtime default for exit_prediction_threshold was corrected from 0.0 to the already-selected frozen -0.009 before any Phase 6 comparison execution.
  - The canonical run request now binds exact AiPhase52ExitStrategy.py SHA-256, and the workflow requires both runtime provenance records to report that same strategy hash.
derived:
  - A later request-only PR can safely be the sole trigger for materialization, both frozen backtests, strict-OOS extraction, deterministic selection, provenance binding, and final result assembly.
unknown:
  - Full GitHub Actions validation result for the final infrastructure head.
conflicts: []
first_failure:
  marker: pr63-static-test-format-typeguard
  evidence: Initial CI exposed an over-broad static call-count assertion, then Ruff format drift, then pre-commit type narrowing caused by a non-TypeGuard helper; all were corrected without changing the request-only execution contract.
rejected_hypotheses:
  - The actual historical comparison should be triggered from the infrastructure PR itself.
  - A generic or shared final-holdout data cache should be restored for this historical comparison.
  - Contract risk_assumptions alone were sufficient to guarantee runtime exit=-0.009; strategy source inspection showed DecimalParameter default=0.0, so the frozen selected default and strategy hash had to be bound before execution.
changed_paths:
  - .github/workflows/ai-platform-phase6-historical-comparison.yml
  - ai_platform/model_comparison/historical-comparison-run-request-schema-v1.json
  - ai_platform/scripts/model_comparison_execution_request.py
  - ai_platform/strategies/AiPhase52ExitStrategy.py
  - tests/ai_platform/test_model_comparison_execution_request.py
  - docs/ai_platform/PHASE6_HISTORICAL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-historical-comparison-workflow.md
validation:
  - command: AI Platform CI #267
    result: PASS
    evidence: pre-strategy-binding head passed tests, Ruff, formatter, Codespell, and JSON validation; final head requires rerun.
  - command: GitHub Actions Security Analysis with zizmor #263
    result: PASS
    evidence: pre-strategy-binding head passed security analysis; final head requires rerun.
blockers: []
next_action: Wait for exact final-head CI on PR #63, fix only concrete failures, and squash-merge only after required gates and review threads are clean; do not add the run-request file in this PR.
```
