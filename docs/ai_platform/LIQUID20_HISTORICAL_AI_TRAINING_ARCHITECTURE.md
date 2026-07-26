# Liquid20 Historical Backfill and AI Training Architecture

## 1. Purpose

Define a safe, reproducible path from historical liquidation market data to FreqAI and reinforcement-learning
research without changing the completed Phase 6 result, the frozen Phase 5 thresholds, the protected final
holdout, or the live-capital boundary.

This document covers:

- exchange-source expansion policy;
- historical-provider selection and import;
- immutable storage and provenance;
- historical-data acceptance;
- event-to-candle feature engineering;
- supervised-model feature ablation;
- later RL observation experiments;
- cross-repository Synology operation;
- the implementation sequence for the next autonomous agent.

It is an architecture and execution declaration. It does not download paid data, train a model, execute a
strategy, change the collector policy, or authorize promotion.

## 2. Authoritative state on 2026-07-26

### 2.1 Live collection

Liquid20 currently collects public liquidation events from:

- Bybit linear derivatives;
- Binance USD-M futures.

The immutable collector image is built from Freqtrade commit
`c00a091c5adc67cf75c46db5805e358ffc72fad7` and is operated by the trusted Synology control plane in
`blakinio/Oteryn-Platform`.

The first uninterrupted 24-hour run:

- completed collection and evidence hashing;
- observed all 20 frozen symbols on both exchanges;
- passed every frozen gate except
  `binance-usdm.maximum_latency_over_threshold_ratio`;
- remains immutable on Synology.

One unchanged retry is running under the same image, symbol universe, duration, schemas, and thresholds. A
repeated failure must be diagnosed in a separate bounded Freqtrade work package. The threshold must not be
weakened merely to obtain a pass.

### 2.2 Portal

The private-LAN portal reads the Liquid20 evidence tree through a read-only mount. It is an observability
consumer only. It has no Docker socket, exchange credentials, training authority, execution authority, or
permission to modify evidence.

### 2.3 AI research

The existing FreqAI baseline, completed LightGBM-versus-XGBoost Phase 6 comparison, PyTorch track, and RL-v2
track do not currently consume Liquid20 features.

The authoritative completed Phase 6 result remains:

```text
selected_model = null
```

The Liquid20 feature track is a new isolated research programme. It cannot reopen or reinterpret Phase 6.

## 3. Non-negotiable boundaries

The implementation must not:

- modify the frozen Phase 5 entry or exit thresholds;
- alter Phase 6 candidates, feature set, windows, selection policy, evidence, or result;
- access or consume `20260801-20260930` for training, tuning, feature selection, model selection, iterative
  evaluation, or debugging;
- treat a historical vendor timestamp as equivalent to the local live collector timestamp without explicit
  provenance;
- merge source-specific liquidation values into one number while hiding exchange semantics;
- fabricate missing events or intervals;
- classify a failed or incomplete acceptance interval as accepted;
- commit raw licensed datasets, API tokens, exchange credentials, or generated model artifacts;
- allow an ML model to bypass deterministic strategy and risk controls;
- enable trading, DCA, leverage optimization, live capital, or promotion.

## 4. Source strategy

### 4.1 Current sources

| Source | Role | Semantics | Decision |
|---|---|---|---|
| Bybit linear | Primary event-level source | Current `allLiquidation` stream reports all liquidation updates at a documented 500 ms push frequency | Keep |
| Binance USD-M | Secondary event-level source | `forceOrder` is snapshot-limited and must not be interpreted as a complete event ledger | Keep with source-specific quality masks |

Bybit introduced the current full `allLiquidation` topic on 2025-02-20 and deprecated the previous topic that
pushed only one liquidation per second. Therefore historical Bybit records before and after that boundary are
separate semantic eras.

### 4.2 Exchange expansion order

Exchange adapters are added only after the current two-source path is operationally understood.

