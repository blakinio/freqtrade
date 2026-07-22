# TradingView Futures Historical Benchmark v1

## Purpose

This work package defines a one-shot, evidence-only historical benchmark for the three candle-only TradingView research strategies whose common Kraken Futures data path was proven by the preceding preflight.

The benchmark covers exactly:

- `TVDonchianBreakoutStrategy`;
- `TVSupertrendStrategy`;
- `TVBollingerMeanReversionStrategy`.

Wick Hunter Multi-VWAP remains excluded because the helper is only a price-distance gate and no trustworthy, deterministically aligned historical liquidation feed is bound to the research track.

## Frozen execution geometry

The machine-readable contract is `ai_platform/research/tradingview/futures-historical-benchmark-v1.json`.

All three candidates use the same:

```text
exchange: krakenfutures
trading mode: futures
margin mode: isolated
stake/settlement currency: USD
pairs: BTC/USD:USD, ETH/USD:USD
timeframe: 15m
execution timerange: 20260301-20260701
semantic research window: 20260301-20260630
download timerange: 20260201-20260701
fee: 0.002
max_open_trades: 2
stake_amount: 100 USD
dry_run_wallet: 10000 USD
dry_run: true
```

The runtime market identities must still resolve to:

- `BTC/USD:USD` / `PF_XBTUSD`;
- `ETH/USD:USD` / `PF_ETHUSD`.

Runtime discovery is revalidated immediately before execution. Missing, ambiguous, renamed, or otherwise drifted markets fail closed.

## Frozen source identity

The contract binds the benchmark to the declared Git blob identities of:

- `ai_platform/strategies/TradingViewResearchStrategies.py`;
- `ai_platform/research/tradingview/signals.py`.

The validator recalculates each Git blob identity before contract acceptance. Strategy or signal changes therefore require a new prospectively declared benchmark contract before any new result-producing run.

## One-shot execution request

The workflow is `.github/workflows/ai-platform-tradingview-futures-historical-benchmark.yml`.

The implementation PR runs only the static contract job because no run-request exists yet.

A later result-producing PR may add exactly one file:

`ai_platform/research/tradingview/run-requests/futures-historical-benchmark-v1.json`

That file must equal the canonical request emitted by:

```bash
python -m ai_platform.scripts.tradingview_futures_historical_benchmark print-canonical-request
```

The execution job is authorized only on the initial `opened` event for that scope-limited request PR. Synchronizing or reopening the request PR does not create another benchmark execution.

## Benchmark evidence

For every candidate the workflow preserves:

- exact execution commit;
- frozen contract and run-request;
- runtime market discovery and materialized config;
- data-coverage evidence;
- exact backtest command;
- backtest log and Freqtrade result archive;
- deterministic common backtest summary;
- pair-level profit/trade breakdown;
- exit-reason breakdown;
- long/short breakdown;
- lookahead-analysis CSV and log when produced;
- recursive-analysis log;
- machine-readable analysis status.

The final `benchmark-summary.json` may contain a deterministic historical ordering using:

1. total relative profit descending;
2. maximum drawdown ascending;
3. trade count descending;
4. strategy name ascending.

This ordering is research evidence only. The summary fixes `selected_candidate = null`, does not authorize an automatic validation claim, and cannot promote a strategy.

## Validation-analysis semantics

### Lookahead analysis

Lookahead analysis runs with the same strategy, config, data, timerange and fee. The workflow requests at least one trade and targets twenty checked trades so low-activity candidates still produce explicit evidence where possible.

A successful command plus a matching CSV row with `has_bias = No` is recorded as a lookahead pass. Bias or incomplete output is preserved explicitly and cannot be converted into an automatic validation claim.

### Recursive analysis

Recursive analysis runs on the frozen BTC perpetual using startup-candle probes:

```text
49, 99, 119, 199, 499, 999
```

A successful command is recorded as `completed_review_required`. The workflow deliberately does not reinterpret the recursive-analysis table as an automatic pass because acceptable variance depends on the affected indicator and whether it can alter trading decisions.

## Historical evidence boundary

The previously consumed platform OOS interval `20260501-20260630` is historical research evidence. Benchmark results cannot be described as unseen final evidence and cannot be used to retune these v1 strategies against the same reported window.

The protected prospective final holdout remains:

```text
20260801-20260930
```

It is forbidden to this work package, and no final evaluation is authorized before `2026-10-01T00:00:00Z`.

Nothing in this benchmark changes frozen Phase 5 thresholds, reopens Phase 6, changes authoritative `selected_model = null`, promotes PyTorch/RL evidence, enables live trading, or makes a profitability or superiority claim.
