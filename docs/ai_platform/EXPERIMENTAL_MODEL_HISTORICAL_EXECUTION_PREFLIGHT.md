# Experimental Model Historical Execution Preflight v1

This bounded task verifies prerequisites for a future real historical PyTorch or RL research execution. It does not run either canonical backtest, does not extract historical-OOS metrics, does not access the protected final holdout, and cannot promote a model or make a profitability claim.

## Verified contract

The canonical tracks remain:

- `pytorch-research-v1` / `SeededPyTorchMLPRegressor` / `AiFrozenCandidateStrategy`;
- `rl-research-v1` / `LongOnlyReinforcementLearner` / `AiLongOnlyRLResearchStrategy`.

Both use:

- exchange: Kraken;
- pairs: `BTC/USDT`, `ETH/USDT`;
- timeframes: `15m`, `1h`, `4h`;
- download range: `20250801-20260630`;
- prediction range: `20260301-20260630`;
- consumed historical-OOS scoring window: `20260501-20260630`;
- one frozen 90-day training window with a 122-day prediction period;
- `dry_run: true` and fee `0.002`.

The protected final holdout remains `20260801-20260930` and is excluded from every preflight command.

## Runtime preflight

The dedicated workflow `.github/workflows/experimental-model-historical-execution-preflight.yml` runs on Ubuntu 24.04 with Python 3.12 and installs both optional dependency profiles required by the inherited experimental model paths:

```text
freqtrade[freqai,freqai_rl]
```

Before market-data access it validates the active task checkpoint and the static research foundation. It then verifies that Freqtrade resolves both custom FreqAI models and both custom strategies without executing a backtest.

## Historical market-data availability

The PyTorch and RL manifests require the same Kraken dataset, so the preflight downloads the dataset only once. A dedicated cache is restored first. On cache miss the workflow downloads Kraken trades for the exact declared range and converts them to the required `15m`, `1h`, and `4h` OHLCV data.

After download, the preflight loads every pair/timeframe combination through Freqtrade's own historical-data loader and fails closed unless the stored data covers the full declared download boundary. A successful run therefore proves data availability for the declared historical geometry in that GitHub Actions runtime.

The cache is dedicated to the experimental research tracks and is not evidence of model performance. Its contents end at the declared June 2026 boundary and never include the protected August-September 2026 final holdout.

## Command-path verification

`ai_platform/scripts/experimental_model_historical_execution_preflight.py` validates the canonical manifests/configs and materializes, but does not execute, the exact command paths used by `ai_platform.scripts.run_experiment`:

- one shared `download-data` path for the Kraken historical dataset;
- one PyTorch `backtesting` command path;
- one RL `backtesting` command path.

The future execution task must still use the canonical manifests and the existing strict extractor `ai_platform.scripts.experimental_model_oos_result_extractor` for fully contained `20260501-20260630` trades. Generic March-June run-summary metrics remain insufficient evidence.

## Safety boundary

This preflight is authorized to download historical data ending `20260630` only. It is not authorized to:

- run a canonical PyTorch or RL Freqtrade backtest;
- score historical OOS;
- retune the frozen thresholds `0.006/-0.009`;
- change Phase 6 candidates, policy, or results;
- access `20260801-20260930`;
- promote a model, trade live, or make profitability/superiority claims.
