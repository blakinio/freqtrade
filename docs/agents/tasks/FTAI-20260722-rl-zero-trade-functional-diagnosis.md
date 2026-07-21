---
task_id: FTAI-20260722-rl-zero-trade-functional-diagnosis
status: active
branch: docs/rl-zero-trade-functional-diagnosis
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "100"
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-zero-trade-functional-diagnosis.md
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EVIDENCE.md
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/configs/freqai-rl-research.example.json
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
search_first:
  - PR #100 live state and current develop before task closure
  - closed execution-carrier PR #94 and workflow run 29844351936
  - merged durable evidence PR #95
optional_reads:
  - workflow artifact 8503197359
  - freqtrade/freqai/prediction_models/ReinforcementLearner.py
  - freqtrade/freqai/RL/BaseReinforcementLearningModel.py
  - freqtrade/freqai/RL/BaseEnvironment.py
---

# RL zero-trade functional diagnosis

## Goal

Determine, without any new model execution or tuning, why the completed frozen `rl-research-v1` historical execution produced zero trades. Distinguish an expected learned no-trade policy from strategy/action gating, action-space integration drift, model/runtime failure, configuration mismatch, or evidence-extraction error. Produce a durable functional root-cause assessment and a bounded recommendation for any later work package.

## Non-negotiable boundaries

- Diagnosis only: no training, backtest rerun, OOS rerun, Hyperopt, reward search, feature search, model-parameter change, threshold change, or strategy behavior change.
- Do not reuse consumed strict historical OOS `20260501-20260630` for tuning or post-fix validation.
- Do not access protected final holdout `20260801-20260930`.
- Do not rank PyTorch versus RL or invent a retrospective cross-track selection policy.
- Do not change completed Phase 6, its frozen candidates, selection policy, or authoritative `selected_model = null` conclusion.
- Any runtime/model fix or fresh evaluation must be a separate prospectively declared bounded task after this diagnosis is complete.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T00:30:00+02:00
head: 2fd283d26edf05d505a8c951e0f0cdc375f900b1
branch: docs/rl-zero-trade-functional-diagnosis
pr: 100
status: ready
context_routes:
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EVIDENCE.md
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-zero-trade-functional-diagnosis.md
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
proven:
  - Workflow run 29844351936 completed one frozen RL historical backtest successfully and durable evidence was merged by PR #95.
  - The full source backtest contained zero trades, and strict-OOS extraction had input_trades 0, included_trades 0 and excluded_trades 0; extraction did not remove activity.
  - The backtest log shows successful model resolution, training and best-model selection for both BTC/USDT and ETH/USDT, so no model-runtime failure explains the inactivity.
  - Prediction processing completed and only 18 of 11712 prediction rows per pair were dropped for NaNs, which does not support systemic prediction gating.
  - The custom environment and strategy both map Neutral 0, Long_enter 1 and Long_exit 2; no action-number mismatch exists.
  - FreqAI RL prediction writes model actions into the strategy label column &-action; the strategy target placeholder value 0 does not by itself force post-start predictions to zero.
  - The custom reward returns 0 for Neutral while neutral and also 0 for valid Long_enter while neutral, while invalid actions are penalized.
  - After entry, holding neutral receives a duration penalty and Long_exit reward depends on PnL, so entering creates downside while permanent neutrality remains a zero-reward solution.
  - The environment starts neutral, randomize_starting_position is false, train_cycles is 1 and deterministic evaluation/inference is used, reinforcing the neutral-policy attractor.
  - add_state_info is false with memoryless MlpPolicy, so the policy lacks explicit position state even though action validity and reward depend on internal position; this is a secondary design limitation, not a proven runtime failure.
  - The execution artifact did not preserve deterministic action-frequency counts, prediction feather files, trained models or TensorBoard action counters, so the exact per-candle action histogram cannot be reconstructed.
  - Primary diagnosis is reward-induced neutral-policy collapse / inactive-policy attractor, with no evidence of runtime, action-mapping, extraction or broad prediction-gating failure.
  - Frozen thresholds 0.006/-0.009, completed Phase 6 selected_model null and protected final holdout 20260801-20260930 remain unchanged.
derived:
  - A future RL-v2 task should remove the risk-free always-neutral optimum, define position-state observability explicitly and preserve action/do_predict/signal histograms before any fresh execution.
  - Any future RL redesign and evaluation must use a new prospectively declared bounded task and fresh non-protected evaluation data.
unknown:
  - Exact deterministic inference counts for Neutral, Long_enter and Long_exit cannot be recovered from the preserved artifact.
conflicts: []
first_failure:
  marker: none
  evidence: Functional diagnosis is complete; no unresolved execution-path defect is required to explain the zero-trade outcome.
rejected_hypotheses:
  - Tune reward, features, thresholds or model parameters again from the consumed historical OOS result.
  - Rerun the same consumed historical OOS after changing model or strategy behavior.
  - Treat zero trades as proof of profitability, robustness or superiority.
  - Compare or rank RL against PyTorch inside this diagnosis-only task.
  - Use protected final holdout data to diagnose or validate the RL track.
changed_paths:
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
  - docs/agents/tasks/FTAI-20260722-rl-zero-trade-functional-diagnosis.md
validation:
  - command: preserved artifact and source inspection
    result: PASS
    evidence: RL artifact 8503197359, run log, run summary, strict-OOS extraction and canonical FreqAI RL source were inspected without model execution or data rerun.
  - command: PR #100 repository gates
    result: PENDING
    evidence: Diagnosis PR is open against develop; exact final CI identifiers will be recorded before merge.
blockers: []
next_action: Let PR #100 complete required repository gates, then update this checkpoint to status done with exact final CI identifiers and squash-merge the diagnosis-only work package. Do not implement RL-v2 changes inside this task.
```
