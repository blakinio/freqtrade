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
- combined prediction window label: `20260301-20260630`;
- download coverage label: `20250801-20260630`;
- `train_period_days = 90`;
- `backtest_period_days = 122`.

The semantic labels above use an inclusive end date. Freqtrade parses the stop token in `YYYYMMDD-YYYYMMDD` at midnight on that date, so its executable stop boundary is exclusive. The foundation therefore pins separate execution encodings:

- `freqtrade_prediction_timerange = 20260301-20260701`;
- `freqtrade_download_timerange = 20250801-20260701`.

These exclusive July 1 stop tokens include all of June 30 without expanding the semantic research window. The 122-day backtest period is consistent with March 1 through June 30 inclusive and keeps one frozen training window before March-June prediction coverage. It prevents periodic FreqAI retraining from learning from May-June historical OOS while that same window is later scored.

Any future result used as research evidence must score only fully contained trades from `20260501-20260630` and report the same trading-level metric families used by the existing research pipeline: profit, drawdown, trade count, and stability. The strict scoring boundary remains `open_date >= 2026-05-01T00:00:00Z` and `close_date < 2026-07-01T00:00:00Z`. Training loss and the generic March-June `run-summary.json` metrics are not accepted as OOS selection evidence.

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

Current FreqAI RL support uses Gymnasium environments and Stable-Baselines3/sb3-contrib models. The `freqai_rl` extra supplies Gymnasium, Stable-Baselines3, sb3-contrib, Torch, and tqdm, while the canonical custom classes also inherit through the regular FreqAI stack. Therefore the dependency-closed heavy runtime profile for both research tracks is `freqtrade[freqai,freqai_rl]`.

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

The dependency-closed heavy runtime profile for both canonical research model classes is `freqtrade[freqai,freqai_rl]`. The `freqai_rl` extra supplies Torch, Gymnasium, and Stable-Baselines3, while the inherited FreqAI model stack also requires dependencies from the regular `freqai` extra. Lightweight contract validation does not import Torch, Gymnasium, pandas, TA-Lib, or Stable-Baselines3 and can run in AI Platform CI:

```bash
python -m ai_platform.scripts.experimental_model_research_contract
```

The validator and lightweight tests check:

- distinct manifests, configs, FreqAI identifiers, and artifact roots;
- the dependency-closed heavy runtime profile;
- `dry_run: true` and empty exchange credentials;
- central protected-final-holdout isolation;
- exact train/tune/OOS semantic geometry and single-training policy;
- separate Freqtrade execution timeranges with an exclusive July 1 stop;
- frozen PyTorch strategy thresholds;
- explicit seeds;
- long-only RL actions;
- no future-information reward declaration;
- no Phase 6 membership, promotion, or profitability claim.

The heavy-runtime integration proof is documented separately in `docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md`. It validates the canonical PyTorch and RL runtime paths on synthetic-only data and is not trading-quality evidence. The boundary-safe historical prerequisite is documented in `docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md`. A later execution task must provide strict May-June OOS result extraction for real experimental backtest artifacts; generic full-window run summaries are insufficient evidence.

## Strict historical-OOS extraction

The research-only extractor is `ai_platform/scripts/experimental_model_oos_result_extractor.py`. Its immutable semantics are declared in `ai_platform/experimental_model_research/oos-extraction-contract-v1.json`, and its output is validated by `ai_platform/experimental_model_research/oos-extraction-schema-v1.json`.

The extractor consumes an already-produced Freqtrade backtest ZIP plus one canonical research manifest. It does not download data, train a model, execute a backtest, retune thresholds, or access the protected final holdout.

Before scoring, it:

- validates the full experimental-model research foundation;
- accepts only `pytorch-research-v1` or `rl-research-v1` with exact canonical manifest content;
- verifies the strategy, model class, FreqAI identifier, and executable prediction timerange embedded in the backtest stats;
- records SHA-256 provenance for the archive, manifest, and config;
- requires exactly one matching strategy result in the archive.

The scoring boundary is `fully_contained_closed_trades`: `open_date >= 2026-05-01T00:00:00Z` and `close_date < 2026-07-01T00:00:00Z`. Trades crossing into the window from April or closing on/after July 1 are excluded and counted. A trade opened and closed on June 30 is eligible; a trade closing exactly at July 1 is not. A `force_exit` is included only when the trade is fully contained inside the scoring window.

The output reports profit, drawdown, included trade count, and two-fold May/June stability using included trades only. Every extraction remains explicitly outside Phase 6, cannot be consumed by its current comparison or selection policy, and cannot authorize promotion or a profitability claim.

Example extraction after a safe backtest artifact exists:

```bash
python -m ai_platform.scripts.experimental_model_oos_result_extractor \
  path/to/backtest-result.zip \
  ai_platform/experiments/pytorch-research-v1.json \
  --output path/to/pytorch-strict-oos.json
```

Producing a valid extraction is evidence plumbing only. It is not evidence that PyTorch or RL is superior or profitable.
