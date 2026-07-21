---
task_id: FTAI-20260721-phase6-model-comparison-execution-workflow
status: implementing
branch: feat/phase6-model-comparison-execution-workflow-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
owned_paths:
  - .github/workflows/ai-platform-phase6-model-comparison.yml
  - ai_platform/scripts/model_comparison_run_request.py
  - tests/ai_platform/test_model_comparison_run_request.py
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-execution-workflow.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json
  - ai_platform/scripts/model_comparison_harness.py
  - ai_platform/scripts/run_experiment.py
  - ai_platform/scripts/model_comparison_oos_result_extractor.py
  - ai_platform/scripts/model_comparison_selection_policy.py
  - ai_platform/scripts/model_comparison_provenance_binding.py
  - ai_platform/scripts/model_comparison_result_assembler.py
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
search_first:
  - .github/workflows/ai-platform-phase5-tuning.yml
  - ai_platform/scripts/model_comparison_run_request.py
  - tests/ai_platform/test_model_comparison_run_request.py
optional_reads:
  - docs/ai_platform/PHASE6_MATERIALIZATION_HASH_PARITY.md
  - docs/ai_platform/PHASE6_FINAL_RESULT_ASSEMBLER.md
---

# Phase 6 one-shot historical model comparison execution workflow

## Goal

Add fail-closed GitHub Actions infrastructure that can execute the already-frozen Phase 6 LightGBM-versus-XGBoost historical comparison only after a separate pull request adds one exact canonical run-request file. Keep workflow installation, actual execution trigger, durable evidence persistence, and any later promotion decision as separate work packages.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T09:00:00Z
head: bc0c9b896052439711f524b1844ba0568f580975
branch: feat/phase6-model-comparison-execution-workflow-v1
pr: none
status: implementing
context_routes:
  - .github/workflows/ai-platform-phase6-model-comparison.yml
  - ai_platform/scripts/model_comparison_run_request.py
  - tests/ai_platform/test_model_comparison_run_request.py
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
owned_paths:
  - .github/workflows/ai-platform-phase6-model-comparison.yml
  - ai_platform/scripts/model_comparison_run_request.py
  - tests/ai_platform/test_model_comparison_run_request.py
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-execution-workflow.md
proven:
  - Phase 6 provenance binding, final result assembly, and exact-byte materialization hash parity are already merged on develop.
  - Live develop was verified at 8be21011678da596ad20f0415c58698e7dacc92a before opening the infrastructure PR; intervening merged work belongs to isolated TradingView and PyTorch/RL research tracks and does not overlap the owned Phase 6 execution-workflow paths.
  - The workflow infrastructure branch adds no canonical run-request file and therefore does not itself trigger the historical comparison.
  - The trigger workflow is restricted to same-repository pull requests targeting develop and validates that the trigger PR adds exactly ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json.
  - Canonical request validation pins the Phase 6 contract hash, historical windows, protected final holdout 20260801-20260930, frozen thresholds 0.006/-0.009, and all retuning/promotion/live/profitability authorization flags to false.
  - Materialization validation occurs before market-data access and requires historical data to end at 20260630.
  - Both frozen model runs execute from the same exact trigger-PR head SHA before strict-OOS extraction, deterministic selection, provenance binding, and final result assembly.
  - Successful and failed workflow evidence are uploaded separately; successful evidence is not automatically promoted or treated as a profitability claim.
  - No historical comparison run, final-holdout access, retuning, model promotion, or live-capital change has been performed by this infrastructure work package.
derived:
  - A separate minimal run-request pull request can provide a reviewable one-shot execution authorization without allowing contract, strategy, workflow, model, or feature changes in the same trigger PR.
  - Pull-request CI can validate this infrastructure against the current develop merge state even if the feature branch itself was created before unrelated non-overlapping research commits landed.
unknown:
  - GitHub Actions CI and zizmor have not yet validated the new workflow, validator, tests, and documentation.
  - The actual historical LightGBM-versus-XGBoost runtime has not yet been exercised through this workflow.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - The workflow infrastructure PR should also contain the canonical run-request trigger.
  - A trigger PR may modify the workflow, contract, model configuration, strategy, or any additional file while requesting execution.
  - Historical comparison evidence can authorize final-holdout access, model promotion, live trading, or a profitability claim.
changed_paths:
  - .github/workflows/ai-platform-phase6-model-comparison.yml
  - ai_platform/scripts/model_comparison_run_request.py
  - tests/ai_platform/test_model_comparison_run_request.py
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-execution-workflow.md
validation:
  - command: GitHub Actions CI
    result: NOT_RUN
    evidence: Infrastructure pull request has not yet been opened.
  - command: local clone/test
    result: BLOCKED
    evidence: Sandbox has no repository clone and prior github.com DNS resolution was unavailable; executable validation uses GitHub Actions.
blockers: []
next_action: Open the infrastructure pull request against current develop, verify mergeability and required AI Platform CI, Freqtrade CI, and zizmor results, fix only infrastructure defects if any, then merge and close a durable checkpoint before creating the separate canonical run-request trigger pull request.
```
