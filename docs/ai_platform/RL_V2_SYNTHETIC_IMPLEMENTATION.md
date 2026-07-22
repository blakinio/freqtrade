# RL-v2 Synthetic Implementation

## Status

`rl-v2-synthetic-implementation-v1` is a **synthetic-only** reference layer implementing the first concrete design mode allowed by `rl-v2-design-contract-v1`.

Selected design mode:

`position_independent_action_semantics`

This work does not create a FreqAI model, strategy, Freqtrade config, experiment manifest, execution workflow, training run, backtest, market-data download, strict-OOS execution, or performance result.

Machine-readable descriptor:

`ai_platform/experimental_model_research/rl-v2-synthetic-implementation-v1.json`

Pure reference module:

`ai_platform.scripts.rl_v2_synthetic_reference`

## Desired-position action semantics

The policy-facing action contract is intentionally position-independent:

- `0 = target_flat`
- `1 = target_long`

The action always expresses the desired position. Its semantic meaning does not change depending on hidden current-position state.

The synthetic training-style and inference-style paths call the same mapping function, so the parity proof is structural rather than inferred from model behavior.

This does not yet define how a future FreqAI model or strategy will translate desired-position actions into order transitions. That integration remains a later bounded task.

## Prospective reward reference

The reference reward constants are fixed prospectively for synthetic proof only and were not tuned against historical OOS data:

- invalid action: `-1.0`;
- `target_flat` while already flat: `-0.1`;
- `target_long` while flat: `+0.1`;
- holding while long: bounded from `0.0` to `-0.01` using a clipped trade-duration ratio;
- `target_flat` while long: supplied decision-time unrealized-profit percentage multiplied by `100`.

The important contract property is relational:

`flat-neutral reward < valid long-target reward`

Therefore a perpetual flat-neutral episode accumulates negative reward instead of remaining an unpenalized zero-reward solution.

The reference reward is a pure function of explicitly supplied decision-time state. It does not read candles, future rows, market data, or global trading state.

These constants are not evidence of profitability and are not authorized for tuning against consumed historical OOS or the protected final holdout.

## Synthetic observability accumulator

The reference accumulator preserves all layers required by the merged design contract:

- deterministic action counts by pair and action;
- zero-count action buckets;
- `do_predict` accepted/rejected counts by pair;
- pre-trade entry/exit signal counts by pair;
- raw backtest trade count;
- strict-OOS input/included/excluded trade counts.

The snapshot is deterministic and JSON-serializable. Raw backtest and strict-OOS counts remain independently attributable.

The accumulator is only a reference primitive. This task does not connect it to a backtest or live runtime.

## Design-contract binding

The synthetic descriptor validates the checked-in `rl-v2-design-contract-v1` before exposing its implementation identity.

The selected mode must:

1. be present in the design contract's allowed mode list; and
2. equal `position_independent_action_semantics` for this bounded task.

Descriptor drift, runtime authorization drift, evaluation-isolation drift, Phase 6 drift, or frozen-threshold drift causes validation to fail.

## Evaluation isolation

The following remain forbidden:

- consumed historical OOS `20260501-20260630`;
- protected final holdout `20260801-20260930`.

No future evaluation window is selected by this task.

The protected final holdout remains unused and unavailable before `2026-10-01T00:00:00Z` under its existing prospective declaration.

## Phase 5 and Phase 6 isolation

The synthetic implementation preserves:

- frozen candidate thresholds `0.006/-0.009`;
- authoritative Phase 6 `selected_model = null`;
- no RL-v2 Phase 6 membership;
- no Phase 6 consumption of synthetic or future RL-v2 results.

## Validation

Validate the checked-in descriptor and design-contract binding with:

```bash
python -m ai_platform.scripts.rl_v2_synthetic_reference
```

Print the canonical descriptor with:

```bash
python -m ai_platform.scripts.rl_v2_synthetic_reference --print-canonical
```

Run targeted synthetic tests with:

```bash
pytest -q tests/ai_platform/test_rl_v2_synthetic_reference.py
```

The tests cover:

- training/inference desired-position action parity;
- unknown-action fail-closed behavior;
- flat-neutral versus valid-long reward ordering;
- negative perpetual-neutral episode reward;
- invalid-action penalty;
- bounded holding reward;
- decision-time-only flatten reward inputs;
- zero-count action observability;
- separate action, `do_predict`, signal, raw-trade and strict-OOS counters;
- descriptor isolation and design-mode drift rejection.

## What comes next

After this synthetic-only layer is merged and closed, a separately declared integration task may implement a concrete RL-v2 FreqAI model/strategy adapter that consumes the desired-position semantics and observability primitives while still using synthetic or minimal pre-OOS validation only.

That later task must remain separate from any historical execution. Selection of a fresh evaluation window and any real backtest require another prospective work package after the integration is frozen.
