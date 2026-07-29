# WickHunter production evidence inventory v1

## Decision

Status: **blocked before WH-01 preflight execution**.

The accepted immutable Liquid20 import is present and verified, but no truthful immutable production package can currently bind the required market-context JSONL, historical dynamic-universe JSONL and prospective split geometry for the same decision interval. The merged materialization operator must not be invoked with invented hashes, synthetic rows, current-state backdating or guessed split parameters.

This inventory grants no label, replay, model, strategy, execution or live-capital authority.

## Bound accepted import

The accepted import remains:

```text
runner path:
/var/lib/freqtrade-staging-state/wickhunter-accepted-imports/
  wickhunter-production-live-archive-20260729-v4/accepted

host path:
/volume1/docker/freqtrade/state/wickhunter-accepted-imports/
  wickhunter-production-live-archive-20260729-v4/accepted
```

Frozen identity:

- import run: `first-party-live:liquid20-20260729T000000Z-0:7a1a5fc5c22c4d5d`;
- input SHA-256: `7a1a5fc5c22c4d5df37cb3df09889c156e597a2f0bb08be8fad302efac8a88ea`;
- accepted events SHA-256: `9303161c3559eec7d68fc8e3bb9a46605e8861d73557758808870f6242eeee04`;
- accepted records: `29253`;
- accepted interval: `[1785283200052, 1785328080435)`;
- protected holdout start: `1785542400000`.

This package contains accepted liquidation events. It does not contain the nine required `MarketContextSnapshot` metrics or historical `DynamicUniverseSnapshot` quality decisions.

## Production paths inventoried

### Liquid20 live archive

The production source root is:

```text
/volume1/docker/freqtrade-liquidations/data/live/runs
```

Its closed run artifacts preserve source-separated Binance USD-M and Bybit Linear liquidation events, source summaries and collector state. They do not define immutable completed-candle history, 24-hour quote volume, spread history, VWAP/VWMA, ATR/volatility/wick/trend ratios, market-wide liquidation intensity snapshots, or historical universe-quality decisions.

The live collector's dynamic subscription universe is operational state. It is not an as-of WickHunter universe history and cannot be backdated to the accepted interval.

### Published Liquid20 candle diagnostic

Repository evidence exists for `liquid20-candle-diagnostic-20260724-v1`:

- sources: Binance USD-M and Bybit Linear;
- timeframe: `5m`;
- interval: `2026-07-24T00:00:00Z` through `2026-07-26T00:00:00Z`;
- records: `23040`;
- classification: `diagnostic_only`;
- performance research authorized: `false`;
- durable Synology raw archive proven: `false`.

This package ends about three days before the accepted import begins. It cannot supply completed candles or availability evidence for `2026-07-29`, and its raw bytes are not proven under an immutable production path.

### Binance Spot instrument acceptance

The candidate durable root is:

```text
/var/lib/freqtrade-staging-state/binance-spot-instrument-acceptance
```

The v2 run was cancelled after five observations and has no terminal accepted, rejected or inconclusive result. The non-blocking v3 implementation exists, but its trigger is separately gated. More importantly, this evidence concerns Binance **Spot**, while the accepted Liquid20 events use Binance USD-M futures and Bybit Linear derivatives. It cannot establish the required venue and market identities for the accepted import.

### Current catalog and runtime state

Current Market Data Fabric catalogs and live runtime snapshots may be useful for a future prospective interval. They cannot be silently treated as historical as-of evidence for the accepted interval. No reviewed production path was found that binds, for every intended decision timestamp:

- canonical Binance USD-M and Bybit Linear instrument identity;
- active state and exact symbol mapping;
- completed-candle availability;
- quote volume and spread;
- candle and feature history depth;
- liquidation source coverage and health;
- symbol risk exclusions;
- exact universe policy and code revision.

## Missing immutable inputs

A valid WH-01 package still requires all of the following:

1. Source-separated completed-candle and market-quality evidence covering the decision interval and every required lookback.
2. Exact availability timestamps and source identities for all nine market-context metrics.
3. Immutable as-of Binance USD-M and Bybit Linear instrument snapshots.
4. Immutable universe-quality inputs and resulting `wickhunter-dynamic-universe-v1` history.
5. A prospectively frozen decision cadence, metric lookbacks, burst window, minimum history, source freshness, partition span, label horizon, purge/embargo gaps and named split windows.
6. Exact SHA-256 identities for the generated market-context and universe-history JSONL files.

The `quote_volume_24h_usd` metric alone requires evidence preceding the accepted interval. The approximately 12.47-hour accepted import cannot provide its own full 24-hour context.

## WH-01 operator preflight outcome

The merged operator preflight was **not invoked against production paths** because no valid materialization request can yet be frozen. The request schema requires exact input SHA-256 values and a declared split geometry; inserting placeholder hashes or guessed geometry would create false authority rather than a bounded missing-input report.

The current truthful outcome is therefore:

```text
accepted import: ready
market context: missing
universe history: missing
split geometry: missing
WH-01 materialization: blocked
WH-02: blocked
```

## Required next package

A separate reviewed no-network evidence-capture package must prospectively freeze one source-separated Binance USD-M and Bybit Linear candle/market-quality interval, including sufficient pre-roll for every metric lookback, and must preserve exact raw hashes and availability semantics. A later package may then derive immutable market-context and universe-history rows, freeze split geometry and run the unchanged WH-01 operator preflight.

No current catalog backfill, synthetic fixture, cross-market substitution, live endpoint call inside materialization, replay, label generation or model execution is permitted.
