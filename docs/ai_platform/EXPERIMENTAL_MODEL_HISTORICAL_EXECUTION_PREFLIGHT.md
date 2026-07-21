# Experimental Model Historical Execution Preflight v2

This bounded task verifies prerequisites for a future real historical PyTorch or RL research execution. It does not run either canonical backtest, does not extract historical-OOS metrics, does not access the protected final holdout, and cannot promote a model or make a profitability claim.

## Semantic windows versus Freqtrade execution timeranges

The research contract uses human-readable semantic window labels whose end date is inclusive:

- prediction window: `20260301-20260630`;
- consumed historical-OOS scoring window: `20260501-20260630`;
- download window label: `20250801-20260630`.

Freqtrade's `YYYYMMDD-YYYYMMDD` timerange parser converts the stop token to midnight at the start of that date. The stop is therefore an exclusive execution boundary. To include all candles and trades from June 30, the canonical experimental execution manifests use:

- Freqtrade prediction timerange: `20260301-20260701`;
- Freqtrade download timerange: `20250801-20260701`.

This is an encoding correction, not an expansion of the semantic research window. The strict OOS extractor still scores only fully contained trades with `open_date >= 2026-05-01T00:00:00Z` and `close_date < 2026-07-01T00:00:00Z`. The protected final holdout remains `20260801-20260930` and is not accessed.

The 122-day prediction period is consistent with the corrected execution boundary: March 1 through June 30 inclusive is exactly 122 days.

## Verified contract

The canonical tracks remain:

- `pytorch-research-v1` / `SeededPyTorchMLPRegressor` / `AiFrozenCandidateStrategy`;
- `rl-research-v1` / `LongOnlyReinforcementLearner` / `AiLongOnlyRLResearchStrategy`.

Both use:

- exchange: Kraken;
- pairs: `BTC/USDT`, `ETH/USDT`;
- timeframes: `15m`, `1h`, `4h`;
- fee: `0.002`;
- one frozen 90-day training window;
- a 122-day prediction period;
- `dry_run: true`.

The research foundation preserves the semantic labels and separately pins `freqtrade_prediction_timerange` and `freqtrade_download_timerange` so future command generation cannot silently lose June 30 again.

## Runtime and resolver preflight

The dedicated workflow `.github/workflows/experimental-model-historical-execution-preflight.yml` runs on Ubuntu 24.04 with Python 3.12 and installs the dependency-closed profile:

```text
freqtrade[freqai,freqai_rl]
```

Before market-data access it validates the active task checkpoint, the research foundation, both canonical manifests, and the exclusive-stop relationship between semantic and executable timeranges. It then verifies that Freqtrade resolves both custom FreqAI models and both custom strategies without executing a backtest.

## Historical Kraken market-data availability

Kraken does not expose deep historical OHLCV through the normal Freqtrade OHLCV path, so Freqtrade must acquire historical trades and convert them to candles. Freqtrade processes trade-history pairs sequentially inside one downloader process. To keep this prerequisite bounded, the preflight uses two independent matrix jobs:

- one for `BTC/USDT`;
- one for `ETH/USDT`.

Each job downloads only its pair over the exact Freqtrade range `20250801-20260701`, converts to `15m`, `1h`, and `4h`, and verifies the stored data through Freqtrade's own historical-data loader. Verification fails closed unless the first candle reaches the required start and the final candle for each timeframe reaches the last expected interval before the exclusive `2026-07-01T00:00:00Z` stop.

A pair-specific cache is saved only after successful coverage validation. Partial or timed-out downloads are not cached as valid evidence.

## Command-path verification

`ai_platform/scripts/experimental_model_historical_execution_preflight.py` validates the canonical manifests/configs and materializes, but does not execute, the exact command paths used by `ai_platform.scripts.run_experiment`:

- the corrected shared `download-data` timerange;
- the corrected PyTorch `backtesting` timerange;
- the corrected RL `backtesting` timerange.

The script also proves that the Freqtrade prediction range spans 122 days and that both executable stop tokens are exactly one day after the inclusive semantic end date.

## Strict OOS boundary

The future execution task must use the canonical manifests and the existing strict extractor `ai_platform.scripts.experimental_model_oos_result_extractor`. Generic full-window run summaries remain insufficient evidence.

Regression coverage explicitly includes a trade opened and closed on June 30, which must be eligible for strict OOS scoring, while a trade closing exactly at `2026-07-01T00:00:00Z` remains excluded.

## Safety boundary

This preflight is authorized to acquire and verify historical data only through the exclusive `20260701` stop, which represents the end of June 30 coverage. It is not authorized to:

- run a canonical PyTorch or RL Freqtrade backtest;
- score historical OOS;
- retune the frozen thresholds `0.006/-0.009`;
- change Phase 6 candidates, policy, or results;
- access `20260801-20260930`;
- promote a model, trade live, or make profitability/superiority claims.
