# OKX Liquidation Shadow Source

## Purpose

Add OKX USDT-margined perpetual-swap liquidation observations as a third, isolated research source without
changing the frozen `liquid20-v1` Bybit-plus-Binance collector, its acceptance policy, its Synology evidence,
or the portal's fixed read contract.

This package establishes source semantics, deterministic normalization, a public collector, immutable instrument
metadata and focused tests. It does not deploy the collector, run an operational smoke, add OKX to the portal,
train a model or authorize trading.

## Source identity

Canonical source:

```text
okx-usdt-swap
```

Public endpoints:

```text
WebSocket:   wss://ws.okx.com:8443/ws/v5/public
Channel:     liquidation-orders
Scope:       instType=SWAP
Time:        https://www.okx.com/api/v5/public/time
Instruments: https://www.okx.com/api/v5/public/instruments?instType=SWAP
```

Public WebSocket channels do not require login. The old public REST liquidation-history endpoint was removed in
2023, so OKX is a forward-collection source rather than a free historical-backfill mechanism.

## Why OKX is isolated first

The existing sources have different contracts:

- Bybit publishes `allLiquidation`;
- Binance publishes the latest forced order per symbol in approximately 1000 ms windows;
- OKX publishes grouped liquidation orders on one public SWAP channel.

Adding OKX directly to `liquid20-v1` would change source count, files, manifest, portal discovery, acceptance
thresholds and storage behavior at once. OKX therefore remains shadow-only until a separate smoke and prospectively
declared acceptance task proves its operational behavior.

## Quantity normalization

OKX `sz` is a number of contracts, not base-asset quantity. Every requested v1 instrument must have a frozen public
instrument record satisfying:

```text
instType  = SWAP
ctType    = linear
settleCcy = USDT
ctValCcy  = base asset
ctMult    = 1
state     = live
```

Normalization is:

```text
base_quantity = sz * ctVal
notional_usd  = base_quantity * bkPx
```

The adapter rejects missing, suspended, inverse, non-USDT, unexpected-multiplier or inconsistent metadata. It must
never calculate `notional_usd` as `sz * bkPx`.

The collector writes an immutable instrument snapshot before collection. The source summary records its endpoint,
file name, SHA-256 and contract count.

## Symbol and side mapping

Explicit v1 symbol examples:

```text
BTC-USDT-SWAP -> BTCUSDT
ETH-USDT-SWAP -> ETHUSDT
```

The collector subscribes once to the public SWAP channel and filters locally to declared canonical symbols. Events
for unrelated instruments are ignored before metadata lookup. A requested symbol without valid metadata fails before
WebSocket collection starts.

The canonical side is the position that was liquidated:

```text
posSide=long                      -> liquidated long
posSide=short                     -> liquidated short
posSide=net and side=sell         -> liquidated long
posSide=net and side=buy          -> liquidated short
```

Unsupported combinations fail closed.

## Canonical event mapping

```text
source                         = okx-usdt-swap
symbol                         = canonical mapping from instId
occurred_at_ms                 = details[].ts
received_at_ms                 = local collector receipt time
price                          = details[].bkPx
quantity                       = details[].sz * frozen ctVal
notional_usd                   = quantity * price
raw_side                       = side:posSide
liquidated_position_side       = normalized position side
```

Cross-exchange observations are never deduplicated.

## Collector

Entry point:

```text
python -m ai_platform.scripts.liquidation_okx_collector
```

Development example:

```bash
PYTHONPATH=. python -m ai_platform.scripts.liquidation_okx_collector \
  --symbol BTCUSDT \
  --symbol ETHUSDT \
  --duration-seconds 60 \
  --require-new-output \
  --collector-commit "$(git rev-parse HEAD)" \
  --output /tmp/okx-usdt-swap.ndjson \
  --summary /tmp/okx-usdt-swap-summary.json \
  --instrument-metadata /tmp/okx-usdt-swap-instruments.json
```

Properties:

- public endpoints only;
- refuses recognized OKX and Freqtrade trading credentials;
- append-only canonical NDJSON;
- source and local timestamps preserved;
- exact instrument snapshot written before collection;
- SHA-256, line count, connection, parse, duplicate, symbol and latency evidence;
- OKX text ping/pong heartbeat;
- bounded reconnect backoff;
- no inbound port, strategy, account or capital authority.

## Explicit non-integration boundary

This package does not change:

- `liquid20-v1` membership or runner;
- `multi-source-acceptance-policy-v1.json`;
- current Bybit or Binance thresholds;
- Synology deployment or active containers;
- portal file discovery or source filters;
- replay, FreqAI or RL feature contracts;
- Phase 5, Phase 6 or protected-holdout evidence;
- trading execution.

## Required next package

Before OKX can join a future `liquid20-v2`, declare a separate shadow staging package that freezes exact symbols,
duration, host identity, endpoints, instrument-snapshot acceptance, clocks, activity, availability, disconnect,
parser, duplicate, latency and artifact-integrity gates.

A short public smoke proves transport only. A later accepted run may authorize research evidence, never trading.

## Subsequent source order

After OKX shadow evidence is accepted, the next recommended source preflight is BitMEX. BitMEX exposes a liquidation
table containing order ID, symbol, side, price and remaining quantity, and table data is available through WebSocket.
It needs an independent instrument-value and side-semantics contract before canonical notional is computed.

Gate.io, Deribit, Kraken Futures and CoinEx remain deferred because their available data is respectively bounded REST
history, delayed liquidation markers, aggregate liquidation volume, or a lower-priority venue. They must not be added
inside the OKX acceptance package.
