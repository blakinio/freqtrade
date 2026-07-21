---
task_id: FTAI-20260722-rl-zero-trade-functional-diagnosis
status: ready
branch: research/rl-zero-trade-functional-diagnosis-v1
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "pending"
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-zero-trade-functional-diagnosis.md
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EVIDENCE.md
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/configs/freqai-rl-research.example.json
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
search_first:
  - merged PR #95 and current develop before diagnosis work
  - closed execution-carrier PR #94 and workflow run 29844351936
  - open PRs or active tasks overlapping RL research ownership
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
head: a86cd0004e87f14c96c01b9fb956d91a34f59796
branch: research/rl-zero-trade-functional-diagnosis-v1
pr: pending diagnosis PR
status: ready
context_routes:
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
  - ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-zero-trade-functional-diagnosis.md
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
proven:
  - Task declaration PR #97 was squash-merged as f3b8230bd30e977a988c2dc54bb2e0a422037217 before diagnosis work began.
  - Diagnosis used the preserved RL artifact 8503197359 from workflow run 29844351936 and exact execution commit af9e27c48c9f2bf4e7277d09fe5eaec2ee020af3.
  - The source backtest completed successfully with total_trades 0 and rejected_signals 0; strict OOS extraction received input_trades 0 and therefore did not discard trades.
  - Both BTC/USDT and ETH/USDT models trained successfully, saved callback-selected best models, and generated prediction data without runtime exceptions.
  - Prediction preparation dropped only 18 of 11712 rows per pair because of NaNs, ruling out blanket do_predict suppression.
  - Action numbering is consistent across the executed custom environment and strategy: neutral 0, long entry 1, long exit 2.
  - The custom reward returns 0 for neutral while flat and 0 for valid long entry, penalizes neutral while long, and rewards/penalizes exit only through unrealized PnL.
  - Both pair-training evaluations logged episode_reward 0.00 +/- 0.00 and were accepted as new best mean reward before the best model was returned.
  - The FreqAI example reward at the same execution commit positively rewards entry and penalizes remaining neutral while flat; the custom reward removed both anti-inactivity shaping terms.
  - Configured rr and profit_aim remain present but are not consumed by the custom calculate_reward implementation.
  - Protected final holdout 20260801-20260930 remained unused and no new model execution or backtest was run during diagnosis.
  - The durable artifact does not contain backtesting prediction files, saved models, TensorBoard action counters, or a per-action inference histogram.
derived:
  - Primary cause is reward-objective degeneracy that makes permanent neutrality a safe zero-reward attractor; evidence strongly supports neutral-policy collapse rather than downstream integration failure.
  - Backtesting position state is unavailable through add_state_info by FreqAI core contract; this is a secondary design constraint, not required to explain the zero-trade outcome.
  - A future reward redesign should be validated first with unit and deterministic synthetic-environment tests, not by rerunning the consumed historical OOS window.
unknown:
  - Exact inference counts for actions 0, 1 and 2 cannot be reconstructed from the preserved artifact.
conflicts: []
first_failure:
  marker: reward-neutral-policy-collapse
  evidence: A permanently neutral policy receives deterministic cumulative reward 0 while entering receives no immediate incentive and exposes the policy to holding and losing-exit penalties; both deterministic evaluation runs achieved exactly reward 0 and the final backtest made zero trades.
rejected_hypotheses:
  - Model loading or training failure caused the zero-trade result.
  - Action enum mismatch between the custom environment and strategy caused the zero-trade result.
  - Strict OOS extraction discarded real trades.
  - Blanket do_predict suppression removed all possible signals.
  - Retune reward, features, thresholds or model parameters from the consumed historical OOS result.
  - Rerun the same consumed historical OOS after a reward or strategy change.
  - Use protected final holdout data or rank RL against PyTorch inside this task.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-zero-trade-functional-diagnosis.md
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
validation:
  - command: preserved artifact integrity and source backtest inspection
    result: PASS
    evidence: Durable artifact hash was already verified by PR #95; run-summary, backtest archive, backtest.log and strict OOS extraction consistently report a successful zero-trade source execution.
  - command: exact execution-commit action and prediction-path source review
    result: PASS
    evidence: Custom action values and strategy gates align; FreqAI RL prediction writes deterministic model actions into the label dataframe and no conflicting action translation was found.
  - command: exact execution-commit reward-contract review
    result: PASS
    evidence: Custom reward permits neutral-forever reward 0, while the preserved deterministic evaluation reward is exactly 0.00 for both trained pairs.
  - command: diagnosis-only boundary review
    result: PASS
    evidence: No training, model execution, historical rerun, parameter change, final-holdout access, Phase 6 change or cross-track selection occurred.
blockers: []
next_action: Open and merge the diagnosis-only PR preserving this root-cause record; any reward-contract hardening or observability implementation must begin as a separate prospectively declared bounded task.
```
