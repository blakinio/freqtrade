# Experimental Model Research Foundation v1

This work package creates two research-only tracks outside the Phase 6 LightGBM-versus-XGBoost comparison:

- **PyTorch Research** — a small seeded MLP regression baseline;
- **Reinforcement Learning Research** — a long-only PPO proof of integration.

The foundation does not execute training or backtesting, does not change the Phase 6 comparison contract or selection policy, does not retune the frozen Phase 5.2 candidate, and does not access the protected final holdout.

## Isolation contract

The canonical foundation is `ai_platform/experimental_model_research/foundation-v1.json`.

Both tracks are explicitly outside Phase 6. Their results cannot be consumed by the current LightGBM-versus-XGBoost decision, cannot change its candidates or predeclared selection policy, and cannot authorize promotion or a profitability claim.

The frozen candidate reference remains:

- `entry_prediction_threshold = 0.006`;
- `exit_prediction_threshold = -0.009`.

The prospective protected final holdout remains `20260801-20260930`. It is forbidden for both tracks. The generic manifest loader enforces this boundary before execution.

## Shared temporal geometry

The tracks deliberately reuse the already-consumed historical research geometry without joining Phase 6:

- training window: `20251201-20260228`;
- tuning/prediction-only coverage: `20260301-20260430`;
- consumed historical OOS scoring window: `20260501-20260630`;
- combined prediction window: `20260301-20260630`;
- download coverage: `20250801-20260630`;
- `train_period_days = 90`;
- `backtest_period_days = 122`.

The 122-day backtest period is intentional: it keeps one frozen training window before March-June prediction coverage and prevents periodic FreqAI retraining from learning from May-June historical OOS while that same window is later scored.

Any future result used as research evidence must score only fully contained trades from `20260501-20260630` and report the same trading-level metric families used by the existing research pipeline: profit, drawdown, trade count, and stability. Training loss and the generic March-June `run-summary.json` metrics are not accepted as OOS selection evidence.

## PyTorch Research

Current FreqAI includes the `BasePyTorchModel` extension hierarchy and a built-in `PyTorchMLPRegressor`. Custom FreqAI model resolution supports `freqaimodel_path`, so the project model remains under `ai_platform/freqaimodels/` without changing upstream core.

Track identity:

- experiment: `pytorch-research-v1`;
- model: `SeededPyTorchMLPRegressor`;
- FreqAI identifier: `ai-platform-pytorch-research-v1`;
- config: `ai_platform/configs/freqai-pytorch-research.example.json`;
- manifest: `ai_platform/experiments/pytorch-research-v1.json`;
- artifact root: `ai_platform/artifacts/experimental-model-research/pytorch`.

The baseline is intentionally small: one hidden layer, 64 hidden units, no dropout, three epochs, and seed 42. The custom wrapper seeds Python, NumPy, PyTorch, and CUDA where available before model construction and data-loader creation. CUDA/cuDNN deterministic settings are requested where supported. This improves reproducibility but is not a guarantee of bit-for-bit identity across different PyTorch versions, hardware, drivers, or devices.

The trading strategy is `AiFrozenCandidateStrategy`, which keeps the Phase 5.2 entry and exit thresholds as constants rather than tunable parameters. Real evaluation, when authorized in a later bounded task, must use trading metrics on strict historical OOS rather than training loss.

**Track status: `feasible` for a reproducible research pipeline foundation.** No model-performance or profitability conclusion has been produced.

## Reinforcement Learning Research

Current FreqAI RL support uses Gymnasium environments and Stable-Baselines3/sb3-contrib models. The optional `freqai_rl` dependency profile supplies Gymnasium, Stable-Baselines3, sb3-contrib, Torch, and tqdm. The built-in framework supports custom model classes and custom environments without modifying Freqtrade core.

Track identity:

- experiment: `rl-research-v1`;
- model: `LongOnlyReinforcementLearner`;
- backend/algorithm: Stable-Baselines3 PPO;
- FreqAI identifier: `ai-platform-rl-research-v1`;
- config: `ai_platform/configs/freqai-rl-research.example.json`;
- manifest: `ai_platform/experiments/rl-research-v1.json`;
- artifact root: `ai_platform/artifacts/experimental-model-research/rl`.

### Observation contract

The agent observes the normalized FreqAI feature window available at the current environment step. Raw OHLC columns are supplied separately because the RL environment needs prices, then removed from the agent feature matrix. Backtesting sets `add_state_info = false` because FreqAI does not support live trade-state injection in backtesting.

### Action contract

The custom research environment is long-only and exposes exactly three discrete actions:

- `0`: neutral;
- `1`: long entry;
- `2`: long exit.

Short entry and short exit actions are absent. This aligns the RL feasibility track with the platform's spot, `can_short = false` research boundary.

### Reward contract

The reward uses only state available at the current environment step:

- invalid action: `-1.0`;
- valid long entry: `0.0`;
- valid long exit: current unrealized trade profit ratio multiplied by 100;
- neutral while long: a small bounded penalty derived from current trade duration.

The reward does not read future candles, future returns, forward-shifted targets, or protected-holdout information.

### Episode and leakage boundaries

Training and the internal non-shuffled evaluation split remain inside the declared pre-OOS training window. Continual learning and randomized episode starts are disabled. The May-June consumed historical OOS window is reserved for a later frozen-model trading backtest; it is not part of reward design, agent search, or hyperparameter tuning.

The FreqAI RL training environment is intentionally simpler than the full Freqtrade trading engine. Therefore environment reward or internal evaluation is integration evidence only. Final research evidence must come from the separate Freqtrade backtesting path over the declared strict OOS boundary and must use trading metrics.

**Track status: `feasible` for proof of integration.** Broad agent search, reward-function search, and hyperparameter sweeps are not justified yet. No model-performance or profitability conclusion has been produced.

## Dependencies and validation

PyTorch and RL runtime smoke checks require the repository's `freqai_rl` optional dependency profile because that is where the current repository declares Torch. Lightweight contract validation does not import Torch, Gymnasium, pandas, TA-Lib, or Stable-Baselines3 and can run in AI Platform CI:

```bash
python -m ai_platform.scripts.experimental_model_research_contract
```

The validator checks:

- distinct manifests, configs, FreqAI identifiers, and artifact roots;
- `dry_run: true` and empty exchange credentials;
- central protected-final-holdout isolation;
- exact train/tune/OOS geometry and single-training policy;
- frozen PyTorch strategy thresholds;
- explicit seeds;
- long-only RL actions;
- no future-information reward declaration;
- no Phase 6 membership, promotion, or profitability claim.

No expensive training is required to validate this foundation. A later execution task must first provide strict May-June OOS result extraction for these experimental manifests; generic full-window run summaries are insufficient evidence.