| Priority | Source | Intended use | Entry condition |
|---|---|---|---|
| 1 | OKX | Third live shadow source and cross-exchange agreement features | Fresh official API preflight, parser contract, isolated acceptance |
| 2 | BitMEX | Independent BTC validation and liquidation-order research | Separate semantics declaration and symbol mapping |
| Later | Gate.io | Historical or bounded supplemental research | Proven API coverage and publication semantics |
| Later | Deribit | BTC/ETH derivatives and options research | Explicit delayed/publication semantics |
| Later | Kraken Futures | Aggregated regime context | Never represented as event-level data |
| Later | CoinEx or another venue | Coverage experiment | Measurable incremental value after ablation |

No new exchange may be added directly to a combined total. Each source receives its own adapter, acceptance
report, feature namespace, and ablation variant.

## 5. Historical-provider decision

### 5.1 Preferred provider: Tardis

Tardis is the preferred first preflight candidate because its normalized liquidation files expose:

- exchange;
- symbol;
- exchange timestamp;
- provider-local arrival timestamp;
- liquidation identifier when available;
- side;
- price;
- amount.

Its documentation reports liquidation coverage for Bybit derivatives and Binance USD-M futures, including the
Binance `forceOrder` stream. This is close to the existing Liquid20 event contract but is not automatically
identical to it.

A provider subscription or purchase is an owner decision and must be separated from implementation. The agent
may implement a provider-neutral importer and validate free samples, but may not purchase a plan or expose a
provider token.

### 5.2 Secondary provider: CoinGlass

CoinGlass provides exchange- and pair-specific historical long/short liquidation amounts aggregated into time
intervals. It can support a fast candle-level feature baseline, but it cannot reproduce event-level Wick Hunter
replay semantics.

CoinGlass data must use a separate schema and feature namespace such as:

```text
coinglass_binance_long_liquidation_usd_15m
coinglass_binance_short_liquidation_usd_15m
```

It must not be converted into fabricated individual liquidation events.

### 5.3 Other vendors

Kaiko or another tick-data vendor may be evaluated only through the same provider preflight. Provider choice
must be based on exact coverage, timestamp semantics, licensing, reproducibility, export format, incident
metadata, and cost. Marketing claims are not acceptance evidence.

## 6. Recommended historical window

The first event-level candidate window is:

```text
start inclusive: 2025-02-20T00:00:00Z
end exclusive:   2026-07-25T00:00:00Z
```

Reasons:

- it begins with Bybit's current `allLiquidation` semantic era;
- it ends before the current first-party Liquid20 live collection began;
- it remains before the protected final holdout beginning on 2026-08-01;
- it provides enough history for a meaningful technical and historical-development study if provider coverage
  is complete.

This is a candidate import window, not a frozen training split. Exact source coverage, incidents, and symbol
availability must be inspected first. A chronological train/tune/test contract must be merged before the first
model execution.

Older history may be retained in separate semantic-era partitions for later research, but it must not be mixed
silently with the post-2025-02-20 Bybit era.

## 7. End-to-end architecture

```text
Exchange public WebSockets                    Historical vendor exports
(Bybit, Binance, later OKX)                   (Tardis first; CoinGlass secondary)
             |                                              |
             v                                              v
 First-party live collector                       Raw immutable import files
             |                                              |
             v                                              v
 Live acceptance report                       Historical import acceptance
             |                                              |
             +-------------------+--------------------------+
                                 |
                                 v
                    Canonical source-aware event layer
                                 |
                                 v
                    Deterministic availability-time join
                                 |
                                 v
                 Atomic 5m liquidation feature partitions
                                 |
                   +-------------+-------------+
                   |                           |
                   v                           v
           Derived 15m FreqAI set        Event replay evidence
                   |                           |
                   v                           v
       LightGBM feature ablation       Wick Hunter research track
                   |
                   v
       Optional XGBoost confirmation
                   |
                   v
       RL-v2 observation-only variant
                   |
                   v
       Shadow / dry-run parity checks
```

The supervised feature ablation is the first model experiment. RL receives liquidation observations only after
the supervised track demonstrates stable incremental value.

## 8. Cross-repository ownership

### `blakinio/freqtrade`

Owns:

- provider-neutral historical contracts;
- provider adapters and parsers;
- canonical normalization;
- historical acceptance and manifests;
- event-to-candle feature generation;
- dataset snapshots;
- FreqAI and RL research contracts;
- tests and model evidence;
- immutable image source.

