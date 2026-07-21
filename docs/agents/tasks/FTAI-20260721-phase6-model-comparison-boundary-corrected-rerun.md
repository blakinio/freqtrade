---
task_id: FTAI-20260721-phase6-model-comparison-boundary-corrected-rerun
status: active
branch: docs/phase6-model-comparison-boundary-supersession
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "pending"
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
  - PR #81 merged state and current develop before corrected trigger
  - open PRs overlapping Phase 6 comparison workflow or evidence ownership
optional_reads:
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-historical-execution.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-evidence.md
---

# Phase 6 boundary-corrected historical comparison rerun

## Goal

Supersede the incomplete execution-boundary conclusion from canonical run #77 without discarding its exact historical evidence, then execute exactly one corrected canonical LightGBM-versus-XGBoost rerun through the merged exclusive-stop workflow. Preserve every frozen comparison choice and keep the protected final holdout unused.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T12:35:00Z
head: 303b600c0b7386b68db8f61ef9c740a7ea9a1f54
branch: docs/phase6-model-comparison-boundary-supersession
pr: pending supersession PR
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
  - Original canonical trigger PR #77 executed commit 38d83e6d22f63a5234458e7c85453b90536b7590 and produced durable artifact phase6-model-comparison-evidence-77 with digest sha256:012ff27b73f2a0944ed19689c993a9021237dff1bf7859c48aa3177d4c7739f4.
  - Direct inspection of the preserved #77 artifact showed both materialized and runtime manifests used timerange 20260301-20260630 and download_timerange 20250801-20260630.
  - Freqtrade treats the stop date as the execution boundary at midnight, so those ranges omitted the remainder of the declared 2026-06-30 session.
  - Boundary fix PR #81 preserved semantic prediction 20260301-20260630, semantic download 20250801-20260630, and strict scoring 20260501-20260630 while materializing execution stops 20260301-20260701 and 20250801-20260701.
  - PR #81 passed exact-head AI Platform CI #320, zizmor #337, and Freqtrade CI #359 before squash merge as 303b600c0b7386b68db8f61ef9c740a7ea9a1f54.
  - Frozen candidates remain LightGBMRegressor and XGBoostRegressor; entry_prediction_threshold remains 0.006 and exit_prediction_threshold remains -0.009.
  - Protected final holdout 20260801-20260930 remains unused and unauthorized for this rerun.
derived:
  - The preserved #77 metrics and selected_model null decision remain exact records of that run but are not authoritative Phase 6 comparison conclusions pending the corrected rerun.
  - The corrected rerun must use the same contract, model identities, features, selection policy, consumed historical OOS semantics, and no-retuning boundary.
unknown:
  - Whether corrected full-June-30 execution changes either model metric or the deterministic selected_model result.
conflicts: []
first_failure:
  marker: phase6-end-exclusive-boundary-defect
  evidence: The original canonical manifests ended at 20260630, which Freqtrade interpreted at midnight and therefore did not cover the complete declared June 30 session.
rejected_hypotheses:
  - Treat the #77 no-selection result as authoritative after discovering the incomplete execution boundary.
  - Retune thresholds, model parameters, features, candidates, or selection policy before the corrected rerun.
  - Use the protected final holdout to resolve or validate the corrected historical comparison.
  - Merge the corrected trigger PR merely because its one-shot workflow completes.
changed_paths:
  - ai_platform/evidence/phase6-model-comparison-lightgbm-vs-xgboost-v1.json
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-boundary-corrected-rerun.md
validation:
  - command: preserved #77 artifact manifest inspection
    result: PASS
    evidence: Materialized and runtime manifests both recorded prediction stop 20260630 and download stop 20260630.
  - command: boundary fix PR #81 exact-head gates
    result: PASS
    evidence: AI Platform CI #320, zizmor #337, and Freqtrade CI #359 completed successfully before merge 303b600c0b7386b68db8f61ef9c740a7ea9a1f54.
  - command: protected final holdout boundary review
    result: PASS
    evidence: Final holdout 20260801-20260930 remains outside all corrected historical semantic and execution ranges and remains unused.
blockers: []
next_action: After this supersession record is merged, create a separate trigger-only PR from fresh develop that adds exactly ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json, execute the corrected canonical Phase 6 workflow once, close the trigger without merge after evidence collection, and replace the superseded durable conclusion only from the corrected artifact.
```
