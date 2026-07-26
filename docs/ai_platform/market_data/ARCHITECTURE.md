# Market Data Fabric Architecture v1

Status: **foundation contracts only**  
Manifest: `docs/ai_platform/market_data/architecture-v1.json`  
Source declarations: `ai_platform/market_data/source-catalog-v1.json`

## 1. Purpose and boundary

The Market Data Fabric is a provider-neutral evidence layer for public market data. Version 1 freezes identities, timestamps, immutable artifact contracts, deterministic universe selection and failure semantics. It does not connect to an exchange, download instruments, start capture, reconstruct an order book, compact files, execute replay, train a model or submit an order.

Generic infrastructure belongs under `ai_platform/market_data/`. Existing Liquid20 code remains under `ai_platform/research/liquidations/` and retains its current source identities, schemas, frozen universe, acceptance rules and evidence. Liquid20 may later consume an explicitly versioned normalized output through a separate adapter; this foundation does not move or reinterpret Liquid20 data.

## 2. Initial venue and market identity

The bounded venue set is Binance, Bybit and OKX. Market identity is explicit and cannot be inferred from a symbol string:

```text
exchange + market_type + native_instrument_id
```

`market_type` is one of `spot`, `perpetual` or `dated_future`. The canonical instrument ID is:

```text
<exchange>:<market_type>:<native_instrument_id>
```

A native symbol and a canonical symbol are both preserved. Mapping never removes exchange or market identity, and similarly named observations on different venues are never cross-exchange duplicates.

The declared initial product families are Binance Spot, Binance USD-M derivatives, Bybit Spot, Bybit Linear derivatives, OKX Spot and OKX SWAP/FUTURES. Every channel is marked not implemented and not validated. A declaration is not source acceptance.

## 3. Data tiers and universe snapshots

Three immutable profiles are supported:

| Profile | Intended tier | Foundation policy |
|---|---|---|
| `all-active-lite-v1` | lightweight status and catalog coverage for every supplied active instrument | deterministic source union, no rank limit |
| `top100-microstructure-v1` | trades and reconstructible L2 candidates | deterministic 50 spot plus 50 derivatives source-union rank |
| `top20-high-frequency-v1` | highest-frequency candidate profile | deterministic 10 spot plus 10 derivatives source-intersection rank |

The 50/50 and 10/10 splits are unvalidated foundation policy values for synthetic contract tests. They are not claims about live exchange liquidity. A later source and instrument-catalog preflight must validate or replace them prospectively before any capture request.

Selection is pure: it accepts supplied immutable instrument and metric snapshots and performs no network access. Spot and derivatives have separate ranking components. Source intersection or union, missing-metric behavior and stable tie-breakers are explicit. Every included and excluded instrument receives reason codes. Repeated equal inputs produce the same ordered membership and snapshot hash.

## 4. Source-native raw capture and normalized events

A future collector must preserve the source-native payload or an immutable payload reference in `RawMarketEventEnvelope`. The envelope binds:

- schema and event type;
- exchange, market type and instrument identity;
- native and canonical symbols;
- exchange occurrence timestamp;
- decision-availability timestamp and its provenance kind;
- ingestion timestamp;
- connection and capture-run identities;
- sequence, previous sequence and snapshot state;
- exact raw-payload SHA-256.

`availability_timestamp_kind` distinguishes first-party `live_collector_receive` from historical `provider_capture`. Historical provider capture time must never be written as first-party live receive time. Exchange occurrence time is not automatically decision availability time.

Normalized events are deterministic derivatives of exact raw segment hashes plus a pinned normalizer commit and contract version. They never replace the immutable raw source of truth.

## 5. Instrument snapshots and mapping

`InstrumentSnapshot` preserves exact source snapshot identity and SHA-256 together with venue, market, native and canonical identities, base, quote and settlement assets, contract type and value, tick size, quantity step, active state, listing time and expiry when supplied.

Spot instruments reject derivative settlement, contract and expiry metadata. Perpetual instruments require contract metadata and reject expiry. Dated futures require contract metadata and expiry. Missing derivative metadata fails closed; it is never guessed from symbol text.

## 6. Capture and connection identity

A `CaptureRequest` prospectively freezes the source-catalog version, exact universe snapshot IDs, exchanges, markets, channel families, start and optional bounded end conditions, raw segment, compression, clock and gap policies, credential policy, output-root identity and code commit.

A capture run has one immutable `capture_run_id`. Each transport lifecycle has a distinct `connection_id`. Reconnects do not reuse the prior connection identity. The capture manifest records source/channel states and every connection interval.

No runtime request is committed by this package.

## 7. Immutable raw segments

Source-native records are written to bounded raw segments. A closed `SegmentManifest` binds the capture, source, channel, connection, instruments, time interval, first and last event identities, sequence bounds, counts, bytes, compression and exact content hash.

