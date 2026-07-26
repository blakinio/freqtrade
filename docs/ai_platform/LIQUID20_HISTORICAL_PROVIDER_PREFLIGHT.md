# Liquid20 Historical Provider Preflight

## 1. Scope

This document closes H0, the source and historical-provider preflight declared by
`LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md`.

It verifies current exchange semantics, provider coverage, timestamp provenance, public samples, licensing,
cost category, storage planning, reproducibility risk, and the exact first import request. It does not implement
an importer, download paid data, train a model, run FreqAI, backtest, execute RL, modify the live collector,
change live acceptance, mutate Synology evidence, or access the protected final holdout.

Verification date: `2026-07-26`.

Machine-readable decision package:

```text
ai_platform/research/liquidations/historical/liquid20-provider-decision-v1.json
ai_platform/research/liquidations/historical/provider-decision-v1.schema.json
```

## 2. Decision

**Selected provider for the first event-level import:** Tardis downloadable normalized liquidation CSV.

**Decision status:** `owner_action_required`.

**Recommended common import window:**

```text
start inclusive: 2025-02-26T00:00:00Z
end exclusive:   2026-07-25T00:00:00Z
```

The original candidate start was `2025-02-20T00:00:00Z`. It is narrowed by six days because:

- Bybit officially introduced `allLiquidation` on `2025-02-20`;
- the inspected Tardis normalizer switches from the old Bybit V5 liquidation mapper to the
  `allLiquidation` mapper on `2025-02-26`;
- no paid credential was used to inspect the intervening six days;
- H0 must not silently mix or relabel incompatible semantics.

The six-day range `2025-02-20T00:00:00Z` through `2025-02-26T00:00:00Z` remains excluded unless Tardis
confirms the raw channel and normalized output semantics for that exact interval.

CoinGlass remains an aggregate candle-level fallback or comparison source. It is not selected for event replay.

## 3. Exchange semantics

### 3.1 Bybit linear

Current official Bybit semantics:

- topic: `allLiquidation.<symbol>`;
- coverage: USDT, USDC, and inverse contracts;
- push frequency: `500ms`;
- message `ts`: time in milliseconds when the system generated the message;
- record `T`: liquidation update timestamp in milliseconds;
- `S=Buy`: a long position was liquidated;
- `S=Sell`: a short position was liquidated;
- `v`: executed size;
- `p`: bankruptcy price.

Official semantic-era boundary:

```text
bybit legacy liquidation: before 2025-02-20
bybit allLiquidation:     from 2025-02-20
```

Tardis normalized semantic boundary observed in source:

```text
BybitV5LiquidationsMapper:    before 2025-02-26
BybitV5AllLiquidationsMapper: from 2025-02-26
```

Tardis maps Bybit liquidated-position semantics into normalized liquidation order side:

```text
Bybit S=Buy  -> Tardis side=sell -> long position liquidated
Bybit S=Sell -> Tardis side=buy  -> short position liquidated
```

The normalized Bybit liquidation identifier is empty because the exchange message does not provide an event ID.

### 3.2 Binance USD-M

Current Binance USD-M `forceOrder` semantics are snapshot-limited:

- stream: `<symbol>@forceOrder` or all-market `!forceOrder@arr`;
- since `2021-04-27`, the streams do not provide every real-time liquidation order;
- for each symbol, only the latest liquidation order in a `1000ms` window is pushed;
- no message is pushed when no liquidation occurs in that interval.

Semantic eras:

```text
binance forceOrder real-time era: before 2021-04-27
binance forceOrder snapshot era:  from 2021-04-27
```

The requested 2025-2026 range is wholly inside the snapshot era.

The inspected Tardis Binance mapper:

- accepts only `FILLED` force orders;
- uses `o.T` as the exchange occurrence/trade time;
- uses `o.p` as price;
- uses `o.z` as filled accumulated quantity;
- maps `SELL` to normalized `sell` and `BUY` to normalized `buy`;
- exposes no liquidation ID.

