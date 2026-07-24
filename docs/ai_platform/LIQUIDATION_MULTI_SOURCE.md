# Multi-Source Liquidation Collection

## Purpose

Collect liquidation observations from more than one public exchange feed while preserving venue identity,
source-specific limitations, timestamps, and immutable evidence. This package uses Binance USD-M Futures as a
second source beside the existing Bybit linear feed.

No exchange credentials, Freqtrade strategy, order adapter, DCA, leverage, protected holdout, or live capital are
involved.

Authoritative source catalog:

`ai_platform/research/liquidations/source-catalog-v1.json`

Authoritative symbol-universe catalog:

`ai_platform/research/liquidations/symbol-universes-v1.json`

Prospective operational acceptance policy:

`ai_platform/research/liquidations/multi-source-acceptance-policy-v1.json`

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

Use the profiled multi-source runner. It loads one frozen universe and passes the identical ordered symbol list to
both collectors while preserving separate immutable files and summaries.

For a bounded development smoke only:

```bash
set -euo pipefail

RUN_ID="smoke-$(date -u +%Y%m%dT%H%M%SZ)"
ROOT="/var/lib/freqtrade/liquidations/multi-source/$RUN_ID"
COMMIT="$(git rev-parse HEAD)"

LIQUIDATION_STAGING_HOST_ID="staging-eu-01" \
PYTHONPATH=. python -m ai_platform.scripts.liquidation_multi_source_runner \
  --profile liquid20-v1 \
  --duration-seconds 30 \
  --require-new-output \
  --run-id "$RUN_ID" \
  --collector-commit "$COMMIT" \
  --output-root "$ROOT"
```

A smoke confirms process and endpoint compatibility only. It cannot satisfy the frozen 24-hour policy.

## Declared 24-hour acceptance run

Run this package only on the intended non-restricted, always-on staging host. Use an unprivileged service account,
a new directory, a stable non-sensitive host identifier, an exact 40-character collector commit, and an environment
that contains no exchange or Freqtrade trading credentials.

```bash
set -euo pipefail
umask 027

test -z "${BYBIT_API_KEY:-}"
test -z "${BYBIT_API_SECRET:-}"
test -z "${BINANCE_API_KEY:-}"
test -z "${BINANCE_API_SECRET:-}"
test -z "${FT_EXCHANGE_KEY:-}"
test -z "${FT_EXCHANGE_SECRET:-}"
test -z "${FREQTRADE__EXCHANGE__KEY:-}"
test -z "${FREQTRADE__EXCHANGE__SECRET:-}"

RUN_ID="liquid20-$(date -u +%Y%m%dT%H%M%SZ)"
HOST_ID="staging-eu-01"
ROOT="/var/lib/freqtrade/liquidations/multi-source/$RUN_ID"
COMMIT="$(git rev-parse HEAD)"
POLICY="ai_platform/research/liquidations/multi-source-acceptance-policy-v1.json"
REPORT="$ROOT/multi-source-acceptance-report.json"

mkdir -p "$(dirname "$ROOT")"

LIQUIDATION_STAGING_HOST_ID="$HOST_ID" \
PYTHONPATH=. python -m ai_platform.scripts.liquidation_multi_source_runner \
  --profile liquid20-v1 \
  --duration-seconds 86400 \
  --require-new-output \
  --run-id "$RUN_ID" \
  --collector-commit "$COMMIT" \
  --output-root "$ROOT"

PYTHONPATH=. python -m ai_platform.scripts.liquidation_multi_source_evaluator \
  --run-root "$ROOT" \
  --policy "$POLICY" \
  --output "$REPORT"

sha256sum \
  "$ROOT"/*.ndjson \
  "$ROOT"/*-summary.json \
  "$ROOT"/multi-source-manifest.json \
  "$ROOT"/multi-source-acceptance-report.json \
  > "$ROOT/artifact-sha256.txt"

sha256sum --check "$ROOT/artifact-sha256.txt"
```

Do not reuse an output directory or edit artifacts after collection. A failed package remains failed evidence. Move
it to an immutable quarantine location and use a new `RUN_ID` for any separately declared rerun.

## Artifacts and failure preservation

The output directory contains:

- `bybit-linear.ndjson` and `bybit-linear-summary.json`;
- `binance-usdm.ndjson` and `binance-usdm-summary.json`;
- `multi-source-manifest.json` with the exact profile, run and host identity, collector commit, start/end clock probes,
  source status, source statistics and safety policy;
- `multi-source-acceptance-report.json` with every deterministic gate and failed-gate name;
- `artifact-sha256.txt` generated only after evaluation.

The runner refuses to start when recognized trading credential environment variables are present. It uses
`asyncio.gather(..., return_exceptions=True)` so one source failure does not erase evidence from the other source.
It writes a failure-preserving manifest before returning a non-zero result. Source errors are bounded strings and
must not contain credentials or private endpoint data.

The evaluator independently reopens both summaries and NDJSON files. It checks actual file hashes, file sizes,
non-empty line counts, event counts, source semantics, start and end clocks, profile identity, collector commit,
run and host identifiers, source-specific statistics, and cross-source coverage.

## Frozen acceptance gates

The policy is prospective and must not be weakened after observing a run.

Common gates include:

- exact `liquid20-v1` ordered membership and both declared sources;
- at least 86,400 seconds at the package and source levels;
- execution disabled and trading credentials absent;
- valid collector commit, unique run ID, and stable non-sensitive host ID;
- new output files with matching SHA-256, byte size and event line count;
- successful source completion with no hidden collector error;
- synchronized source clocks at both start and end;
- unchanged source-specific feed semantics;
- no cross-exchange deduplication or unlabeled summation.

Each source independently requires at least 99.5% connection availability, no parser failures, no more than two
disconnects per hour, at most a 1% duplicate ratio, and at most 1% of observed event latency samples above five
seconds. Bybit requires at least 20 events across at least eight symbols and 20 latency samples. Binance requires at
least 10 events across at least five symbols and 10 latency samples.

Across both sources, at least 12 distinct symbols must be observed in the union and at least five in the
intersection. This is stricter and more meaningful than forcing one event from every contract during one fixed day,
which could fail solely because legitimate market activity did not occur.

A run passes only when every gate passes. Missing events, inaccessible clocks, insufficient activity, altered
artifacts, source failure, or incomplete duration remain explicit failed evidence; they are not grounds to edit the
policy retrospectively.

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

The original `data-only-staging-policy-v1.json` remains the frozen Bybit Stage 1 policy and is not modified by this
package. The multi-source policy governs only the new combined evidence package.

Passing the multi-source policy authorizes immutable research evidence only. It does not unlock deterministic
replay, signal-only dry-run, Freqtrade dry-run, strategy or model promotion, protected-holdout access, order
execution, DCA, leverage, live capital, or any profitability claim. Each later capability requires a separate,
prospectively declared work package and its own evidence.
