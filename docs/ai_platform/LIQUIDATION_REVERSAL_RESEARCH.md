# Liquidation Reversal Research and Deployment Process

## Purpose

This work package prepares a research-only liquidation reversal track inspired by the public behavior of
Wick Hunter's Original Liquidation Bot. It does not copy proprietary implementation details and does not
authorize trading with real capital.

The intended entry shape is:

```text
trusted liquidation event
AND event notional >= declared minimum
AND event price is outside the declared VWAP/VWMA band
AND deterministic volume/risk filters pass
=> counter-trade the liquidated position side
```

A liquidated long below the lower band may create a long entry candidate. A liquidated short above the
upper band may create a short entry candidate. A liquidation event or a band breach alone is never enough.

## Exact v1 boundary

The first implementation is deliberately narrower than the complete hosted product:

- public Bybit linear `allLiquidation.{symbol}` ingestion only;
- BTCUSDT and ETHUSDT example subscriptions;
- canonical append-only NDJSON events;
- deterministic duplicate detection;
- source timestamp and local receive timestamp preservation;
- counter-trade signal evaluation as a pure function;
- rolling typical-price VWAP using completed candles only;
- no execution adapter;
- no DCA;
- no TP, SL, trailing exit, leverage optimization, or live capital.

The public Wick Hunter material uses both `VWAP` and newer `VWMA` terminology. The existing local research
helper already implements rolling typical-price VWAP, so v1 keeps that method explicit instead of silently
claiming equivalence. A close-price VWMA or optimized/adaptive band is a separate candidate and must be
validated independently.

## Canonical liquidation event

Every stored event contains:

- schema version;
- normalized source and symbol;
- deterministic source event ID;
- normalized liquidated position side (`long` or `short`);
- source occurrence timestamp in milliseconds;
- local receive timestamp in milliseconds;
- price, quantity, and computed USD notional;
- original source-side value.

Exchange order-side conventions are not passed directly into strategy logic. The adapter must normalize the
meaning into the side of the position that was liquidated.

## Deterministic time alignment

For an event occurring inside candle interval `[open, close)`, the event is assigned to that containing
interval for evidence purposes. Signal features may use only candles that were fully closed before the event.
The current partial candle must not be used in historical replay unless an independently recorded intrabar
trade/candle stream proves exactly what was available at the event timestamp.

This conservative rule prevents a replay from using the final high, low, close, or volume of a candle that
had not finished when the liquidation occurred.

## Data collector

The public Bybit collector is invoked explicitly and has no trading credentials:

```bash
python -m ai_platform.scripts.liquidation_collector \
  --symbol BTCUSDT \
  --symbol ETHUSDT \
  --output /var/lib/freqtrade/liquidations/bybit-linear.ndjson
```

Operational requirements:

- run as a dedicated unprivileged service account;
- mount only the append-only data directory;
- do not provide exchange API keys;
- restart on disconnect with bounded exponential backoff;
- monitor last-event/last-message age and process health;
- rotate files externally and preserve every closed file as immutable evidence;
- compute SHA-256 for closed files and record collector commit, start/end timestamps, symbols, endpoint,
  event count, duplicate count, parse failures, disconnects, and latency distribution;
- keep host time synchronized with NTP;
- never repair missing intervals by fabricating events.

A gap must be represented as a gap. Data collected while host time is unsynchronized or while event latency
is outside the declared acceptance policy must be quarantined from research datasets.

## Deployment stages

### Stage 0 — Foundation

Deliver the event contract, Bybit parser, collector, deterministic alignment, signal policy, example disabled
profile, tests, and this process. No network process is automatically started.

Exit gate:

- compile and Ruff pass;
- focused tests pass;
- JSON validation passes;
- CI and review are green;
- profile remains `enabled: false`, execution remains disabled and `dry_run: true`.

### Stage 1 — Data-only staging

Deploy only the public collector. Do not load a Freqtrade strategy and do not provide trading credentials.
Record operational metrics and immutable daily files.

Exit gate must be prospectively declared before collection is judged. At minimum it must cover availability,
clock synchronization, reconnect/gap accounting, parse failures, duplicate handling, event latency, storage
integrity, and symbol/source coverage.

### Stage 2 — Frozen research dataset

Select a completed collection interval that does not overlap the protected final holdout. Freeze:

- exact file hashes;
- collector and parser commit;
- source endpoint and subscribed topics;
- accepted/quarantined intervals;
- candle source and hashes;
- symbol mapping;
- fee and slippage assumptions;
- all signal, volume, exit, DCA, and risk parameters.

No parameter may be changed after examining the reported OOS result without creating a new experiment.

### Stage 3 — Deterministic replay

Replay events in occurrence order while making each decision no earlier than its recorded receive time.
Use only completed candles. Reject duplicates, stale events, unknown sources/symbols, missing VWAP history,
and periods with unaccepted data gaps.

Required evidence:

- event-to-candle alignment tests;
- no-lookahead tests;
- deterministic repeated replay;
- fee/slippage and delayed-entry stress tests;
- separate in-sample, tuning, OOS, and walk-forward windows;
- minimum trade count and maximum drawdown gates;
- full rejected-signal reason counts.

### Stage 4 — Signal-only dry-run

Run the collector and signal engine continuously, but persist hypothetical decisions without submitting
orders. Compare live decisions with deterministic replay semantics and monitor latency, stale-event rejects,
source gaps, and band values.

Promotion requires sustained evidence under a prospectively declared duration and acceptance policy.

### Stage 5 — Freqtrade dry-run execution

Implement a private adapter that converts accepted signal decisions into Freqtrade entry intent. Freqtrade
retains trade lifecycle ownership. The configuration must remain `dry_run: true` and use isolated margin,
fixed leverage, strict position limits, deterministic stop controls, and a kill switch.

DCA remains disabled in the first execution candidate. It can be introduced only as a separate work package
with maximum orders, maximum total exposure, spacing/range rules, stop distance, and liquidation-distance
stress tests declared before evaluation.

### Stage 6 — Shadow and live-small review

Shadow operation compares intended orders with market outcomes without capital. Any live-small transition
requires explicit owner approval, separate credentials without withdrawal permission, a reviewed rollback,
strict exposure and loss limits, alerting, and a separate PR. Nothing in this foundation authorizes it.

## Wick Hunter feature mapping

| Public behavior | Local implementation status |
|---|---|
| Real-time liquidation source selection | Source-agnostic contract; Bybit linear adapter first |
| Minimum liquidation notional | Implemented in pure signal policy |
| Counter-trade liquidated side | Implemented in pure signal policy |
| Long/short VWAP distance bands | Implemented with completed-candle VWAP |
| Pair and direction selection | Implemented in policy contract |
| Volume filters | Contract placeholder; exact metric not selected |
| Entry order and position sizing | Disabled example contract only |
| DCA | Explicitly disabled pending separate risk package |
| TP, SL, trailing exits | Explicitly unselected pending replay declaration |
| Multi-exchange aggregation | Contract supports sources; additional adapters not yet implemented |
| Optimized/adaptive bands | Out of scope for v1 |

## Current blocker after this foundation

The remaining blocker is no longer the absence of a data definition or collector. It is the absence of an
operationally collected, integrity-checked, sufficiently representative frozen dataset and a prospectively
declared replay contract. Until those exist, the strategy remains research-only and cannot make a
profitability claim.