Therefore Binance data must remain in its own namespace and must never be represented as a complete event ledger.

## 4. Provider comparison

| Provider/product | Granularity | Provider capture time | Replay suitability | Authentication | H0 decision |
|---|---:|---:|---|---|---|
| Tardis downloadable liquidation CSV | Event rows sourced from exchange WebSockets; Binance rows inherit snapshot limitation | Yes, `local_timestamp` | Selected for source-aware historical import | First day of month free; bulk access requires API key | Selected, pending owner |
| CoinGlass pair liquidation history | Aggregated long/short USD by interval | Not documented by inspected endpoint | Candle-level comparison only | `CG-API-KEY` | Fallback only |
| Kaiko or another tick vendor | Not preflighted | Unknown | Evaluate only if Tardis is rejected | Expected paid | Deferred |

### 4.1 Why Tardis is selected

Tardis provides the fields needed for a no-lookahead historical contract:

- exchange;
- native symbol;
- exchange timestamp;
- provider-local message-arrival timestamp;
- side;
- price;
- amount;
- liquidation ID when an exchange provides one.

The normalized CSV schema is common across exchanges, while raw files and source semantics remain exchange-specific.

### 4.2 Tardis export semantics

- export format: CSV;
- compression: gzip;
- partition: one file per exchange, data type, symbol, and UTC day;
- day assignment and row order: provider `local_timestamp`;
- provider `timestamp`: exchange timestamp in microseconds, with provider local time as a documented fallback only
  when an exchange timestamp is absent;
- provider `local_timestamp`: message-arrival time in microseconds;
- newly completed daily files: normally available the next day around `06:00 UTC`;
- empty result: a valid empty gzip file may be returned;
- disconnect markers: excluded from normalized CSV and available only in raw replay;
- free access: the first day of each month may be downloaded without an API key;
- bulk access: bearer API key through a paid plan or one-off purchase;
- raw replay pagination: one-minute slices based on provider local timestamp;
- CSV download quota details depend on purchased plan and current provider policy.

Historical provider-local time must map to `provider_captured_at_ms`, never to first-party live
`received_at_ms`.

## 5. Verified coverage

Public provider metadata was downloaded and hashed in GitHub Actions run `30193642455`.

### 5.1 Metadata snapshots

| Exchange metadata | Bytes | SHA-256 | Dataset export range | Reported incidents |
|---|---:|---|---|---:|
| `bybit.json` | 651,818 | `edd2ae8ae020a7464dda28604224279db9fcf25c42f420f802ad59909f91f70d` | `2019-11-07` through `2026-07-26` | 0 |
| `binance-futures.json` | 354,894 | `8a8f634cfdee60f652cbdf555e0e9a1d5d6cef18540ab22e52c6e8a91c7c1731` | `2019-11-17` through `2026-07-26` | 0 |

A current incident count of zero means only that the downloaded provider metadata listed no incidents. It does
not prove that every interval is complete. Future historical acceptance must still detect file absence, empty
files, timestamp gaps, duplicate behavior, and source-specific anomalies.

### 5.2 Exact target availability

| Exchange | Symbol | Symbol available since | Liquidation dataset available since | Verified available through |
|---|---|---|---|---|
| Bybit | `BTCUSDT` | `2020-05-28` | `2020-12-18` | `2026-07-26` |
| Bybit | `ETHUSDT` | `2020-10-21` | `2020-12-18` | `2026-07-26` |
| Binance USD-M | `BTCUSDT` | `2019-11-17` | `2019-11-17` | `2026-07-26` |
| Binance USD-M | `ETHUSDT` | `2019-11-27` | `2019-11-27` | `2026-07-26` |

Both target symbols and the entire recommended range are available according to current provider metadata and
provider liquidation coverage documentation.

## 6. Public sample inspection

Only public first-of-month samples were downloaded. Exact original bytes existed only in the ephemeral GitHub
Actions workspace. Raw files and representative rows were not committed or uploaded as artifacts.

