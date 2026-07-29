# WickHunter real dataset materialization preflight

## Decision

Status: **blocked before implementation**.

The first accepted immutable production Liquid20 import now exists, but it is not yet a WickHunter feature dataset. WH-01 requires accepted liquidation events plus real decision-time market context, real dynamic-universe history and a prospectively frozen split geometry. The repository currently proves those joins only with synthetic fixtures.

This preflight authorizes no replay, labels, model fitting, scoring, optimization, strategy-quality claim, profitability claim, order path or live capital.

## Bound accepted import

The only input selected by this preflight is the immutable accepted package under the approved Synology state mapping:

```text
/var/lib/freqtrade-staging-state/wickhunter-accepted-imports/
  wickhunter-production-live-archive-20260729-v4/accepted
```

Host identity:

```text
/volume1/docker/freqtrade/state/wickhunter-accepted-imports/
  wickhunter-production-live-archive-20260729-v4/accepted
```

Frozen identities:

- operation: `wickhunter-production-live-archive-20260729-v4`;
- source run: `liquid20-20260729T000000Z-0`;
- import: `first-party-live:liquid20-20260729T000000Z-0:7a1a5fc5c22c4d5d`;
- input identity: `7a1a5fc5c22c4d5df37cb3df09889c156e597a2f0bb08be8fad302efac8a88ea`;
- manifest identity: `a9e53a2d6f4accd14cfd0c668584fc75f0b97ffebd8c9bccc3e0b4b633f98cb8`;
- accepted events SHA-256: `9303161c3559eec7d68fc8e3bb9a46605e8861d73557758808870f6242eeee04`;
- accepted event IDs SHA-256: `7141e77a27d2c352774cd0180656d3391a1197806433656357dafec811783e7f`;
- accepted interval: `[1785283200052, 1785328080435)`;
- protected holdout start: `1785542400000`.

The package contains 29,253 accepted records, zero rejections and zero duplicate records. Passing `load_accepted_import()` proves only accepted-import integrity; it does not materialize WH-01 rows.

## Required WH-01 inputs that are still absent

### Decision-time market context

Every materialized row requires a `MarketContextSnapshot` whose metrics are available no later than the decision timestamp. The required metric set is:

- `quote_volume_24h_usd`;
- `vwap`;
- `vwma`;
- `atr_ratio`;
- `volatility_ratio`;
- `wick_ratio`;
- `trend_return_ratio`;
- `spread_bps`;
- `market_wide_liquidation_intensity`.

A real package must bind each value to an immutable source identity, availability timestamp and code revision. Completed-candle metrics may not become available before the candle close. Current WH-01 tests construct these values as fixtures; they are not production evidence.

### Historical dynamic universe

Every decision timestamp requires the latest eligible `DynamicUniverseSnapshot`. Building it requires immutable as-of evidence for:

- canonical exchange, market type and instrument identity;
- active/inactive state and exact symbol mapping;
- quote volume and spread;
- candle and feature history depth;
- latest candle availability;
- source-labelled liquidation coverage and health;
- symbol risk exclusions;
- the exact universe policy and code revision.

The reviewed Market Data Fabric instrument adapters produce catalog snapshots, but catalog evidence alone does not provide the required historical quality and completed-candle context. A current catalog also cannot be silently treated as an as-of snapshot for the accepted interval.

### Symbol and venue mapping

The accepted import is multi-source and contains hundreds of concrete symbols. A materializer must preserve source and venue identity and must not infer a canonical instrument solely from the symbol string. It must fail closed when a liquidation symbol cannot be mapped to an immutable as-of instrument snapshot for the intended market type.

### Prospective split geometry

No production split geometry is authorized by this preflight. Before reading or generating feature rows, a later request must freeze:

- decision cadence and exact decision timestamps;
- burst window and minimum liquidation history;
- source freshness limits;
- label horizon, even though WH-01 itself produces no labels;
- purge and embargo durations;
- named train/development/evaluation windows;
- partition span;
- protected-holdout exclusion;
- minimum usable row, symbol and temporal-coverage gates.

The accepted interval is approximately 12.47 hours. It provides broad symbol coverage but does not prove temporal or regime diversity and must not be represented as a robust replay corpus by itself.

## Bounded implementation route

The next implementation package must remain WH-01-only and read-only:

```text
accepted immutable Liquid20 import
  + immutable as-of instrument snapshots
  + immutable completed-candle/market-quality evidence
  + prospectively frozen split geometry
  -> validated MarketContextSnapshot stream
  -> validated DynamicUniverseSnapshot history
  -> existing build_wickhunter_dataset()
  -> immutable no-overwrite feature partitions and manifest
```

Required safeguards:

- no network access inside the dataset build step;
- no writable mount of accepted or source evidence;
- exact input hashes and code SHA recorded before materialization;
- deterministic availability ordering and duplicate refusal;
- no current-state backfill masquerading as historical evidence;
- no protected-holdout access;
- atomic output and no overwrite;
- independent reload and hash verification;
- `model_execution_authorized = false`;
- no replay or WH-02 invocation in the same package.

If immutable market-context or universe evidence for the accepted interval cannot be located, the operator must stop with a bounded missing-input report rather than synthesize, query live endpoints or weaken the contract.

## Entry gate for WH-02

WH-02 remains blocked until a separately reviewed run produces all of the following:

- a non-empty `wickhunter-dataset-manifest-v1`;
- exact accepted-import selection identity;
- real market-context and universe snapshot hashes;
- deterministic feature partitions with verified row and partition hashes;
- a prospective purge/embargo split identity;
- an interval ending before the protected holdout;
- an independent reload verification;
- explicit `model_execution_authorized = false`.

Even after this gate passes, replay ordering, labels, costs, slippage, latency and evaluation policy remain a separate WH-02 contract.
