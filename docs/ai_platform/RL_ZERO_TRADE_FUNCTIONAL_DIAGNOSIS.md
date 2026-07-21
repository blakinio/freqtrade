# RL zero-trade functional diagnosis

## Scope

This document diagnoses the completed frozen `rl-research-v1` historical execution that produced zero trades. It is evidence-only analysis. No training, historical backtest rerun, OOS rerun, reward tuning, feature tuning, model-parameter tuning, threshold change, promotion, live trading, Phase 6 change, cross-track selection, or protected-final-holdout access was performed.

The diagnosis is bound to execution commit `af9e27c48c9f2bf4e7277d09fe5eaec2ee020af3`, workflow run `29844351936`, and RL evidence artifact `8503197359`.

## Conclusion

The primary functional cause is **reward-objective degeneracy leading to a neutral/no-trade policy collapse**, not a demonstrated FreqAI action-mapping, strategy-gating, runtime, or evidence-extraction failure.

Confidence: **high** for the reward-contract defect and **moderate-to-high** that it is the direct cause of the observed zero-trade backtest.

The exact inference action histogram was not preserved in the durable artifact, so this diagnosis does not claim that every individual prediction was action `0`. The available evidence nevertheless strongly supports a neutral-policy collapse and provides no positive evidence for a downstream integration failure.

## Evidence

### 1. The historical execution completed normally

The preserved `run-summary.json` records:

- status `success`;
- exactly one Freqtrade `backtesting` command;
- strategy `AiLongOnlyRLResearchStrategy`;
- model `LongOnlyReinforcementLearner`;
- execution range `20260301-20260701`;
- fee `0.002`;
- `total_trades = 0`;
- `rejected_signals = 0`.

The backtest log shows that FreqAI resolved the custom model, trained BTC/USDT and ETH/USDT independently, found a best model for both pairs, generated backtesting predictions, and completed the 122-day backtest. There is no runtime exception or model-loading failure in the preserved log.

Prediction preparation dropped only 18 of 11,712 prediction rows per pair because of NaNs. This rules out blanket `do_predict = 0` suppression as a credible explanation for the entire zero-trade result.

### 2. Evidence extraction did not hide existing trades

The source backtest archive itself contains an empty trade list and reports zero total trades. The strict OOS extractor received `input_trades = 0`, included zero trades, and excluded zero trades.

Therefore the strict OOS result is faithfully reporting a zero-trade source backtest rather than losing trades during window filtering or evidence extraction.

### 3. Action numbering is internally consistent

The exact execution code defines:

- `Neutral = 0`;
- `Long_enter = 1`;
- `Long_exit = 2`.

The strategy consumes the same values:

- `&-action == 1` creates `enter_long` when `do_predict == 1`;
- `&-action == 2` creates `exit_long` when `do_predict == 1`.

FreqAI RL prediction code returns deterministic model actions directly in the model label dataframe. No conflicting action-number translation was found between the custom environment, FreqAI prediction path, and strategy.

### 4. The custom reward makes inactivity a safe zero-reward solution

The executed `LongOnlyEnvironment.calculate_reward()` has these effective incentives:

- invalid action: `-1.0`;
- neutral while flat: `0.0`;
- enter long while flat: `0.0`;
- neutral while long: a progressively negative duration penalty;
- exit long: unrealized PnL multiplied by `100`.

Because every episode starts neutral, an agent that remains neutral forever receives a deterministic cumulative reward of exactly zero and avoids all invalid-action, holding-duration, fee, and losing-exit risk.

An agent that enters receives no immediate positive reward. Once long, remaining neutral becomes negatively rewarded, and the eventual exit reward depends on realized market outcome after fees. The custom reward therefore provides no pressure to leave the flat state while making trading capable of producing negative cumulative reward.

This creates a direct neutral-policy attractor.

### 5. Training evaluation matches the neutral-policy attractor

The preserved backtest log records, for both pair trainings:

