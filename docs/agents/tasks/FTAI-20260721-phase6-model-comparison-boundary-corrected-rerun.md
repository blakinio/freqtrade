---
task_id: FTAI-20260721-phase6-model-comparison-boundary-corrected-rerun
status: active
branch: docs/phase6-model-comparison-corrected-evidence
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "pending evidence PR"
owned_paths:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-boundary-corrected-rerun.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json
  - ai_platform/scripts/model_comparison_run_request.py
  - .github/workflows/ai-platform-phase6-model-comparison.yml
search_first:
  - PR #88 closed state and corrected workflow evidence
  - open PRs overlapping Phase 6 comparison workflow or evidence ownership
optional_reads:
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-historical-execution.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-evidence.md
---

# Phase 6 boundary-corrected historical comparison rerun

## Goal

Supersede the incomplete execution-boundary conclusion from canonical run #77 without discarding its exact historical evidence, execute exactly one corrected canonical LightGBM-versus-XGBoost rerun through the merged exclusive-stop workflow, preserve the corrected evidence durably, and close Phase 6 without retuning or protected-final-holdout access.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T15:00:00Z
head: 1fc2e2bd58e8838975023f45cda9f688585b424c
branch: docs/phase6-model-comparison-corrected-evidence
pr: pending evidence PR
status: ready
context_routes:
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - .github/workflows/ai-platform-phase6-model-comparison.yml
owned_paths:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-boundary-corrected-rerun.md
proven:
  - Original canonical run #77 evidence remains preserved in Git history but is non-authoritative because its execution/download stops at 20260630 omitted the remainder of the declared June 30 session.
  - Boundary fix PR #81 preserved all semantic research windows and frozen comparison choices while changing only Freqtrade execution/download exclusive stops to 20260701; it merged as 303b600c0b7386b68db8f61ef9c740a7ea9a1f54.
  - Corrected one-shot trigger PR #88 added exactly ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json, executed commit ad44823af157a27258a1bdbc3c64536aae2d3593, and was closed without merge after evidence collection.
  - Corrected dedicated workflow run 29832315428 / job 88639846851 completed successfully through trigger-scope validation, frozen-contract validation, materialization, historical data preparation, both frozen backtests, strict-OOS extraction, deterministic selection, provenance binding, result assembly, and evidence upload.
  - Trigger-head AI Platform CI run 29832315390, zizmor run 29832315494, and Freqtrade CI run 29832315485 completed successfully; Pre-commit Types update run 29832315504 was skipped rather than failed.
  - Corrected artifact phase6-model-comparison-evidence-88 has artifact id 8498159861 and GitHub digest sha256:a180b4b4eb2265a96884198388b60d1fca6439066043d8385ca2f3a374df28e4.
  - Independently downloaded corrected artifact ZIP hashes to a180b4b4eb2265a96884198388b60d1fca6439066043d8385ca2f3a374df28e4, exactly matching the GitHub digest.
  - Corrected materialization records semantic prediction 20260301-20260630 and semantic download 20250801-20260630 while using execution ranges 20260301-20260701 and 20250801-20260701.
  - Strict historical OOS remains 20260501-20260630 with close upper bound exclusive 2026-07-01T00:00:00Z.
  - Frozen candidates remain LightGBMRegressor and XGBoostRegressor; entry_prediction_threshold remains 0.006 and exit_prediction_threshold remains -0.009.
  - Corrected deterministic selection remains selected_model null with basis no_model_passed_predeclared_eligibility_gates.
  - LightGBMRegressor corrected strict-OOS metrics are profit -0.00147892571, drawdown 0.0018957532099999298, trades 17, stability 0.0; minimum-profit and minimum-stability gates failed.
  - XGBoostRegressor corrected strict-OOS metrics are profit -0.0015392486680000002, drawdown 0.0021411325816178377, trades 25, stability 0.0; minimum-profit and minimum-stability gates failed.
  - Protected final holdout 20260801-20260930 remains unused and unauthorized; retuning, promotion, live trading, and profitability claims remain forbidden.
derived:
  - The boundary-corrected run is now the authoritative Phase 6 LightGBM-versus-XGBoost comparison evidence.
  - Phase 6 ends with no eligible model selected under the frozen predeclared policy.
  - The corrected evidence does not authorize changing thresholds, features, candidates, model parameters, selection policy, or using consumed historical OOS for new tuning.
  - Separate PyTorch/RL research cannot retroactively alter the completed Phase 6 result.
unknown:
  - Whether an independent future model-family research work package will produce a candidate worth evaluating under a separately declared policy; this is outside Phase 6.
conflicts: []
first_failure:
  marker: none
  evidence: The corrected one-shot comparison and evidence collection completed successfully; both candidates simply failed the predeclared eligibility gates.
rejected_hypotheses:
  - Merge trigger PR #88 merely because its workflow completed.
  - Select LightGBM solely because its corrected historical profit is slightly less negative than XGBoost despite both failing the frozen gates.
  - Retune thresholds, model parameters, features, candidates, or selection policy from consumed historical OOS.
  - Access protected final holdout 20260801-20260930 to break the no-selection outcome.
  - Let isolated PyTorch/RL research rewrite or expand the completed Phase 6 candidate set.
changed_paths:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-boundary-corrected-rerun.md
validation:
  - command: AI Platform Phase 6 Model Comparison run 29832315428 / job 88639846851
    result: PASS
    evidence: All corrected execution, extraction, deterministic selection, provenance-binding, result-assembly, and artifact-upload steps completed successfully.
  - command: trigger-head repository gates for ad44823af157a27258a1bdbc3c64536aae2d3593
    result: PASS
    evidence: AI Platform CI 29832315390, zizmor 29832315494, and Freqtrade CI 29832315485 completed successfully; Pre-commit Types update 29832315504 was skipped.
  - command: independently downloaded corrected artifact SHA-256
    result: PASS
    evidence: Local ZIP SHA-256 a180b4b4eb2265a96884198388b60d1fca6439066043d8385ca2f3a374df28e4 exactly matches the GitHub artifact digest.
  - command: protected final holdout boundary review
    result: PASS
    evidence: Final holdout 20260801-20260930 remains outside all corrected historical semantic/execution ranges and was not used.
blockers: []
next_action: Open a two-file durable-evidence PR against current develop, validate repository gates, squash-merge it, then mark this task done. After Phase 6 evidence closure, continue only with the separately bounded PyTorch/RL execution-infrastructure workstream; do not retune Phase 6 or access the protected final holdout.
```