A closed segment is valid only when `immutable=true`, `closure_state=closed`, its content hash is known and its self-hash and deterministic segment ID verify. Closed bytes are never edited. Corrections create a new segment and provenance chain; they do not rewrite the old segment.

Object storage or a filesystem may hold authoritative segment bytes. ClickHouse, caches, compacted files and query indexes are derived stores and never the immutable source of truth.

## 8. Gaps, reconnects and resynchronization

Disconnects, reconnects, sequence discontinuities and provider-missing intervals remain explicit `GapMarker` records. A marker binds its source, connection, channel, optional instrument, detected time, sequence or interval bounds and resolution evidence.

For order books:

1. a snapshot establishes a valid sequence base;
2. deltas must satisfy the source-specific sequence contract;
3. any unresolved gap, disconnect or reconnect without resynchronization invalidates the reconstructed book;
4. the book remains invalid until a successful new snapshot is preserved in a closed immutable resynchronization segment;
5. no stale or partial book is represented as healthy.

Source-specific snapshot/delta rules are deliberately deferred to separate verified connector packages.

## 9. Storage, compaction and quarantine

The logical storage layers are:

```text
raw immutable segments
  -> deterministic normalized partitions
  -> optional deterministic compaction
  -> consumer-specific derived artifacts and indexes
```

Each derived layer references exact input hashes and the producing code revision. Compaction never changes event meaning or removes gap markers. Invalid schema, hash, identity, sequence, clock or source evidence is quarantined with explicit reason codes. Missing or quarantined data never becomes an implicit zero.

Licensed or real raw market records are not committed to Git. Retention and redistribution remain provider-license decisions.

## 10. Historical providers and timestamp semantics

Historical imports preserve provider capture time as `provider_capture`. Provider timestamps, file boundaries and incident evidence remain source-specific provenance. A historical provider can support deterministic replay only when raw bytes, hashes, parser version, timestamp semantics and accepted or quarantined intervals are frozen.

Provider capture time cannot prove the time a first-party collector would have received the event. Cross-era or cross-provider comparisons require explicit semantic-era and quality evidence; they are not silently normalized into equivalent live latency.

## 11. Deterministic replay boundary

Replay is a later package. Before replay starts, a separate request must freeze total ordering, tie-breakers, sequence and duplicate policy, availability rule, gap and outage behavior, resynchronization, candle alignment, price sampling, fees, slippage, latency and evaluation windows.

Replay consumes only accepted immutable segment identities and produces new self-hashed evidence. It cannot mutate raw capture, repair missing observations, reinterpret timestamp kinds or authorize trading.

## 12. Consumer boundaries

- **Liquid20** retains its existing contracts and source-specific acceptance. Integration requires an explicit adapter and cannot change frozen evidence.
- **FreqAI** may consume versioned normalized or feature artifacts only after availability and no-lookahead contracts pass.
- **RL** may consume a separately versioned observation schema only after deterministic data and replay evidence exists. It cannot change the completed RL-v2 evidence implicitly.
- **Portal** is a read-only observability consumer of bounded derived evidence. It cannot choose host paths, start capture, mutate evidence or access exchange endpoints directly.

Models, strategies and portal code cannot bypass deterministic risk or execution boundaries.

## 13. Credential and trading boundary

The fabric uses public market-data access only. Trading and account credentials, private account streams, order or account endpoints, order submission, DCA, leverage changes and live capital are outside this package. A future collector must refuse recognized trading credential environment variables. Any later trading configuration remains `dry_run: true` until a separately reviewed execution package is authorized.

## 14. Dependency-ordered implementation program

Each item is a separate small PR with a dated checkpoint:

1. **Foundation v1 — this package:** contracts, schemas, source declarations, deterministic universe selector and synthetic tests.
2. **Source and instrument-catalog live preflight:** verify current official documentation, product/channel semantics, rate and connection constraints, symbol metadata and sample payloads; perform no broad capture.
3. **Instrument snapshot adapters:** bounded public REST metadata readers with immutable snapshots and mappings.
4. **One-source raw collector prototype:** one venue/product/channel family, bounded duration, immutable segments and gap evidence.
5. **Snapshot/delta order-book validation:** source-specific sequencing, reconnect and resynchronization evidence using bounded synthetic and public smoke data.
6. **Multi-source bounded capture:** only after separate source acceptance and capacity evidence; no trading credentials.
7. **Normalization and compaction:** deterministic output from exact segment hashes, quarantine and reproducibility tests.
8. **Deterministic replay:** prospectively frozen replay request and no-lookahead evidence.
9. **Consumer adapters:** independent Liquid20, FreqAI, RL and portal packages after their entry gates pass.

The immediate next package is item 2. It must not be combined with this foundation.