### `blakinio/Oteryn-Platform`

Owns:

- the trusted Synology runner control plane;
- exact-SHA image build, publication, and deployment;
- provider-token injection through repository or environment secrets;
- bounded download/import execution on Synology;
- metadata-only status publication;
- explicit evidence collection operations.

Oteryn must treat the Freqtrade source commit and image as immutable inputs. It must not patch Freqtrade code,
weaken acceptance, or rewrite provenance.

### Portal

The portal may later display historical dataset metadata and experiment state. It remains read-only and must not
start downloads, imports, training, model promotion, or trading.

## 9. Synology storage layout

Existing live evidence must remain in place. Do not move, rename, or chmod current run directories.

```text
/volume1/docker/freqtrade-liquidations/data/
├── runs/
│   ├── liquid20-20260724T170830Z-1/
│   └── liquid20-.../
├── github-uploaded/
│   └── <run-id>
├── historical/
│   ├── imports/
│   │   └── <provider>/
│   │       └── <import-run-id>/
│   │           ├── raw/
│   │           ├── normalized/
│   │           ├── manifests/
│   │           └── acceptance/
│   ├── datasets/
│   │   └── <dataset-id>/
│   │       ├── features-5m/
│   │       ├── features-15m/
│   │       ├── manifests/
│   │       └── reports/
│   └── quarantine/
│       └── <import-run-id>/
└── control/
    └── non-immutable operation markers only
```

Rules:

- raw files are append-only and never edited in place;
- normalized files are reproducible from raw files and pinned code;
- every closed file receives a SHA-256 digest;
- quarantine is explicit and never silently promoted;
- generated datasets never modify raw or live evidence;
- GitHub artifacts are optional bounded copies, not the authoritative store;
- licensed raw data is not uploaded unless the provider license explicitly permits it.

## 10. Proposed repository structure

```text
ai_platform/research/liquidations/
├── historical/
│   ├── __init__.py
│   ├── contracts.py
│   ├── manifests.py
│   ├── semantic_eras.py
│   ├── normalization.py
│   ├── acceptance.py
│   ├── temporal_join.py
│   ├── features.py
│   ├── datasets.py
│   └── providers/
│       ├── __init__.py
│       ├── base.py
│       ├── tardis.py
│       └── coinglass.py
├── historical-import-policy-v1.json
├── feature-contract-v1.json
└── experiment-contracts/
    ├── liquid20-lightgbm-ablation-v1.json
    └── liquid20-rl-observation-v1.json

ai_platform/scripts/
├── liquidation_history_preflight.py
├── liquidation_history_import.py
├── liquidation_history_acceptance.py
├── liquidation_feature_dataset.py
└── liquidation_feature_ablation.py

tests/ai_platform_integration/
├── test_liquidation_history_contracts.py
├── test_liquidation_history_import.py
├── test_liquidation_history_acceptance.py
├── test_liquidation_temporal_join.py
├── test_liquidation_feature_dataset.py
└── test_liquidation_feature_ablation_contract.py

docs/ai_platform/
├── LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
└── LIQUIDATION_REVERSAL_RESEARCH.md

docs/agents/tasks/
└── FTAI-20260726-liquid20-historical-ai-training.md

docs/agents/prompts/
└── FTAI-20260726-liquid20-historical-ai-training.md
```

Provider-specific modules must contain parsing and provider semantics only. Feature and model code must consume
the provider-neutral canonical layer.

## 11. Historical event contract

Do not overwrite the meaning of the existing live `received_at_ms` field. Historical vendor arrival timestamps
have a different provenance.

A normalized historical record should include at minimum:

