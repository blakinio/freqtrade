# Multi-Source Liquidation Collection

## Purpose

Collect liquidation observations from more than one public exchange feed while preserving venue identity,
source-specific limitations, timestamps, and immutable evidence. This package adds Binance USD-M Futures as a
second source beside the existing Bybit linear feed.

No exchange credentials, Freqtrade strategy, order adapter, DCA, leverage, or live capital are involved.

Authoritative source catalog:

`ai_platform/research/liquidations/source-catalog-v1.json`

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

## Running both collectors

Use separate immutable files and summaries. This prevents concurrent append races and keeps source outages and
hashes independently auditable.

```bash
set -euo pipefail

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/var/lib/freqtrade/liquidations/multi-source/$RUN_ID"
COMMIT="$(git rev-parse HEAD)"
mkdir -p "$ROOT"

PYTHONPATH=. python -m ai_platform.scripts.liquidation_collector \
  --symbol BTCUSDT \
  --symbol ETHUSDT \
  --duration-seconds 86400 \
  --require-new-output \
  --collector-commit "$COMMIT" \
  --output "$ROOT/bybit-linear.ndjson" \
  --summary "$ROOT/bybit-linear-summary.json" &
BYBIT_PID=$!

PYTHONPATH=. python -m ai_platform.scripts.liquidation_binance_collector \
  --symbol BTCUSDT \
  --symbol ETHUSDT \
  --duration-seconds 86400 \
  --require-new-output \
  --collector-commit "$COMMIT" \
  --output "$ROOT/binance-usdm.ndjson" \
  --summary "$ROOT/binance-usdm-summary.json" &
BINANCE_PID=$!

wait "$BYBIT_PID"
wait "$BINANCE_PID"

sha256sum "$ROOT"/*.ndjson "$ROOT"/*-summary.json > "$ROOT/artifact-sha256.txt"
```

Both processes must run as an unprivileged service account without exchange credentials. A failure of either
source is preserved as source-specific evidence; it must not be concealed by availability from the other source.

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
