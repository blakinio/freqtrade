# RL-v2 Runtime Integration

## Status

`rl-v2-runtime-integration-v1` is a bounded **runtime-integration-only** layer.

It adds an isolated FreqAI model/environment adapter and research strategy that bind the merged RL-v2
synthetic desired-position semantics to the existing FreqAI reinforcement-learning extension surface.
It does not declare or run training, fitting, backtesting, market-data download, historical evaluation,
strict-OOS execution, performance extraction, promotion, or live trading.

Machine-readable descriptor:

`ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json`

Model/environment adapter:

`ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py`

Strategy adapter:

`ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py`

Parent synthetic reference:

`ai_platform.scripts.rl_v2_synthetic_reference`

## Runtime binding

The integration preserves the previously frozen runtime family choices without adding an execution
configuration:

- Stable-Baselines3 through the existing FreqAI `ReinforcementLearner` surface;
- PPO algorithm family;
- MLP policy family;
- long-only spot semantics;
- exactly two policy-facing actions.

A later separately declared execution task must supply any concrete FreqAI configuration. This task does
not create a config, experiment manifest, run request, timerange, or evaluation-window declaration.

## Desired-position action semantics

The policy-facing action space is exactly:

```text
0 = target_flat
1 = target_long
```

Both actions remain valid policy outputs regardless of current position. Current position is used only by
the environment adapter to translate the desired position into the canonical lifecycle transition:

```text
flat + target_flat -> hold_flat
flat + target_long -> enter_long
long + target_long -> hold_long
long + target_flat -> exit_long
```

`DesiredPositionEnvironment` delegates this translation to
`ai_platform.scripts.rl_v2_synthetic_reference.desired_position_transition`; it does not define a second
action-semantic mapping.

Unsupported action codes are outside the two-action Gym action space. If supplied directly to the reward
adapter they receive the prospectively frozen invalid-action penalty from the canonical synthetic reward
reference; they do not create a trade transition.

## Reward binding

`DesiredPositionEnvironment.calculate_reward()` delegates directly to
`ai_platform.scripts.rl_v2_synthetic_reference.reference_reward` using only:

- canonical current position (`flat` or `long`);
- desired-position action;
- current decision-tick unrealized profit;
- current trade duration in steps.

The runtime adapter does not duplicate or tune reward constants. The frozen values continue to live only
in `REWARD_REFERENCE` from the merged synthetic implementation.

Reward calculation occurs before the environment applies the desired-position transition and before the
market tick advances. No future candle or post-decision market value is passed into the reference reward.

## Strategy binding

`AiDesiredPositionRLResearchStrategy` inherits the existing research-only feature/target surface but
replaces policy interpretation with the RL-v2 desired-position contract:

- `do_predict == 1` and `target_long` (`&-action == 1`) emit long-entry intent;
- `do_predict == 1` and `target_flat` (`&-action == 0`) emit long-exit intent;
- no current-position state is required to interpret the policy output;
- no short-entry or short-exit action exists.

Freqtrade may naturally ignore an exit signal when no long trade is open; that execution-state behavior
does not change the policy-facing meaning of `target_flat`.

## Observability binding

The strategy exposes dependency-light binding hooks around the canonical
`RLV2ObservabilityAccumulator` rather than defining a new counter vocabulary.

For a prediction dataframe the adapter records, separately:

- deterministic desired-position action counts by pair, including the accumulator's zero-count buckets;
- `do_predict` accepted and rejected rows by pair;
- pre-trade entry and exit signal counts derived only after the `do_predict == 1` gate.

The parent accumulator continues to own raw-backtest and strict-OOS input/included/excluded counters. This
task does not populate those values because no backtest or strict-OOS execution is authorized.

## Heavy-runtime safety

The runtime model imports the existing FreqAI RL dependency surface, which may require the repository's
heavy `freqai_rl` dependency profile. The integration tests therefore validate descriptor identity,
synthetic-reference parity, and source/AST bindings without importing the heavy model or strategy modules.

This keeps lightweight CI capable of proving the contract without weakening the actual runtime adapter.
A later execution-preflight task may perform a minimal import/construction check only after explicitly
declaring the required dependency profile and still without training or historical evaluation.

## Evaluation isolation

No evaluation window is selected by this integration.

The following remain forbidden:

- consumed historical OOS `20260501-20260630`;
- protected final holdout `20260801-20260930`.

Frozen candidate thresholds remain:

```text
entry_prediction_threshold = 0.006
exit_prediction_threshold = -0.009
```

Completed Phase 6 remains authoritative with:

```text
selected_model = null
```

RL-v2 remains a separate research track outside Phase 6.

## Validation

Targeted validation is intentionally static/synthetic and must not execute the model:

```bash
pytest -q tests/ai_platform/test_rl_v2_runtime_integration.py
python -m ai_platform.scripts.rl_v2_synthetic_reference
```

Repository Python compile/Ruff checks may cover the new files when the heavy dependency profile is
available. No validation command for this task may train a model, download market data, run a backtest,
select an evaluation window, or access either forbidden timerange.

## Next bounded step

After this integration is reviewed, merged, and frozen, any real import/construction or execution work
requires a separately declared execution-preflight task. Historical training/evaluation and prospective
window declaration remain later, separately reviewed work packages.