Sample date: `2025-03-01`, which is after the Tardis Bybit `allLiquidation` mapper boundary.

### 6.1 File evidence

| Exchange | Symbol | Rows | Compressed bytes | Uncompressed bytes | Compressed SHA-256 | Uncompressed SHA-256 |
|---|---|---:|---:|---:|---|---|
| Bybit | `BTCUSDT` | 2,092 | 24,661 | 140,039 | `7fae926819808b32cd08c7d55b8a875a3aec13d28c63cfcdab42971523371e1f` | `330156e8b7ba54a828a4d74c5e5d916116f9ec35f1b9441fffc7aea971600746` |
| Bybit | `ETHUSDT` | 1,283 | 16,482 | 85,227 | `ef25b4b786a03b82007e65bc3a87bea15304519646cf756b83fcb4885e04c861` | `b5460e5b54e8d6f07daa4ee9637ed14b890c6e46fbfadb92ae88cb94815eb45b` |
| Binance USD-M | `BTCUSDT` | 1,082 | 17,842 | 84,695 | `59c546d4d65ae682b50697ac63715970b1974a72190b3c4827e8358915b381ba` | `fcf1695902786817cf8c495b8adcbf3d3c65cb2857f3c9f8f9c5b0bbeb88c596` |
| Binance USD-M | `ETHUSDT` | 1,128 | 18,516 | 87,204 | `f89832b8c7d0c59eb687f957e3b74e72de16cb0b623ee9756f9b6b0250f1b79a` | `98c33dd8f44311801a5a14edb43d17680532a2b77b1c424b8b0a78841618df45` |

### 6.2 Common schema and integrity results

Observed header:

```text
exchange,symbol,timestamp,local_timestamp,id,side,price,amount
```

All four files:

- passed gzip decompression;
- matched the documented schema;
- used microseconds since Unix epoch;
- used UTC;
- contained provider-local capture timestamps in every row;
- contained only the requested exchange and symbol;
- contained only `buy` and `sell` side values;
- contained no malformed rows;
- contained no exact duplicate rows;
- contained no non-positive price or amount values;
- contained no row where provider local timestamp preceded exchange timestamp;
- had an empty liquidation ID in every row.

The sample inspection confirms file and field mechanics, not full-period completeness.

### 6.3 Side counts

| Exchange | Symbol | `buy` | `sell` |
|---|---|---:|---:|
| Bybit | `BTCUSDT` | 1,529 | 563 |
| Bybit | `ETHUSDT` | 443 | 840 |
| Binance USD-M | `BTCUSDT` | 592 | 490 |
| Binance USD-M | `ETHUSDT` | 487 | 641 |

For Tardis normalized liquidation rows:

```text
buy  = short position liquidated
sell = long position liquidated
```

## 7. Timestamp contract

The future importer must preserve the provider microsecond fields and derive milliseconds deterministically:

```text
occurred_at_ms          = timestamp // 1000
provider_captured_at_ms = local_timestamp // 1000
imported_at_ms          = importer processing time
received_at_ms          = forbidden for historical provider data
```

No event may be used for a decision at candle close `T` unless:

```text
occurred_at_ms < T
provider_captured_at_ms <= T
```

Tardis CSV files are partitioned by provider local timestamp. Exchange timestamps may be non-monotonic relative
to row order; provider capture order is authoritative for file ordering. Equal exchange timestamps require stable
row order as a tie-breaker.

## 8. Licensing, retention, and redistribution

The inspected Tardis terms permit storage of data and manipulated data on the Customer System for the licensed
internal business use. They prohibit redistribution or resale of raw data, except for separately allowed
aggregated and calculated data with a lowest external resolution of ten minutes.

Consequences:

- licensed raw files may be retained immutably on the private Synology Customer System;
- licensed raw files must not be committed to Git;
- licensed raw files must not be uploaded to normal GitHub artifacts unless the license is separately confirmed
  to permit that transfer;
