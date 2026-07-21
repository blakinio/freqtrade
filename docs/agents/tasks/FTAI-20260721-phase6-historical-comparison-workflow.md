---
task_id: FTAI-20260721-phase6-historical-comparison-workflow
status: ready
branch: develop
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
updated_at: 2026-07-21T09:30:00Z
head: 433d9a70289c901a6ce74f2cbcab071583c47c03
branch: develop
pr: "#63 merged"
status: ready
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
  - PR #63 squash-merged to develop at 433d9a70289c901a6ce74f2cbcab071583c47c03.
  - The merged workflow is request-only; the infrastructure change did not add ai_platform/model_comparison/run-requests/historical-comparison-v1.json and therefore did not execute the comparison.
  - The request validator runs before dependency installation, cache restore, or market-data access and pins contract, selection-policy, and strategy SHA-256 values.
  - Historical download coverage is pinned to 20250801-20260630 and strict scoring to consumed historical OOS 20260501-20260630.
  - AiPhase52ExitStrategy runtime default is frozen to the already-selected exit_prediction_threshold=-0.009; entry_prediction_threshold remains 0.006.
  - Both historical backtest provenance records must match the request-head commit and request-bound frozen strategy SHA-256.
  - Protected final holdout 20260801-20260930 remains unused and forbidden for model comparison, promotion, live trading, and profitability claims.
derived:
  - A separate request-only PR containing exactly the canonical generated request can now be used as the sole trigger for the historical LightGBM-versus-XGBoost comparison.
unknown:
  - The actual historical LightGBM-versus-XGBoost comparison result and workflow artifact do not exist yet because the trigger request has not been added.
conflicts: []
first_failure:
  marker: pr63-static-test-format-typeguard-runtime-exit-default
  evidence: CI exposed static test, formatting, and type-narrowing issues; execution-readiness review also found strategy exit default=0.0, which was corrected to frozen -0.009 and bound by strategy SHA before merge.
rejected_hypotheses:
  - The infrastructure PR itself should trigger the actual historical comparison.
  - Contract risk_assumptions alone were sufficient to guarantee runtime exit=-0.009.
  - A generic or protected-final-holdout cache should be reused for this historical comparison.
changed_paths:
  - .github/workflows/ai-platform-phase6-historical-comparison.yml
  - ai_platform/model_comparison/historical-comparison-run-request-schema-v1.json
  - ai_platform/scripts/model_comparison_execution_request.py
  - ai_platform/strategies/AiPhase52ExitStrategy.py
  - tests/ai_platform/test_model_comparison_execution_request.py
  - docs/ai_platform/PHASE6_HISTORICAL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-historical-comparison-workflow.md
validation:
  - command: AI Platform CI #278
    result: PASS
    evidence: success on final PR #63 head 8b937de25e17404ccbde10885b2bae313fe36864
  - command: GitHub Actions Security Analysis with zizmor #274
    result: PASS
    evidence: success on final PR #63 head 8b937de25e17404ccbde10885b2bae313fe36864
  - command: Freqtrade CI #295
    result: PASS
    evidence: success on final PR #63 head 8b937de25e17404ccbde10885b2bae313fe36864
  - command: review threads PR #63
    result: PASS
    evidence: no inline review threads
  - command: compare 433d9a70289c901a6ce74f2cbcab071583c47c03...develop
    result: PASS
    evidence: identical; ahead_by=0; behind_by=0
blockers: []
next_action: Create a separate branch from develop, add exactly ai_platform/model_comparison/run-requests/historical-comparison-v1.json using the canonical request generated by model_comparison_execution_request.py, open a trigger-only PR against develop, and inspect the guarded Phase 6 historical comparison workflow result without modifying any other file in that PR.
```
