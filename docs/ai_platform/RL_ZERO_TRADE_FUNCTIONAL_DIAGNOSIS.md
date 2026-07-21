# RL Zero-Trade Functional Diagnosis

## Scope

This document classifies why the completed frozen `rl-research-v1` historical execution produced
zero trades. It is diagnosis-only. It does not authorize a new training run, backtest, OOS rerun,
reward search, feature search, parameter change, promotion, cross-track selection, or protected
final-holdout access.

The source execution is GitHub Actions run `29844351936`, track `rl-research-v1`, with durable
evidence in:

`ai_platform/experimental_model_research/evidence/rl-research-v1-historical-oos-v1.json`

The protected final holdout `20260801-20260930` was not used.

## Classification

Primary diagnosis:

**reward-induced neutral-policy collapse / inactive-policy attractor**

The available evidence does not support a model-runtime failure, action-number mismatch,
strategy/action-space integration drift, systemic `do_predict` gating failure, configuration identity
mismatch, or strict-OOS extraction error as the cause of the zero-trade result.

The diagnosis is based on the preserved execution evidence, the canonical strategy/model/config
source, and the FreqAI RL prediction contract. The exact per-candle action histogram was not preserved
in the artifact, so this document does not claim that every valid model prediction was directly
observed to be action `0`. It concludes that no actionable long-entry signal reached the backtester,
and that the configured reward structure gives a deterministic neutral policy a structurally safe
zero-reward solution with no positive incentive to enter.

## Evidence that runtime and training completed

The preserved backtest log shows, for both `BTC/USDT` and `ETH/USDT`:

- the custom `LongOnlyReinforcementLearner` was resolved successfully;
- one training timerange was used;
- training started and completed;
- training used 272 features and 6878 training points per pair;
- the evaluation callback found a best model;
- prediction processing completed;
- the backtest completed successfully with no runtime exception.

The run summary records `status: success`, the canonical FreqAI identifier
`ai-platform-rl-research-v1`, and `total_trades: 0`.

Therefore the zero-trade result is not explained by failure to instantiate, train, load, or execute
the RL model.

## Evidence that strict-OOS extraction did not remove trades

The strict-OOS evidence records:

- `input_trades: 0`;
- `included_trades: 0`;
- `excluded_trades: 0`.

The full backtest result also records zero trades over `20260301-20260701`.

Therefore the strict historical-OOS extractor did not transform an active run into a zero-trade
result. The inactivity originated before extraction, in the backtest signal/action path.

## Action-space mapping is internally consistent

The custom environment defines:

```text
Neutral    = 0
Long_enter = 1
Long_exit  = 2
```

The action space is `Discrete(3)`.

The strategy uses exactly the same mapping:

- enter long when `&-action == 1` and `do_predict == 1`;
- exit long when `&-action == 2` and `do_predict == 1`.

FreqAI's RL prediction path creates the output dataframe using the strategy label list and writes
model predictions into that output. The strategy label is `&-action`. The canonical placeholder
assignment `dataframe["&-action"] = 0` is therefore a target/label declaration and is not, by itself,
evidence that FreqAI predictions were forced to zero after `self.freqai.start()`.

No action-number mismatch is present between the custom environment and strategy.

## Prediction gating was not systemically disabled

The execution log reports only 18 dropped prediction rows out of 11712 prediction rows for each pair
due to NaNs. The RL configuration disables DI-based filtering and other configured outlier-removal
paths that could otherwise suppress a large part of inference.

This does not preserve an exact `do_predict` histogram, but it rules against the hypothesis that the
entire prediction interval was rejected by data-quality or uncertainty gating.

The backtest summary also reports zero rejected signals, so there is no evidence that a stream of
valid entry signals was produced and then rejected by ordinary backtest capacity rules.

## Root cause in the reward geometry

The custom reward function has the following relevant behavior.

When the environment is neutral:

- `Neutral` is valid and returns reward `0.0`;
- `Long_enter` is valid and also returns reward `0.0`;
- `Long_exit` is invalid and returns reward `-1.0`.

After entering a long position:

- remaining `Neutral` receives an increasingly negative duration penalty;
- `Long_exit` receives realized decision-time unrealized PnL multiplied by `100`;
- invalid actions receive `-1.0`.

