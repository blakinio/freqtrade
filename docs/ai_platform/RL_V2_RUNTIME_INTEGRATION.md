# RL-v2 Runtime Integration

## Status

`rl-v2-runtime-integration-v1` is a bounded, non-executing FreqAI runtime integration surface.

It adds a concrete model/environment adapter and a research strategy that reuse the merged RL-v2 synthetic desired-position semantics. It does not add a training config, experiment manifest, run request, evaluation window, historical execution, promotion path, or live-capital authorization.

Machine-readable descriptor:

`ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json`

Runtime model adapter:

`ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py`

Strategy adapter:

`ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py`

## Canonical dependency

The integration does not redefine the RL-v2 action or reward contract. It imports the merged pure reference from:

`ai_platform.scripts.rl_v2_synthetic_reference`

The runtime environment delegates to:

- `desired_position_transition` for lifecycle transitions;
- `reference_reward` for the prospectively frozen reward geometry;
- `desired_position_label` for stable action labels;
- `RLV2ObservabilityAccumulator` for the zero-initialized observability vocabulary.

The frozen policy-facing actions remain:

```text
0 = target_flat
1 = target_long
```

Both actions are valid policy outputs regardless of whether the externally owned current position is flat or long. Current position is used only by the canonical transition/reward adapter; it does not change the meaning of the policy-facing action.

## Environment mapping

`DesiredPositionEnvironment` exposes `Discrete(2)` and maps the canonical transitions as follows:

```text
flat + target_flat -> hold_flat
flat + target_long -> enter_long
long + target_long -> hold_long
long + target_flat -> exit_long
```

Reward calculation is delegated directly to `reference_reward` using only current decision-time unrealized profit and current trade duration supplied by the FreqAI environment.

Unsupported action codes are outside the declared action space, fail the validity mask, and receive the frozen invalid-action penalty when evaluated through the canonical reward reference.

## Strategy mapping

`AiDesiredPositionRLResearchStrategy` preserves long-only semantics:

- `do_predict == 1` and `target_long` emit `enter_long` intent;
- `do_predict == 1` and `target_flat` emit `exit_long` intent;
- rejected predictions emit neither intent;
- no short-entry or short-exit semantics exist.

The strategy does not need hidden current-position state to interpret the predicted action. The action itself always describes the desired position.

## Observability binding

The model adapter exposes a factory for the canonical `RLV2ObservabilityAccumulator`. A newly created accumulator preserves zero-count buckets for both desired-position actions and separately attributable counters for:

- accepted/rejected `do_predict` rows;
- pre-trade entry/exit signals;
- raw backtest trades;
- strict-OOS input/included/excluded trades.

This task does not fabricate runtime counts because it authorizes no execution.

## Heavy-runtime safety

The adapter follows the existing FreqAI `ReinforcementLearner` extension point and can use Stable-Baselines3 PPO with an MLP policy when a later separately declared config authorizes execution.

The bounded tests for this task remain dependency-light: they validate the machine-readable descriptor, compile/parse the new model and strategy source, prove direct binding to the canonical synthetic functions, and exercise the pure transition/reward/observability reference. They do not instantiate the heavy RL runtime, train a model, download data, or execute a backtest.

## Isolation and non-execution boundary

This integration deliberately contains no:

- training config;
- experiment manifest;
- run request;
- historical timerange or future evaluation-window declaration;
- market-data download;
- training or model fitting;
- backtest or strict-OOS execution;
- Hyperopt, reward search, feature search, or hyperparameter search;
- promotion, profitability, superiority, or live-trading claim.

Consumed historical OOS `20260501-20260630` remains forbidden. Protected final holdout `20260801-20260930` remains unused and forbidden under its existing prospective boundary.

Frozen Phase 5 thresholds remain `0.006/-0.009`. Completed Phase 6 remains authoritative with `selected_model = null`. RL-v2 remains a separate research track and is not ranked against PyTorch by this task.

## Next bounded step

After this runtime integration is merged and frozen, any execution work requires a new bounded task. That later task must first declare an execution preflight and, separately, a fresh prospective non-protected and unconsumed evaluation window before any result-producing run is authorized.
