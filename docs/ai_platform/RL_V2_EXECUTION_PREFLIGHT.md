# RL-v2 Execution Preflight

## Status

`rl-v2-execution-preflight-v1` is a bounded, non-result-producing preflight for the frozen RL-v2 desired-position runtime integration.

It exists only to prove that the merged model and strategy still resolve under the current repository runtime, that the construction-only configuration surface is explicit and fail-closed, and that the frozen desired-position and observability contracts remain intact.

## Parent runtime

The preflight is bound to the runtime integration merged by PR #151 as `251fa56aeaaa8fb95c7cdf73015da0c1142dc978`:

- model: `DesiredPositionReinforcementLearner`;
- strategy: `AiDesiredPositionRLResearchStrategy`;
- backend: Stable-Baselines3 through FreqAI;
- algorithm: PPO;
- policy: `MlpPolicy`;
- trading semantics: long-only spot;
- actions: `0=target_flat`, `1=target_long`.

Transition, reward, action labels, and observability remain delegated to `ai_platform.scripts.rl_v2_synthetic_reference`.

## What the preflight does

The dedicated preflight script:

1. validates the machine-readable descriptor;
2. creates an ephemeral in-memory construction-only configuration inside a temporary directory;
3. rejects any historical or future execution geometry;
4. resolves `DesiredPositionReinforcementLearner` through `FreqaiModelResolver`;
5. resolves `AiDesiredPositionRLResearchStrategy` through `StrategyResolver`;
6. constructs the frozen two-action environment from synthetic in-memory frames only;
7. verifies PPO, `MlpPolicy`, long-only semantics, both desired-position actions, canonical transitions, strategy entry/exit mapping, and zero-preserving observability buckets.

The script does not call model fitting, `.learn()`, backtesting, data download, exchange data, or performance scoring.

## Ephemeral configuration contract

The preflight requires only the configuration keys needed for current-runtime construction and resolution. The configuration is created at runtime and is never committed as a training configuration.

Required top-level surfaces include:

- `dry_run=true`;
- `trading_mode=spot`;
- `timeframe`;
- `stake_amount`;
- `exchange.pair_whitelist`;
- `freqaimodel` and `freqaimodel_path`;
- `strategy` and `strategy_path`;
- temporary `user_data_dir`;
- `freqai` configuration containing feature, split, model-training, and RL construction metadata.

Frozen RL requirements:

- `freqai.rl_config.model_type=PPO`;
- `freqai.rl_config.policy_type=MlpPolicy`;
- `freqai.rl_config.model_reward_parameters` must exist;
- no short semantics.

The preflight fails closed if any of these execution-geometry keys are present:

- `timerange`;
- `freqai.train_period_days`;
- `freqai.backtest_period_days`;
- `freqai.live_retrain_hours`.

## Isolation

This work package does not authorize or perform:

- a committed training config;
- an experiment manifest or run request;
- training or model fitting;
- backtesting or historical execution;
- market-data or exchange-data access;
- historical or future evaluation-window selection;
- strict-OOS execution or scoring;
- use of consumed historical OOS `20260501-20260630`;
- access to protected final holdout `20260801-20260930`;
- Hyperopt or reward/feature/hyperparameter search;
- PyTorch-vs-RL ranking;
- promotion, profitability, superiority, or live-trading claims.

Frozen thresholds `0.006/-0.009` and authoritative Phase 6 `selected_model = null` remain unchanged.

## Validation

The dedicated workflow validates the active task checkpoint, installs the current FreqAI/freqai_rl dependency profile, runs targeted fail-closed tests, and executes only the bounded preflight script.

A successful preflight proves runtime resolvability and contract compatibility only. It is not model-performance evidence and does not authorize a later training or historical-execution step without a new prospectively declared task.