```json
{
  "schema_version": 1,
  "source": "bybit-linear",
  "symbol": "BTCUSDT",
  "liquidated_position_side": "long",
  "occurred_at_ms": 1740000000000,
  "available_at_ms": 1740000000123,
  "available_at_semantics": "vendor_capture_timestamp",
  "price": "104500.50",
  "quantity": "0.25",
  "notional_usd": "26125.125",
  "source_event_id": "...",
  "dataset_origin": "historical_vendor",
  "historical_provider": "tardis",
  "provider_exchange": "bybit",
  "provider_timestamp_us": 1740000000000000,
  "provider_local_timestamp_us": 1740000000123000,
  "native_channel": "allLiquidation",
  "semantic_era": "bybit-all-liquidation-v1",
  "import_run_id": "liquid20-history-...",
  "raw_file_sha256": "..."
}
```

Timestamp conversion from microseconds to milliseconds must be deterministic. Preserve the original
microsecond fields. Never infer precision that the source did not provide.

For aggregate providers without a defensible event-availability timestamp, expose candle aggregates only and
lag them by at least one completed feature interval unless a prospectively reviewed publication-time contract
proves earlier availability.

## 12. Semantic eras

At minimum, partition:

```text
bybit-legacy-liquidation:       before 2025-02-20
bybit-all-liquidation-v1:       from 2025-02-20
binance-force-order-pre-sample: before provider-documented snapshot change
binance-force-order-snapshot:   current sampled/snapshot era
first-party-liquid20-live:      locally collected data from 2026-07-25
```

Exact Binance transition dates and provider capture behavior must be pinned from source documentation in the
preflight manifest. A semantic-era boundary is metadata, a partition key, and a model-analysis dimension. It
must not be hidden inside a single uninterrupted series.

## 13. Historical acceptance

Historical acceptance is separate from live collector acceptance.

### Required import gates

- provider and product identifiers are exact;
- requested date and symbol coverage are recorded;
- download responses and closed files are hashed;
- raw files are immutable;
- schema version and parser commit are recorded;
- all numeric fields are decimal-safe and finite;
- source side is normalized into liquidated-position side;
- impossible price, quantity, notional, and timestamp records are rejected;
- exact duplicates are counted deterministically;
- gaps and provider incidents are represented, never fabricated;
- semantic-era boundaries are assigned;
- symbol mapping is explicit;
- provider timestamp and provider-local timestamp ordering is measured;
- data-license restrictions are recorded;
- the protected final holdout is excluded;
- acceptance and quarantine intervals are explicit.

### Required report outputs

```text
historical-import-manifest.json
historical-import-acceptance-report.json
historical-source-summary-<source>.json
historical-rejected-records-summary.json
historical-file-hashes.json
```

A report may pass with documented gaps only when the prospectively frozen policy permits those gaps and feature
rows carry the corresponding quality masks. Passing must never mean pretending the gaps do not exist.

## 14. Temporal alignment and no-lookahead rule

For a feature interval ending at time `T`, an event may contribute only when:

```text
occurred_at_ms < T
AND available_at_ms <= T
```

The resulting feature is available no earlier than the next decision boundary. For example, liquidation events
inside a 5-minute interval ending at 12:05 may be used for a decision at or after 12:05, never for a decision
inside that completed interval.

Rules:

- use completed candles only;
- use provider capture time as the historical information-availability boundary when available;
- use first-party receive time for local live data;
- preserve both occurrence and availability time;
- reject or quarantine negative latency beyond a small declared clock-tolerance policy;
- never fill a missing liquidation interval with fabricated zero unless a separate `source_available` mask
  proves that the source was observed and no events occurred;
- use explicit missing values when source availability is unknown.

The same join implementation must support deterministic replay and repeatable dataset generation.

## 15. Feature contract

### 15.1 Atomic 5-minute features

Generate source-specific features first:

```text
<source>_long_liq_count_5m
<source>_short_liq_count_5m
<source>_long_liq_notional_5m
<source>_short_liq_notional_5m
<source>_largest_liq_notional_5m
<source>_liq_count_imbalance_5m
<source>_liq_notional_imbalance_5m
<source>_time_since_last_liq_s
<source>_liq_notional_zscore_1h
<source>_liq_notional_percentile_24h
<source>_source_available
<source>_source_accepted
<source>_gap_detected
<source>_latency_p50_ms
<source>_latency_p95_ms
<source>_latency_over_threshold_ratio
<source>_semantic_era
```

### 15.2 Price and liquidity context

