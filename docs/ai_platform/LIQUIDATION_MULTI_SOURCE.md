# Multi-Source Liquidation Collection

## Purpose

Collect liquidation observations from more than one public exchange feed while preserving venue identity,
source-specific limitations, timestamps, and immutable evidence. This package uses Binance USD-M Futures as a
second source beside the existing Bybit linear feed.

No exchange credentials, Freqtrade strategy, order adapter, DCA, leverage, or live capital are involved.

Authoritative source catalog:

`ai_platform/research/liquidations/source-catalog-v1.json`

Authoritative symbol-universe catalog:

`ai_platform/research/liquidations/symbol-universes-v1.json`

## Sources

### Bybit linear

- endpoint: `wss://stream.bybit.com/v5/public/linear`;
- stream: `allLiquidation.{SYMBOL}`;
- canonical source: `bybit-linear`;
- documented behavior: all liquidation events, pushed every 500 ms;
- event price: bankruptcy price;
- side is normalized to the position that was liquidated.

### Binance USD-M Futures

- endpoint: `wss://fstream.binance.com/market/ws`;
- stream: `{symbol_lower}@forceOrder`;
- canonical source: `binance-usdm`;
- documented behavior: only the latest liquidation order for a symbol in each 1000 ms interval is pushed;
- quantity uses executed accumulated quantity when available, then last fill, then original quantity;
- price uses average fill price when available, then order price;
- `SELL` forced close means a long position was liquidated; `BUY` means a short was liquidated.

The Binance feed is useful as an additional venue observation but is not a complete event-by-event feed. Its
values must not be interpreted as full-market liquidation volume.

## Frozen symbol universe

The default `liquid20-v1` profile contains 20 USDT perpetual symbols:

```text
BTCUSDT ETHUSDT SOLUSDT XRPUSDT DOGEUSDT
BNBUSDT ADAUSDT SUIUSDT LINKUSDT AVAXUSDT
TRXUSDT DOTUSDT LTCUSDT BCHUSDT ETCUSDT
APTUSDT NEARUSDT UNIUSDT FILUSDT ATOMUSDT
```

This is a curated, frozen research universe of established and generally liquid contracts expected to be common
to Bybit linear and Binance USD-M. It is intentionally not described as a live market-cap or 24-hour-volume top
20, because those rankings change continuously and would make replay and acceptance evidence non-reproducible.

Universe rules:

- a profile name, frozen date, exact ordered symbol list, and declared count are persisted;
- all symbols must be uppercase alphanumeric USDT contracts;
- duplicates and count mismatches fail closed;
- changing membership requires a new profile version and fresh endpoint validation;
- more than 50 symbols requires the explicit `--allow-broad-universe` capacity acknowledgement;
- 100 symbols is the hard loader limit, not the recommended starting point.

Starting with 20 increases event frequency substantially relative to BTC and ETH alone while keeping symbol
availability, storage growth, latency, and source-specific gaps auditable. Expansion to 50 should follow a measured
20-symbol run. A 100-symbol universe should be a separate work package with symbol lifecycle, delisting, storage,
and low-liquidity filtering rules.

## Running both collectors

Use the profiled multi-source runner. It loads one frozen universe and passes the identical symbol list to both
collectors while preserving separate immutable files and summaries.

```bash
set -euo pipefail

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/var/lib/freqtrade/liquidations/multi-source/$RUN_ID"
COMMIT="$(git rev-parse HEAD)"

PYTHONPATH=. python -m ai_platform.scripts.liquidation_multi_source_runner \
  --profile liquid20-v1 \
  --duration-seconds 86400 \
  --require-new-output \
  --collector-commit "$COMMIT" \
  --output-root "$ROOT"

sha256sum "$ROOT"/*.ndjson "$ROOT"/*-summary.json "$ROOT"/multi-source-manifest.json \
  > "$ROOT/artifact-sha256.txt"
```

The output directory contains:

- `bybit-linear.ndjson` and `bybit-linear-summary.json`;
- `binance-usdm.ndjson` and `binance-usdm-summary.json`;
- `multi-source-manifest.json` with the exact profile identity, symbol list, clocks, source statistics, and safety
  policy.

The runner refuses to start when trading credential environment variables are present. A failure of either source
is preserved as source-specific evidence; it must not be concealed by availability from the other source.

A custom catalog may be supplied with `--universe-file`, but its exact contents must be committed or preserved with
the run artifacts. Broad profiles above 50 symbols additionally require `--allow-broad-universe`.

## Cross-source treatment

Do not deduplicate events between exchanges. A Bybit event and a Binance event at a similar timestamp are
venue-specific observations and may be separate legs of the same market cascade. Canonical event IDs include the
source, so only duplicates within the same source are rejected.

Do not sum venue values without retaining the source label. Binance's one-event-per-symbol-per-second snapshot
semantics make direct volume comparison with Bybit's all-liquidation feed invalid unless a prospectively declared
normalization method is evaluated.

For future replay, events should be ordered by recorded receive time, then occurrence time, source, and source
event ID. Decisions must still use only candles completed before each event.

## Acceptance boundary

The existing `data-only-staging-policy-v1.json` remains the frozen Bybit Stage 1 policy and is not modified by
this package. Multi-source operational acceptance requires a separately declared policy that covers each source
independently, including:

- exact endpoint and stream contract;
- source-specific clock synchronization;
- connection availability and gaps;
- parser failures and duplicates;
- latency distributions;
- observed symbol coverage;
- immutable file hashes;
- explicit acknowledgement of sampled versus complete feed semantics.

Until that policy and an accepted run exist, Binance data is additional research evidence only. It does not
unlock deterministic replay, signal-only dry-run, Freqtrade dry-run, or any profitability claim.