This creates an asymmetric optimization problem:

1. A policy that remains neutral forever can collect exactly zero reward without exposure to
   holding penalties, invalid-action penalties, or negative exits.
2. Entering a position receives no immediate positive reward compared with staying neutral.
3. Once a position is opened, the policy becomes exposed to negative holding penalties and possibly
   negative exit rewards.
4. The configured environment starts neutral and `randomize_starting_position` is `false`.
5. Training uses only `train_cycles: 1`, and inference/evaluation is deterministic.

The default Freqtrade demonstration reward deliberately contains the opposite incentives for the
neutral state: it rewards a valid entry and penalizes staying neutral. The custom long-only reward
removed both of those terms.

The resulting custom objective therefore contains a simple zero-risk local optimum: **never enter**.
The observed zero-trade backtest is consistent with the learned policy converging to or selecting
that neutral solution.

## Secondary observability limitation

The configuration uses:

```text
add_state_info = false
policy_type = MlpPolicy
```

The environment's validity and reward depend on whether its internal position is `Neutral` or
`Long`, but with `add_state_info = false` that position is not explicitly included in the policy
observation. A memoryless MLP policy therefore does not receive direct position state while learning
a state-dependent action contract.

This is not required to explain the zero-trade result, and it is not classified as a proven runtime
bug. It is a secondary design limitation that can further favor a conservative neutral policy and
should be explicitly addressed in any future RL research design.

## Hypotheses rejected by the available evidence

### Model/runtime failure

Rejected. Training, best-model selection, prediction processing, and backtest completion all
succeeded for both pairs.

### Action-space numbering mismatch

Rejected. Environment and strategy both use `0 = Neutral`, `1 = Long_enter`, `2 = Long_exit`.

### Strict-OOS extraction error

Rejected. The full source backtest already contained zero trades.

### Systemic prediction rejection

Not supported. Only a small number of prediction rows were dropped for NaNs; no evidence shows the
whole interval being gated by `do_predict`.

### Ordinary trade-capacity rejection

Not supported. The backtest reports zero rejected signals and permits up to two simultaneous trades.

## Evidence limitation

The one-shot artifact did not preserve:

- the backtesting prediction feather files containing the action sequence;
- an explicit action-frequency histogram for deterministic inference;
- the trained model files;
- TensorBoard action counters.

Consequently the exact number of predicted `Neutral`, `Long_enter`, and `Long_exit` actions cannot be
reconstructed after artifact collection.

This limits direct action-sequence proof, but does not change the structural diagnosis: the execution
path worked, no trades existed before extraction, mapping is consistent, and the custom reward makes
permanent neutrality an unpenalized solution while entry has no positive incentive.

## Bounded recommendation for any future task

Any follow-up must be a new, prospectively declared work package. It must not modify or rerun the
consumed strict historical OOS `20260501-20260630`, and it must not access the protected final holdout
`20260801-20260930`.

A future RL-v2 research task should, before any new historical execution:

1. define a reward contract that removes the risk-free always-neutral optimum, with explicit unit
   tests for neutral-state and entry incentives;
2. define how the policy receives or avoids dependence on position state during both training and
   historical inference;
3. preserve deterministic inference action counts (`Neutral`, `Long_enter`, `Long_exit`) as mandatory
   evidence;
4. preserve `do_predict` counts and signal counts before Freqtrade trade execution;
5. use a fresh, prospectively declared non-protected evaluation window that has not been consumed by
   this diagnosis or previous tuning;
6. keep the track isolated from completed Phase 6 and from the protected Phase 5 final holdout.

Switching algorithms, changing rewards, adding state information, changing action masking, or
altering features are research changes and are explicitly out of scope for this diagnosis-only task.

## Conclusion

The zero-trade RL result is best classified as a **functionally successful execution with a
degenerate inactive policy**, primarily caused by a reward geometry that makes permanent neutrality
a safe zero-reward solution and provides no positive reward for entering a valid long position.

There is no evidence that the zero-trade result was caused by model-runtime failure, action mapping,
strict-OOS extraction, or broad prediction gating. A future RL redesign may be justified, but it must
be a new bounded research task with fresh evaluation data and improved action-level observability.