- internal 5-minute features may be generated for research, but external redistribution of 5-minute values is not
  authorized by this preflight;
- external sharing, publication, or resale requires separate legal and provider review.

This is a technical classification, not legal advice.

## 9. Authentication and cost

Public first-of-month samples require no API key.

The exact requested range requires paid access and an owner-provided Tardis API key. The current order flow
supports a one-off purchase or subscription and states a minimum order of `$300`. The exact price for the four
symbol/exchange series and the requested history was not obtained because H0 does not authorize a purchase.

Subscription history depth depends on plan type and billing interval. A quote must confirm that
`2025-02-26T00:00:00Z` through `2026-07-25T00:00:00Z` is included.

No secret may be stored in Git. A future authorized H3 execution must inject the key through Oteryn's secret
boundary.

## 10. Exact first import request

### 10.1 Provider request

```text
provider:          Tardis
product:           downloadable normalized liquidation CSV
start inclusive:   2025-02-26T00:00:00Z
end exclusive:     2026-07-25T00:00:00Z
days:              514
exchanges:         bybit, binance-futures
native symbols:    BTCUSDT, ETHUSDT
normalized pairs:  BTC/USDT:USDT, ETH/USDT:USDT
data type:         liquidations
files:             2 exchanges × 2 symbols × 514 days = 2,056 gzip CSV files
```

Expected provider URL pattern:

```text
https://datasets.tardis.dev/v1/<exchange>/liquidations/<YYYY>/<MM>/<DD>/<SYMBOL>.csv.gz
```

### 10.2 Storage estimate

The four public files for `2025-03-01` totaled:

```text
compressed:   77,501 bytes
uncompressed: 397,165 bytes
```

A direct 514-day sample-scaled point estimate is:

```text
compressed:   39,835,514 bytes  (37.99 MiB)
uncompressed: 204,142,810 bytes (194.69 MiB)
```

This is not a volume guarantee because liquidation activity is highly variable. Reserve `10 GiB` for raw data,
normalized output, manifests, acceptance reports, quarantine, and variance. H3 must verify free space before
download.

### 10.3 Synology destination

Do not modify the existing live tree:

```text
/volume1/docker/freqtrade-liquidations/data/runs/
```

Use:

```text
/volume1/docker/freqtrade-liquidations/data/historical/
├── imports/
│   └── tardis/
│       └── <import-run-id>/
│           ├── raw/
│           │   ├── bybit/linear-perpetual/<symbol>/<year>/<month>/
│           │   └── binance-futures/usd-m-perpetual/<symbol>/<year>/<month>/
│           ├── normalized/
│           ├── manifests/
│           └── acceptance/
├── datasets/
└── quarantine/
```

Raw files are append-only and immutable.

### 10.4 Required hashes and manifests

Every closed provider file must record:

- request URL;
- exchange;
- market;
- symbol;
- intended UTC local-capture day;
- HTTP status;
- response size;
- gzip integrity;
- exact SHA-256;
- download time;
- provider metadata snapshot SHA-256;
- importer commit;
- acceptance status;
- quarantine reason where applicable.

Required generated files:

```text
historical-import-manifest.json
historical-file-hashes.json
historical-import-acceptance-report.json
historical-source-summary-bybit.json
historical-source-summary-binance-futures.json
historical-rejected-records-summary.json
```

## 11. Historical acceptance implications

Downloading successfully is not acceptance. H1 and later implementation must reject or quarantine:

- missing expected files;
- wrong hashes;
- decompression failures;
- incompatible headers;
- invalid timestamp units or timezone;
- missing provider capture time where the contract requires it;
- invalid symbol mappings;
- non-positive price or amount;
- invalid side values;
- non-deterministic duplicate identity;
- malformed rows;
- unexplained missing intervals;
- semantic-era crossings;
- inconsistent repeated import output.

Do not reuse the live Binance latency gate as the complete historical policy.

Do not treat an empty provider file as proof of zero liquidation volume without accepted source-availability
evidence.

## 12. Reproducibility and vendor lock-in

