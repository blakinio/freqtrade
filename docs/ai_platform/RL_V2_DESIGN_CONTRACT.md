# RL-v2 Design Contract

## Purpose

This document describes the fail-closed design contract for a future `rl-research-v2` track.

The contract addresses the completed RL-v1 diagnosis before any RL-v2 model, strategy, training,
backtest, market-data download, or evaluation window is created.

Canonical contract:

`ai_platform/experimental_model_research/rl-v2-design-contract-v1.json`

Validator:

`ai_platform/scripts/rl_v2_design_contract.py`

Source diagnosis:

`docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md`

## Current authorization

This is a design-only contract. It authorizes none of the following:

- model or strategy implementation;
- model training;
- historical backtesting;
- market-data download;
- historical OOS execution;
- promotion;
- live trading.

A later implementation task and a still-later prospectively declared execution task are required
before any RL-v2 historical model run can occur.

## Root-cause response

RL-v1 allowed a permanently neutral policy to collect zero reward while valid entry also received
zero immediate reward. Once a trade was opened, the policy became exposed to holding penalties and
market-dependent exit outcomes. The observed deterministic zero-reward evaluation and zero-trade
backtest were therefore consistent with a neutral-policy attractor.

RL-v2 makes the following requirements prospective:

- valid long entry must be strictly preferred to remaining neutral while flat;
- permanent neutral inactivity may not remain an unpenalized solution;
- invalid actions remain penalized;
- reward inputs must use decision-time information only;
- numeric reward values must be frozen before any later execution;
- unit and deterministic synthetic reward tests are required before execution.

The contract does not choose numeric reward magnitudes and does not authorize a reward sweep.

## Position-state and inference parity

The RL-v1 action contract used transition actions whose validity depended on hidden internal position
state, while Freqtrade backtesting does not make `add_state_info` available to the policy.

The RL-v2 design contract resolves this prospectively by changing the **policy contract**, not by
assuming unavailable state:

```text
0 = target_flat
1 = target_long
```

These are desired-position semantics. The policy states the desired position and does not need to
observe the current trade position merely to choose a valid transition action. Freqtrade remains the
owner of the actual trade lifecycle.

The future strategy translation is declared as:

```text
target_long -> enter-long candidate
target_flat -> exit-long candidate
```

A later implementation must prove with synthetic tests that training and historical inference use
the same desired-position semantics. No model or strategy implementing this design is added by this
contract task.

## Variable isolation

The first implementation slice keeps the following unchanged:

- algorithm: `PPO`;
- policy type: `MlpPolicy`;
- seed: `42`;
- existing feature set;
- no algorithm search;
- no feature search;
- no hyperparameter sweep;
- no reward sweep.

The bounded redesign scope is limited to:

1. reward-contract implementation;
2. desired-position action semantics;
3. execution observability;
4. unit tests;
5. deterministic synthetic-environment tests.

This prevents future results from being attributed to many simultaneous research changes.

## Mandatory future observability

RL-v1 evidence did not preserve the deterministic inference action sequence or sufficient pre-trade
signal diagnostics. A future RL-v2 run is incomplete unless durable evidence contains at least:

- deterministic action counts by pair and in total;
- accepted and rejected `do_predict` counts;
- entry and exit signal counts before Freqtrade trade-capacity/order handling;
- rejected-signal count;
- raw backtest trade count;
- strict-OOS input, included, and excluded trade counts;
- deterministic evaluation episode reward evidence;
- Git commit and FreqAI identifier;
- model class;
- config, strategy, model-source, and contract hashes.

Action, prediction-gate, and pre-trade-signal histograms must be persisted before transient workflow
artifacts can expire.

## Evaluation isolation

The contract permanently marks these windows as unavailable to RL-v2 redesign validation:

- consumed historical OOS: `20260501-20260630`;
- protected final holdout: `20260801-20260930`.

No RL-v2 evaluation window is declared here.

A future evaluation window must:

- be declared prospectively in a separate bounded task;
- use fresh non-protected data;
- not overlap either forbidden window;
- be frozen before execution;
- require a separate canonical execution request.

## Phase 5 and Phase 6 isolation

The frozen candidate thresholds remain:

```text
entry_prediction_threshold = 0.006
exit_prediction_threshold = -0.009
```

RL-v2 cannot use consumed OOS to change those values and cannot access the protected Phase 5 final
holdout.

RL-v2 remains outside completed Phase 6 and cannot alter its candidate set, selection policy,
evidence, or authoritative `selected_model = null` result.

## Fail-closed validator

Run the static validator with:

```bash
python ai_platform/scripts/rl_v2_design_contract.py \
  ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
```

The validator rejects the contract if it authorizes implementation or execution, weakens data
isolation, permits the neutral-policy attractor, relies on unavailable backtest state, changes the
bounded algorithm/search scope, omits mandatory evidence, or removes pre-execution gates.

## Pre-execution gates

No future RL-v2 training or historical backtest is authorized until a later work package proves:

- design-contract validation;
- reward unit tests;
- synthetic reward tests;
- desired-position action semantics tests;
- training/inference parity tests;
- execution-observability instrumentation;
- prospectively declared fresh evaluation window;
- forbidden-window overlap check;
- protected-final-holdout check;
- pinned canonical identity hashes.

## Next bounded work package

After this contract is merged, the next safe dependency task is an **implementation-only RL-v2
reward/action/observability harness** with unit and deterministic synthetic tests.

That implementation task must still prohibit historical training and backtesting. A fresh evaluation
window declaration and a one-shot execution carrier belong to later, separate work packages after the
implementation is frozen and its deterministic gates pass.
