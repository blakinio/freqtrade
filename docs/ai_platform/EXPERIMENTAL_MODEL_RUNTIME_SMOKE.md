# Experimental Model Heavy Runtime Smoke v1

## Purpose

This bounded research task validates that the canonical experimental PyTorch and reinforcement-learning model paths can execute with the repository's real heavy runtime dependencies and tracked research configs.

It is integration evidence only. It does not download market data, train on historical market data, run a Freqtrade backtest, score historical OOS, access the protected final holdout, compare profitability, retune models, or promote any model.

## Scope

The smoke entry point is:

```bash
python -m ai_platform.scripts.experimental_model_runtime_smoke
```

The dedicated GitHub Actions workflow installs the dependency-closed `freqai` plus `freqai_rl` runtime on Python 3.12 and runs one combined bounded smoke.

All synthetic timestamps are constrained to the declared pre-OOS training window `20251201-20260228`. The smoke fails if synthetic data reaches the historical OOS boundary or the protected final holdout.

### PyTorch path

The smoke loads `ai_platform/configs/freqai-pytorch-research.example.json` and constructs the canonical `SeededPyTorchMLPRegressor` through its normal config-based constructor.

It then:

- creates deterministic synthetic train and test features and labels;
- verifies the canonical research seed remains `42`;
- executes the real inherited PyTorch `fit()` path twice on identical inputs in the same CPU runtime;
- requires both fitted model state dictionaries to contain finite tensors;
- requires exact tensor equality across both same-runtime seeded fits.

This establishes a bounded same-runtime reproducibility property for the seeded research baseline. It does not claim bit-for-bit reproducibility across different hardware, drivers, operating systems, or PyTorch versions, and it does not measure trading quality.

### Reinforcement-learning path

The smoke loads `ai_platform/configs/freqai-rl-research.example.json` and constructs the canonical `LongOnlyReinforcementLearner` through its normal config-based constructor.

It then:

- verifies Stable-Baselines3 PPO resolves as the canonical backend;
- obtains the environment contract through `pack_env_dict()` and verifies seed `42` and fee `0.002`;
- constructs the canonical `MyRLEnv` on deterministic synthetic features and OHLC prices;
- verifies the long-only `Discrete(3)` action contract and expected observation shape;
- exercises `long_enter`, `neutral`, and `long_exit` actions;
- creates the training and evaluation environments through `set_train_and_eval_environments()`;
- executes the inherited PPO `fit()` path and requires bounded training to complete.

The environment and PPO run use synthetic pre-OOS training-window data only. Completion is integration evidence, not evidence of profitability or superiority.

## Safety boundaries

The smoke result explicitly declares:

- `data_scope = synthetic_pre_oos_training_window_only`;
- `historical_oos_scored = false`;
- `final_holdout_used = false`;
- `phase6_member = false`;
- `retuning_performed = false`;
- `promotion_allowed = false`;
- `profitability_claim_allowed = false`.

The protected final holdout remains `20260801-20260930`. This workflow is not authorized to read or score it.

The smoke remains outside Phase 6 and cannot affect the LightGBM-versus-XGBoost candidate set, selection policy, frozen thresholds, promotion state, or profitability claims.