Tardis creates a material provider dependency because provider-local capture timestamps cannot be reconstructed
from exchange-only archives. The mitigation is:

- retain exact raw provider bytes immutably;
- retain exact metadata snapshots;
- hash every file;
- pin parser and normalizer commits;
- preserve provider timestamp and local timestamp separately;
- keep Bybit and Binance in separate namespaces;
- make all normalized output reproducible from raw hashes;
- record provider incidents and accepted/quarantined intervals;
- do not fabricate event IDs or missing events.

A future switch to another vendor requires a new provider preflight and cannot silently reuse Tardis availability
semantics.

## 13. Owner decisions

H0 requires the owner to decide:

1. **Commercial access:** choose Tardis one-off purchase or subscription and approve the exact quote.
2. **License:** accept internal Customer-System retention and the raw redistribution restriction.
3. **Secret:** authorize creation and Oteryn-only injection of the Tardis API key for H3.
4. **Bybit boundary:** accept the common start `2025-02-26`, or request Tardis confirmation for
   `2025-02-20` through `2025-02-25`.

Storage is currently classified as small. No material storage purchase is indicated, but H3 must confirm at least
`10 GiB` free before execution.

## 14. Rejected hypotheses

- Use `2025-02-20` without resolving the Tardis mapper boundary: rejected.
- Treat Binance `forceOrder` as a complete event ledger: rejected.
- Combine Bybit and Binance into an unqualified total: rejected.
- Use CoinGlass aggregates to fabricate events: rejected.
- Label Tardis local time as first-party `received_at_ms`: rejected.
- Commit public or licensed raw sample rows to Git: rejected.
- Purchase data or request a credential during H0: rejected.
- Train a model during H0: rejected.

## 15. Source register

Verified on `2026-07-26`:

- Bybit all-liquidation WebSocket:
  `https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation`
- Bybit V5 changelog:
  `https://bybit-exchange.github.io/docs/changelog/v5`
- Binance developer documentation:
  `https://developers.binance.com/en/docs/catalog`
- Binance official connector liquidation stream:
  `https://github.com/binance/binance-futures-connector-python/blob/main/binance/websocket/um_futures/websocket_client.py`
- Tardis normalized CSV documentation:
  `https://docs.tardis.dev/downloadable-csv-files`
- Tardis datasets API:
  `https://docs.tardis.dev/downloadable-csv-files/api`
- Tardis raw HTTP API:
  `https://docs.tardis.dev/api/http`
- Tardis Bybit coverage:
  `https://docs.tardis.dev/historical-data-details/bybit`
- Tardis Binance USD-M coverage:
  `https://docs.tardis.dev/historical-data-details/binance-futures`
- Tardis liquidation coverage and semantic notes:
  `https://docs.tardis.dev/faq/data`
- Tardis billing and subscription scope:
  `https://docs.tardis.dev/faq/billing-and-subscriptions`
- Tardis terms:
  `https://docs.tardis.dev/legal/terms-of-service`
- Tardis live metadata:
  `https://api.tardis.dev/v1/exchanges/bybit`
  `https://api.tardis.dev/v1/exchanges/binance-futures`
- CoinGlass pair liquidation history:
  `https://docs.coinglass.com/reference/liquidation-history`
- Tardis open-source Bybit mapper:
  `https://github.com/tardis-dev/tardis-node/blob/3e3f4d704d66d1187037d2e2c48f68b82441e808/src/mappers/bybit.ts`
- Tardis open-source Binance mapper:
  `https://github.com/tardis-dev/tardis-node/blob/3e3f4d704d66d1187037d2e2c48f68b82441e808/src/mappers/binance.ts`

## 16. H0 outcome

H0 is technically complete. Tardis is adequate for the first provider-neutral implementation path, public samples
prove the expected event schema and provider-local capture timestamp, and the recommended common import range is
fully covered.

Bulk access remains blocked on the explicit owner decisions in section 13. H1 must be a separate task and PR.
