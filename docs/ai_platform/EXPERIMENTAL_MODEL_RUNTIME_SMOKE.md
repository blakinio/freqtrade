# Experimental Model Heavy Runtime Smoke v1

## Purpose

This bounded research task validates that the canonical experimental PyTorch and reinforcement-learning model paths can execute with the repository's real heavy runtime dependencies.

It is integration evidence only. It does not download market data, train on historical market data, run a Freqtrade backtest, score historical OOS, access the protected final holdout, compare profitability, or promote any model.

## Scope

The smoke entry point is:

```bash
python -m ai_platform.scripts.experimental_model_runtime_smoke
```

The dedicated GitHub Actions workflow installs both `freqai` and `freqai_rl` optional dependency profiles, then runs the smoke on Python 3.12.

### PyTorch path

The smoke uses the canonical `SeededPyTorchMLPRegressor` class and its real `fit()` path with:

- 32 deterministic synthetic feature rows;
- one synthetic regression target;
- one training epoch;
- CPU execution;
- the repository's real `PyTorchMLPModel`, `PyTorchModelTrainer`, optimizer, loss, and data converter.

The output is checked only for a valid finite prediction tensor with the expected shape. No loss value or trading-performance conclusion is recorded.

### Reinforcement-learning path

The smoke uses the canonical `LongOnlyReinforcementLearner` and `LongOnlyEnvironment` with:

- deterministic synthetic features and synthetic OHLC prices;
- exactly three long-only actions;
- Stable-Baselines3 PPO;
- one train cycle;
- a tiny `n_steps=8`, `batch_size=4` configuration;
- no randomized starting position;
- no historical or future-derived inputs.

The learner executes its real inherited `fit()` path against the custom environment. The only success criterion is that PPO training completes and returns a PPO model instance.

## Safety boundaries

The smoke result always declares:

- `data_source = synthetic_only`;
- `historical_oos_scored = false`;
- `protected_final_holdout_used = false`;
- `performance_conclusion_allowed = false`.

The protected final holdout remains `20260801-20260930`. This workflow is not authorized to read or score it.

The smoke remains outside Phase 6 and cannot affect the LightGBM-versus-XGBoost candidate set, selection policy, frozen thresholds, promotion state, or profitability claims.
