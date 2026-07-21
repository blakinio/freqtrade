# Experimental Model Historical Execution Preflight v1

This bounded task verifies prerequisites for a future real historical PyTorch or RL research execution. It does not run either canonical backtest, does not extract historical-OOS metrics, does not access the protected final holdout, and cannot promote a model or make a profitability claim.

## Semantic windows versus Freqtrade execution timeranges

The research contract distinguishes the already-declared semantic windows from the technical timeranges passed to Freqtrade.

Semantic windows remain unchanged:

- prediction window: `20260301-20260630`;
- download window: `20250801-20260630`;
- consumed historical-OOS scoring window: `20260501-20260630`.

Freqtrade parses an eight-digit stop date as UTC midnight at the start of that date. Therefore a technical timerange ending `20260630` excludes June 30. To execute the unchanged semantic windows through the end of June 30, the canonical technical timeranges use the next-day exclusive stop:

- prediction/backtest timerange: `20260301-20260701`;
- download timerange: `20250801-20260701`.

This is an execution-boundary correction, not an expansion of the semantic research period. July 1 is the exclusive stop boundary and is not part of the May-June scoring window.

## Verified contract

The canonical tracks remain:

- `pytorch-research-v1` / `SeededPyTorchMLPRegressor` / `AiFrozenCandidateStrategy`;
- `rl-research-v1` / `LongOnlyReinforcementLearner` / `AiLongOnlyRLResearchStrategy`.

Both use Kraken, `BTC/USDT` and `ETH/USDT`, `15m`/`1h`/`4h`, one frozen 90-day training window, a 122-day prediction period, `dry_run: true`, and fee `0.002`.

The protected final holdout remains `20260801-20260930` and is excluded from every preflight command. Frozen thresholds remain `0.006/-0.009`. The experimental tracks remain outside Phase 6.

## Runtime preflight

The dedicated workflow `.github/workflows/experimental-model-historical-execution-preflight.yml` runs on Ubuntu 24.04 with Python 3.12 and installs the dependency-closed runtime:

```text
freqtrade[freqai,freqai_rl]
```

Before market-data access it validates the active task checkpoint, the static research foundation, semantic-versus-technical temporal geometry, canonical manifests/configs, and model/strategy resolution. It does not execute a backtest.

## Historical market-data availability

The PyTorch and RL manifests require the same Kraken dataset, so the boundary-corrected preflight downloads the dataset only once. It uses a dedicated `boundary-v2` cache namespace so no stale data or evidence from superseded PR #66 is accepted.

On cache miss the workflow downloads Kraken trades with technical timerange `20250801-20260701` and converts them to `15m`, `1h`, and `4h` OHLCV. The stop at `20260701T00:00:00Z` is exclusive, so the resulting required coverage includes June 30 and does not include July 1 in the semantic research window.

After download, the preflight loads every pair/timeframe combination through Freqtrade's historical-data loader and fails closed unless the stored data reaches the final required candle before the exclusive July 1 stop.

A successful run proves data availability for the declared historical geometry in that GitHub Actions runtime. It is not evidence of model performance.

## Command-path verification

`ai_platform/scripts/experimental_model_historical_execution_preflight.py` validates the canonical inputs and materializes, but does not execute, the exact command paths used by `ai_platform.scripts.run_experiment`:

- one shared `download-data` path with `20250801-20260701`;
- one PyTorch `backtesting` command path with `20260301-20260701`;
- one RL `backtesting` command path with `20260301-20260701`.

The future execution task must still use the canonical manifests and the strict extractor `ai_platform.scripts.experimental_model_oos_result_extractor`. The extractor continues to score only fully contained trades in semantic window `20260501-20260630`, with `2026-07-01T00:00:00Z` as the exclusive end boundary. Generic full-window run-summary metrics remain insufficient evidence.

## Safety boundary

This preflight is authorized to download historical data only through the corrected exclusive stop required to cover June 30. It is not authorized to:

- run a canonical PyTorch or RL Freqtrade backtest;
- score historical OOS;
- retune the frozen thresholds `0.006/-0.009`;
- change Phase 6 candidates, policy, or results;
- access `20260801-20260930`;
- promote a model, trade live, or make profitability or superiority claims.