```text
<source>_liq_price_distance_from_close_atr
<source>_liq_price_distance_from_vwap_atr
<source>_liq_notional_to_quote_volume
<source>_liq_burst_during_atr_expansion
<source>_long_liq_below_lower_vwap_band
<source>_short_liq_above_upper_vwap_band
```

### 15.3 Cross-exchange features

Cross-source features may be added only after source-specific columns exist:

```text
bybit_binance_liq_direction_agreement_5m
bybit_binance_notional_rank_spread_5m
bybit_binance_burst_time_delta_s
accepted_source_count_5m
```

Avoid a raw `total_exchange_liquidations` feature in v1. Differing exchange publication rules make an unqualified
sum misleading.

### 15.4 Derived 15-minute features

The current FreqAI baseline uses a 15-minute base timeframe. Build 5-minute atomic partitions once, then derive
15-minute features deterministically from exactly three closed 5-minute partitions. Do not independently
re-query or reparse raw data for each timeframe.

## 16. Dataset snapshot contract

Each frozen dataset must include:

```json
{
  "dataset_id": "liquid20-features-v1-...",
  "created_at": "...",
  "pairs": ["BTC/USDT:USDT", "ETH/USDT:USDT"],
  "atomic_timeframe": "5m",
  "model_timeframes": ["15m"],
  "source_semantic_eras": {},
  "import_run_ids": [],
  "raw_file_sha256": {},
  "acceptance_report_sha256": {},
  "candle_file_sha256": {},
  "feature_builder_commit": "...",
  "feature_contract_sha256": "...",
  "symbol_mapping_version": 1,
  "availability_policy": "occurred_at_ms < close && available_at_ms <= close",
  "protected_holdout_excluded": true
}
```

The snapshot must be reproducible from raw files, manifests, candle files, and one pinned code revision.

## 17. First model experiment

### 17.1 Model order

1. LightGBM feature ablation.
2. Optional XGBoost confirmation only after the LightGBM experiment is interpretable.
3. RL-v2 observation-only variant only after supervised evidence demonstrates stable incremental value.
4. More complex PyTorch sequence models only after sufficient event volume and baseline evidence exist.

### 17.2 Ablation variants

The first supervised contract should compare:

| Variant | Inputs |
|---|---|
| A | Existing baseline features only |
| B | Baseline plus accepted Bybit features |
| C | Baseline plus accepted Binance features |
| D | Baseline plus accepted Bybit and Binance source-specific features |
| E, optional | Variant D plus cross-exchange agreement features |

Freeze across variants:

- target definition;
- strategy code;
- model class and parameters;
- random seeds;
- pairs and timeframes;
- candle data and hashes;
- train, tune, and historical test windows;
- fees and slippage;
- entry and exit thresholds;
- risk assumptions;
- missing-data policy.

Do not tune the feature set and model parameters simultaneously.

### 17.3 Evidence

Compare at minimum:

- predictive metrics;
- historical-test return and drawdown;
- trade count;
- monthly and pair stability;
- seed stability;
- feature importance and permutation importance;
- performance with delayed event availability;
- performance with each source masked;
- behavior around gaps and rejected intervals;
- rejected-signal reason counts.

Historical backfill evidence is historical-development evidence. It is not authorization to claim strict unseen
final validation, superiority, or promotion.

## 18. RL-v2 integration

Liquidation features may later extend the RL observation vector. The first RL variant must change only the
observation feature contract.

It must not simultaneously change:

- reward function;
- action space;
- trade lifecycle;
- entry or exit policy;
- ROI or stop-loss behavior;
- training seed contract;
- fees or market-data geometry.

The RL experiment must have its own identifier, immutable observation schema, seed set, and evidence. Existing
RL-v2 evidence remains unchanged.

## 19. Live parity and shadow progression

After historical ablation:

1. rebuild the same features from accepted first-party live Liquid20 data;
2. compare historical-provider and first-party-live distributions by source and semantic era;
3. record signal-only hypothetical decisions;
4. verify feature parity, availability timing, stale-data rejection, and gap handling;
5. proceed to Freqtrade dry-run only through a separate reviewed work package.

