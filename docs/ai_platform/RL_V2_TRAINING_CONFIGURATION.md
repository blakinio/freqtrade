# RL-v2 Training Configuration

## Status

`rl-v2-training-configuration-v1` is a committed, research-only configuration contract for the frozen RL-v2 desired-position runtime.

It is intentionally **non-executing and non-result-producing**. It does not authorize or trigger model training, fitting, backtesting, market-data download, strict-OOS scoring, evaluation-window selection, promotion, or live trading.

Configuration:

`ai_platform/configs/rl_v2_training_research.json`

Machine-readable descriptor:

`ai_platform/experimental_model_research/rl-v2-training-configuration-v1.json`

## Parent bindings

The configuration is bound to the completed RL-v2 chain:

- runtime integration: `rl-v2-runtime-integration-v1`;
- runtime integration merge: `251fa56aeaaa8fb95c7cdf73015da0c1142dc978`;
- execution preflight: `rl-v2-execution-preflight-v1`;
- execution preflight merge: `ae28c4fe9d1e94313e0b232b1bcd99d6f4ba59bc`;
- task declaration merge: `960251d5534e0921e5a71b661bd4664df0deeac3`.

The frozen runtime identity remains:

- model: `DesiredPositionReinforcementLearner`;
- strategy: `AiDesiredPositionRLResearchStrategy`;
- backend: Stable-Baselines3 through FreqAI;
- algorithm: PPO;
- policy: `MlpPolicy`;
- long-only spot semantics;
- actions: `0=target_flat`, `1=target_long`.

## Research-only safety posture

The committed configuration is deliberately constrained:

- `dry_run=true`;
- `trading_mode=spot`;
- `initial_state=stopped`;
- exchange credentials are empty;
- `force_entry_enable=false`;
- no short semantics;
- no live-capital authorization or withdrawal capability.

The configuration is a versioned input contract only. Its presence in the repository is not an execution request.

## Fixed training surface

The configuration records one deterministic, non-tuned compatibility surface for later separately authorized work:

```text
seed = 42
n_steps = 128
batch_size = 64
train_cycles = 1
max_trade_duration_candles = 96
max_training_drawdown_pct = 0.2
cpu_count = 1
net_arch = [64, 64]
training_fee = 0.002
```

These values are not claimed to be optimal and were not selected through Hyperopt, reward search, feature search, or RL-v2 performance evidence.

`model_reward_parameters` is deliberately empty. RL-v2 reward behavior and constants remain owned exclusively by the canonical synthetic reference:

- `ai_platform.scripts.rl_v2_synthetic_reference.reference_reward`;
- `ai_platform.scripts.rl_v2_synthetic_reference.REWARD_REFERENCE`.

The configuration therefore cannot redefine or tune the frozen RL-v2 reward constants.

## Desired-position semantic binding

The policy-facing action space remains exactly:

```text
0 = target_flat
1 = target_long
```

Both actions retain position-independent desired-position meaning. Runtime transition semantics remain delegated to:

`ai_platform.scripts.rl_v2_synthetic_reference.desired_position_transition`

The configuration keeps `add_state_info=false`, so it does not introduce hidden current-position state as a requirement for interpreting policy actions.

No short action, short-entry signal, or short-exit signal is introduced.

## Execution-geometry isolation

The following keys are intentionally absent and forbidden in this work package:

- `timerange`;
- `freqai.train_period_days`;
- `freqai.backtest_period_days`;
- `freqai.live_retrain_hours`.

No run request or experiment-execution manifest is added.

Any future historical or prospective training/execution work must be declared in a new bounded task that separately defines its execution geometry and evidence boundary before any model run occurs.

## Evaluation isolation

The following remain forbidden:

- consumed historical OOS `20260501-20260630`;
- protected final holdout `20260801-20260930`.

Frozen Phase 5 thresholds remain:

```text
entry_prediction_threshold = 0.006
exit_prediction_threshold = -0.009
```

Completed Phase 6 remains authoritative with:

```text
selected_model = null
```

RL-v2 remains outside Phase 6. This configuration does not authorize PyTorch-vs-RL ranking, candidate promotion, profitability claims, or superiority claims.

## Validation

Validation is dependency-light and static. It reads JSON and source files only; it does not import the heavy FreqAI RL runtime or execute a model.

```bash
pytest -q tests/ai_platform/test_rl_v2_training_configuration.py
```

The tests fail closed if the configuration introduces execution geometry, live-capital posture, a different model or strategy, a different PPO/policy binding, reward-constant redefinition, short semantics, or weakened OOS/final-holdout isolation.

A successful validation proves configuration-contract consistency only. It is not training evidence, model-performance evidence, profitability evidence, or authorization for historical execution.
