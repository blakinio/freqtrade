# TradingView Strategy Research v1

## Purpose

This is a research-only track for independently written adaptations of public TradingView strategy ideas.
It is not part of the frozen Phase 6 LightGBM-versus-XGBoost comparison, cannot change its selection
policy, and cannot promote a strategy or model.

The protected final holdout `20260801-20260930` is forbidden for this track. No final evaluation may
use it before `2026-10-01T00:00:00Z`.

## Source and licensing boundary

TradingView source pages are used to identify public research ideas and document their stated logic.
The repository does not copy or republish Pine source code. Local implementations are independent
adaptations intended for controlled Freqtrade validation.

The v1 catalog is `ai_platform/research/tradingview/catalog-v1.json`.

## Initial candidates

### Donchian breakout

Local class: `TVDonchianBreakoutStrategy`

Research adaptation:

- breakouts use the completed previous Donchian window, avoiding self-inclusion of the breakout candle;
- a 100-period EMA acts as a direction filter;
- a shorter Donchian window provides exit signals;
- long and short research signals are enabled for futures testing.

Public inspiration:
`https://www.tradingview.com/script/hyYvFjux-Donchian-Breakout-Strategy/`

### Supertrend reversal

Local class: `TVSupertrendStrategy`

Research adaptation:

- ATR-based Supertrend state;
- entry when the completed candle changes trend direction;
- opposite direction change exits the current side and can create the opposite-side signal;
- fixed hard stoploss remains independent of the trend signal.

Public inspiration:
`https://www.tradingview.com/script/VLRj2sG9-SuperTrend-STRATEGY/`

### Bollinger mean reversion

Local class: `TVBollingerMeanReversionStrategy`

Research adaptation:

- 20-period mean and two-standard-deviation bands;
- close below the lower band creates a long candidate;
- close above the upper band creates a short candidate;
- the middle band is the signal exit target;
- a fixed hard stoploss is used instead of copying source-specific dynamic risk logic.

Public inspiration:
`https://www.tradingview.com/script/GDrB3tu3-Bollinger-Bands-Simple-Strategy/`

### Wick Hunter Multi-VWAP liquidation gate

Local helper: `add_wickhunter_vwap_gates`

Research adaptation:

- rolling typical-price VWAP;
- configurable percentage distance below VWAP for a long gate;
- configurable percentage distance above VWAP for a short gate.

This is **not** a complete strategy. A valid entry additionally requires a time-aligned historical
liquidation event. The track must not substitute candle volume, wick size, or inferred liquidation
values for real liquidation observations.

The separate liquidation foundation now provides:

- canonical liquidation event records under `ai_platform/research/liquidations/`;
- a public Bybit linear collector at `ai_platform/scripts/liquidation_collector.py`;
- completed-candle-only alignment and counter-trade policy tests;
- a disabled example profile;
- the staged deployment process in `docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md`.

These components remove the missing contract/collector blocker, but they do not create a tradable candidate.
Historical replay remains blocked until an immutable integrity-checked event dataset and a prospectively
declared replay contract are available.

Public inspiration:
`https://www.tradingview.com/script/9bDNkZXk-Multi-VWAP-for-Wick-Hunter/`

## Validation protocol

Candidates must be compared using the same declared:

- historical/OOS timerange;
- pair universe;
- timeframe;
- exchange market type;
- fee assumption;
- startup/warm-up treatment;
- execution semantics.

A profitable backtest is not sufficient. Any candidate considered beyond exploration must also pass
out-of-sample evaluation, walk-forward evaluation, lookahead analysis, recursive analysis, drawdown
review, and minimum trade-count checks according to the platform lifecycle.

Do not tune a candidate on the same OOS window used to report its performance.

## Loading the strategies

The strategy classes live under `ai_platform/strategies/` and can be discovered with an explicit
strategy path:

```bash
freqtrade list-strategies --strategy-path ai_platform/strategies -1
```

Example research backtest shape:

```bash
freqtrade backtesting \
  --strategy TVDonchianBreakoutStrategy \
  --strategy-path ai_platform/strategies \
  -c <research-futures-dry-run-config.json> \
  --timerange <declared-historical-oos-range> \
  --fee <declared-fee>
```

Use the same command shape for `TVSupertrendStrategy` and `TVBollingerMeanReversionStrategy`.
The concrete config, pair universe, timerange, fee and data provenance must be pinned before any
results are compared.

## Current status

- Donchian breakout: ready for controlled historical OOS backtest.
- Supertrend reversal: ready for controlled historical OOS backtest.
- Bollinger mean reversion: ready for controlled historical OOS backtest.
- Wick Hunter liquidation/VWAP: data collection foundation available; strategy replay remains blocked on
  an immutable integrity-checked liquidation dataset and a prospectively declared replay contract.

No profitability conclusion is made by this foundation work package.