No step in this architecture authorizes live capital.

## 20. Implementation sequence

### H0 — Source and provider preflight

Deliver:

- current official exchange API verification;
- provider coverage, schema, timestamp, license, incident, and cost matrix;
- free-sample inspection where available;
- exact candidate symbols and dates;
- owner decision points for any paid access.

No bulk download and no model execution.

### H1 — Provider-neutral contracts

Deliver:

- historical event/envelope contracts;
- import manifest and acceptance schemas;
- semantic-era registry;
- provider interface;
- deterministic IDs and decimal normalization;
- focused synthetic tests.

No network access required.

### H2 — Tardis sample importer

Deliver:

- sample downloader or local-file importer;
- Tardis parser;
- raw hash manifest;
- normalization and rejection summaries;
- sample acceptance evidence.

A paid credential remains optional and secret-backed. No bulk purchase is authorized by code.

### H3 — Bulk immutable backfill

Requires owner confirmation of provider access and license.

Deliver:

- bounded exact-date download request;
- Synology exact-SHA image execution;
- immutable raw files and hashes;
- historical acceptance and quarantine reports;
- explicit evidence collection.

No training in the same work package.

### H4 — Feature dataset

Deliver:

- deterministic temporal join;
- atomic 5-minute partitions;
- derived 15-minute partitions;
- quality masks;
- no-lookahead tests;
- frozen dataset manifest.

### H5 — LightGBM ablation declaration and execution

Use the established declaration, inert infrastructure, exact-one-file request, evidence, and interpretation
pattern. The execution PR must not contain code or contract changes.

### H6 — Optional confirmation and RL

Proceed only after interpreting H5 evidence. XGBoost confirmation and RL observation experiments are separate
prospectively declared tasks.

### H7 — OKX shadow source

OKX is the first planned live source expansion, but it must not be coupled to historical backfill or first model
training. It receives an isolated adapter, staging policy, acceptance run, feature namespace, and ablation.

## 21. Success criteria

The architecture track succeeds when:

- historical raw data is immutable and traceable to provider files;
- semantic eras are explicit;
- accepted and quarantined intervals are deterministic;
- no-lookahead tests prove availability-time alignment;
- 5-minute and 15-minute feature datasets reproduce exactly;
- the first LightGBM ablation compares identical geometry and parameters;
- results are interpreted without promotion claims;
- live collector, portal, Phase 6, PyTorch, RL-v2, and protected holdout boundaries remain unchanged.

Profitability is not an architecture acceptance criterion.

## 22. Stop conditions

Stop and record a blocker when:

- provider coverage or licensing is insufficient;
- timestamps cannot support a defensible availability-time contract;
- data require silently mixing incompatible semantic eras;
- raw evidence cannot be retained immutably;
- the requested window overlaps the protected final holdout;
- a source acceptance report is missing or failed and no explicit quality-mask experiment was declared;
- implementation would require changing Phase 6, current RL-v2 evidence, or live trading behavior;
- paid access, credentials, or a material storage cost require owner approval.

## 23. External references for preflight

These links are inputs to the preflight, not frozen evidence. The implementation task must verify them again at
execution time.

- Bybit all-liquidation WebSocket:
  `https://bybit-exchange.github.io/docs/v5/websocket/public/all-liquidation`
- Bybit V5 changelog:
  `https://bybit-exchange.github.io/docs/changelog/v5`
- Binance developer documentation:
  `https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/Introduction`
- OKX API documentation and changelog:
  `https://www.okx.com/docs-v5/`
  `https://www.okx.com/docs-v5/log_en/`
- BitMEX liquidation endpoint:
  `https://docs.bitmex.com/api-explorer/get-liquidation`
- Tardis normalized liquidation schema:
  `https://docs.tardis.dev/downloadable-csv-data-types`
- Tardis Binance futures coverage:
  `https://docs.tardis.dev/historical-data-details/binance-futures`
- Tardis Bybit coverage:
  `https://docs.tardis.dev/historical-data-details/bybit`
- CoinGlass pair liquidation history:
  `https://docs.coinglass.com/reference/liquidation-history`
