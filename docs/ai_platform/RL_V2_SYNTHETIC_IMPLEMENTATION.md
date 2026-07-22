# RL-v2 Synthetic Implementation

## Status

`rl-v2-synthetic-implementation-v1` is a **synthetic-only reference layer**.

It implements no FreqAI model, no Freqtrade strategy, no config, no experiment manifest, and no
execution workflow. It performs no training, backtest, market-data download, historical-OOS
execution, Hyperopt, performance evaluation, promotion, or live trading.

Canonical descriptor:

`ai_platform/experimental_model_research/rl-v2-synthetic-implementation-v1.json`

Reference implementation:

`ai_platform.scripts.rl_v2_synthetic_reference`

Parent design contract:

`ai_platform/experimental_model_research/rl-v2-design-contract-v1.json`

## Selected design mode

This bounded task selects the design-contract-authorized mode:

`position_independent_action_semantics`

The policy-facing action means the desired position:

```text
0 = target_flat
1 = target_long
```

The action meaning is stable regardless of current trade state. A pure transition adapter uses the
externally owned current state only to translate desired position into a lifecycle event:

```text
flat + target_flat -> hold_flat
flat + target_long -> enter_long
long + target_long -> hold_long
long + target_flat -> exit_long
```

The synthetic training-style and historical-inference-style adapters call the same canonical
transition function. This proves action-meaning parity without assuming that FreqAI `add_state_info`
is available during backtesting.

This does not yet prove that a concrete FreqAI model/strategy integration is correct. Runtime
integration is a separate later task.

## Prospectively frozen synthetic reward reference

The following constants were selected in the task declaration before implementation and were not
chosen from historical-OOS performance:

```text
flat_neutral_reward                 = -0.01
valid_long_entry_reward             =  0.00
holding_profit_clip_abs             =  0.02
holding_duration_penalty_per_step   =  0.0001
holding_duration_penalty_cap        =  0.01
exit_profit_clip_abs                =  0.05
invalid_action_penalty              = -1.00
```

The pure reward reference has these semantics:

### Flat state

- `target_flat` returns `-0.01`;
- `target_long` returns `0.0`.

Therefore valid entry is strictly preferred to remaining flat, and a policy that remains flat for an
entire episode accumulates negative reward rather than receiving the RL-v1 safe zero-reward outcome.

### Long state

- `target_long` returns current decision-time unrealized profit clipped to `[-0.02, 0.02]`, minus a
  duration penalty capped at `0.01`;
- `target_flat` returns current decision-time unrealized profit clipped to `[-0.05, 0.05]`.

The holding reward is therefore bounded to `[-0.03, 0.02]` under the frozen reference values.

Unsupported action codes return `-1.0`.

The pure function accepts only explicitly supplied current position, desired-position action,
decision-time unrealized profit, and duration steps. It has no candle series, future return, shifted
price, or other future-market input.

These constants are reference values for deterministic synthetic proof only. This task produces no
claim that they are profitable or optimal, and it does not authorize changing them based on consumed
historical OOS.

## Observability accumulator

`RLV2ObservabilityAccumulator` provides the dependency-light counter layer required before a later
runtime integration may be evaluated.

For every declared pair, snapshots preserve:

- desired-position action counts for `target_flat` and `target_long`, including zero-count actions;
- `do_predict` accepted and rejected counts;
- pre-trade entry and exit signal counts.

The snapshot also keeps separately attributable:

- raw backtest trade count;
- strict-OOS input trade count;
- strict-OOS included trade count;
- strict-OOS excluded trade count.

Strict-OOS counts fail closed unless:

```text
included + excluded = input
```

Snapshots are deterministic and JSON serializable. The accumulator deliberately does not execute a
trade or interpret performance.

## Contract binding

The synthetic descriptor cannot validate unless the checked-in merged RL-v2 design contract first
passes its own exact fail-closed validator.

The synthetic validator then requires exact descriptor identity and verifies that the selected
`position_independent_action_semantics` mode is one of the parent contract's allowed design modes.

Validate with:

```bash
python -m ai_platform.scripts.rl_v2_synthetic_reference
```

Print the canonical descriptor with:

```bash
python -m ai_platform.scripts.rl_v2_synthetic_reference --print-canonical
```

Run targeted tests with:

```bash
pytest -q tests/ai_platform/test_rl_v2_synthetic_reference.py
```

## Evaluation isolation

This task does not select an evaluation window.

The following remain forbidden:

- consumed historical OOS `20260501-20260630`;
- protected final holdout `20260801-20260930`.

The protected final holdout remains unused and unavailable under its existing prospective boundary.

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

## What this proves

This bounded task proves synthetically that:

- the policy-facing desired-position action meaning is independent of hidden current-position state;
- training-style and inference-style transition adapters use identical semantics;
- the frozen reference reward removes RL-v1's unpenalized perpetual-flat solution;
- holding and exit rewards are bounded using explicitly supplied decision-time state;
- invalid actions are penalized;
- the future observability layers can preserve action, prediction-gate, signal, raw-trade, and
  strict-OOS counts separately.

It does **not** prove that a concrete FreqAI integration will train successfully, generate trades, or
be profitable.

## Next bounded dependency task

After this task is merged and frozen, the next safe task is a **runtime-integration-only RL-v2
implementation** that wires the synthetic reference semantics and observability into a new isolated
model/strategy surface with unit and synthetic integration tests.

That later task still must not train, backtest, download market data, choose an evaluation window, or
consume historical OOS. A fresh prospective evaluation declaration and one-shot execution carrier
remain separate later work packages.