`Eval num_timesteps=6878, episode_reward=0.00 +/- 0.00`

and the callback immediately treats that evaluation as a new best mean reward.

The production FreqAI `ReinforcementLearner.fit()` returns the callback-selected best model when `best_model.zip` exists. Both BTC and ETH training runs logged `Callback found a best model.`

A deterministic zero-reward evaluation is exactly consistent with a policy that remains neutral for the full episode under this custom reward contract.

### 6. The custom reward removed the anti-inactivity shaping present in the FreqAI example

At the exact execution commit, the upstream/example `ReinforcementLearner.MyRLEnv.calculate_reward()` explicitly:

- rewards a valid long entry with `+25`;
- penalizes neutral action while neutral with `-1`.

The custom long-only environment removed both mechanisms. It also does not use the configured `rr` and `profit_aim` values in its reward calculation, even though those parameters remain present in `model_reward_parameters`.

This does not mean the upstream example reward should be copied into production. It does show that the custom feasibility reward eliminated the mechanisms that prevented a flat forever policy from being reward-neutral.

## Secondary design findings

### Backtesting cannot use position state through `add_state_info`

Freqtrade core explicitly rejects `add_state_info = true` for backtesting. The frozen config correctly sets it to `false`.

As a result, the backtest inference policy cannot receive current trade position, current profit, or trade duration as additional state. This is a known FreqAI RL backtesting constraint, not a configuration error in this run. It should still be considered in any future RL design because action validity is position-dependent while the prediction input is market-feature-only.

This constraint is not required to explain the observed zero trades; the reward degeneracy is sufficient and better supported by the evidence.

### Training budget may amplify the collapse but is not diagnosed as the root cause

The frozen config uses one training cycle. A small training budget can make policy exploration weaker, but changing `train_cycles`, PPO parameters, architecture, reward parameters, or features from this consumed OOS result would be retrospective tuning and is outside this task.

## Ruled out or unsupported causes

The evidence does **not** support these as the primary cause:

- model failed to load;
- model training crashed;
- FreqAI skipped all predictions;
- action enum mismatch between environment and strategy;
- Freqtrade rejected a stream of generated entry signals;
- strict OOS extraction discarded real trades;
- the zero result demonstrates profitability or robustness.

## Evidence gap

The one-shot evidence artifact intentionally preserved the backtest archive, logs, manifests, provenance, and strict OOS extraction, but not the FreqAI backtesting prediction feather files, saved model, TensorBoard action counters, or a per-action inference histogram.

Therefore the exact counts of predicted actions `0/1/2` cannot be reconstructed from the durable artifact alone.

A future execution-observability design should, before any new evaluation, prospectively persist non-sensitive aggregate action counts and `do_predict` counts so inactivity can be classified without retaining large model artifacts. Adding that observability must not authorize a rerun of the already-consumed OOS window.

## Functional classification

`rl-research-v1` should be classified as:

**execution-integrated, evidence-valid, behaviorally inactive due to a reward contract that permits neutral-policy collapse**.

It should **not** be classified as a validated trading model, a profitable model, a selected model, or a demonstrated runtime-integration failure.

## Recommended next bounded work package

The next safe work package is a **reward-contract hardening and synthetic environment validation** task, not another historical OOS run.

That work package may:

- redesign reward semantics prospectively without using consumed OOS metrics as tuning targets;
- add unit tests for action validity and reward ordering;
- add deterministic synthetic-price environment tests that verify the reward contract does not make permanent neutrality a uniquely safe optimum;
- add prospective action-count observability for a future execution;
- document the backtesting state-information limitation.

It must not:

- rerun or tune against consumed strict OOS `20260501-20260630`;
- access protected final holdout `20260801-20260930`;
- change frozen Phase 6 conclusions;
- rank RL against PyTorch;
- claim that a redesigned reward improves trading performance until evaluated under a separately predeclared, unused validation contract.
