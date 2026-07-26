# Liquidations Portal Module and AI Bot Architecture

## 1. Purpose and authority

This is the canonical continuation route for work involving:

- the Liquid20 public liquidation collectors;
- the read-only **Likwidacje** portal module;
- the Wick Hunter-inspired liquidation-reversal research track;
- a future liquidation-aware AI bot;
- later dry-run, shadow, and separately authorized live-small execution.

It prevents future agents from treating these as one component or from assuming that a working market-data page is a validated trading strategy.

Source-of-truth order:

1. current repository state and `develop` head;
2. merged pull requests and required CI;
3. immutable Liquid20 run evidence and acceptance reports;
4. current deployment evidence;
5. durable task checkpoints;
6. this document;
7. chat history and old prompts.

When sources conflict, stop and resolve the conflict from the higher-authority source. Do not silently choose the most convenient statement.

## 2. Current verified snapshot

Snapshot date: `2026-07-26`.

### 2.1 Portal integration

The read-only portal integration is complete in three bounded packages:

| Package | PR | Merge SHA | Delivered |
|---|---:|---|---|
| Liquid20 read-model | `#307` | `aa2f193b970588e478b5d57f58d2ddfd7f4aab67` | versioned contracts, bounded incremental NDJSON reader, exact decimal aggregation, health and acceptance semantics, deterministic tests |
| BFF and UI | `#311` | `228b5ad3eb12c6adab300ab86461d3fa67acaa47` | same-origin routes, responsive `/market/liquidations`, filters, summaries, rankings, source semantics, E2E |
| Synology integration | `#313` | `1bf106fb5919706cca4db4f8245e00d2a1932df9` | read-only evidence mount, non-root access through a verified supplementary group, exact-SHA candidate validation, rollback and LAN probes |

Real-data deployment evidence:

- feature candidate SHA: `e48c421aea4adb46854578264d80622803498a87`;
- feature deployment run: `30191045808`;
- authoritative merged deployment run: `30191687921`;
- private-LAN URL at that checkpoint: `http://192.168.1.2:3031`.

The current running image, collector image, active run and newest acceptance result are mutable runtime facts. Reverify them before every operational task.

### 2.2 Collector and research foundation

The supporting sequence includes:

| PR | Purpose |
|---:|---|
| `#236` | canonical liquidation event, Bybit parser/collector, completed-candle helper, pure counter-trade policy, disabled research profile |
| `#247` | measurable data-only staging and frozen acceptance policy |
| `#250` | Binance USD-M source with explicit sampled-feed semantics |
| `#254` | frozen `liquid20-v1` universe of 20 USDT perpetual symbols |
| `#256` | deterministic 24-hour multi-source acceptance package |
| `#258` | hardened Synology collector deployment project |

These packages establish collection and evidence contracts. They do not establish profitability, model validity or trading authorization.

### 2.3 Truthful current claim

The portal can display real, source-labelled liquidation evidence from Synology as a research preview.

The portal does not prove:

- that the newest data set passed the frozen acceptance policy;
- that a liquidation observation creates a trade signal;
- that the Wick Hunter-inspired strategy is profitable;
- that an AI model has been validated for liquidation data;
- that TP, SL, DCA or leverage has been selected;
- that any order submission or live capital is enabled.

An earlier completed run failed only `binance-usdm.maximum_latency_over_threshold_ratio`. A later run is accepted only when its own final report explicitly contains `passed: true`.

## 3. Component definitions

### 3.1 Liquid20 collector

A public-market-data process that:

- subscribes to fixed Bybit linear and Binance USD-M liquidation feeds;
- normalizes events into the canonical schema;
- writes source-separated append-only NDJSON;
- writes source summaries, a multi-source manifest and acceptance evidence;
- has no exchange trading keys;
- has no order, account or capital authority.

### 3.2 Liquid20 evidence

The immutable or append-only run directory containing normalized events and evidence metadata. It is the source of truth for portal presentation and future research dataset selection.

### 3.3 Portal Liquidations module

A server-side read-model, same-origin BFF and browser page that present bounded market-data observations. It is not a strategy and cannot create a signal, intent or order.

### 3.4 Wick Hunter-inspired research track

A separate, independently implemented hypothesis with the proposed shape:

```text
trusted liquidation event
AND event notional >= declared minimum
AND price is outside a declared VWAP or VWMA band
AND deterministic filters pass
=> counter-trade candidate
```

It is inspired only by publicly described behavior. It does not claim third-party source-code compatibility or exact product reproduction.

### 3.5 AI bot

A portal-managed `BotInstance` with immutable configuration, strategy, model, feature-schema and risk-policy identities.

An AI model may produce a prediction or ranking. Only deterministic strategy and risk layers may convert that output into an approved intent. Freqtrade owns the order and trade lifecycle.

## 4. Architecture overview

### 4.1 Current read-only path

```text
Bybit public liquidation feed      Binance USD-M forceOrder feed
                |                               |
                +---------------+---------------+
                                |
                                v
                     Liquid20 collector
                     - public endpoints only
                     - source-specific adapters
                     - canonical event schema
                                |
                                v
                append-only / immutable run evidence
                - source NDJSON
                - source summaries
                - multi-source manifest
                - final acceptance report when available
                                |
                     Synology read-only bind mount
                                |
                                v
                    Next.js server read-model
                    - fixed-path discovery
                    - incremental reads
                    - bounded cache
                    - exact aggregation
                                |
                                v
                     same-origin portal BFF
                                |
                                v
                    browser Likwidacje page
```

### 4.2 Future strategy path

```text
accepted and frozen Liquid20 evidence
              +
versioned candle evidence
              |
              v
deterministic event/candle replay
              |
              v
versioned feature builder
              |
              +-----------------------------+
              |                             |
              v                             v
deterministic baseline              optional AI prediction
              |                             |
              +--------------+--------------+
                             |
                             v
                   deterministic strategy
                             |
                             v
                    deterministic risk gate
                             |
                             v
                 approved dry-run intent only
                             |
                             v
                   private ExecutionAdapter
                             |
                             v
                  isolated Freqtrade runtime
```

No browser, collector, research worker or model may bypass the risk and execution boundaries.

## 5. Canonical data contract

### 5.1 Event fields

Every normalized event preserves:

```text
schema_version
source
source_event_id
symbol
liquidated_position_side
occurred_at_ms
received_at_ms
price
quantity
notional_usd
raw_side
```

Portal output additionally derives:

```text
ingest_latency_ms = received_at_ms - occurred_at_ms
```

### 5.2 Invariants

- `liquidated_position_side` describes the position that was liquidated, not the exchange order-side token.
- `price`, `quantity` and `notional_usd` remain decimal strings or exact decimal values.
- `source` is part of event identity and attribution.
- Cross-exchange observations are never silently deduplicated.
- Malformed records are rejected, not repaired with invented values.
- Missing intervals remain explicit gaps.
- Source or clock failure never becomes a healthy zero.

### 5.3 Source semantics

Bybit and Binance are not interchangeable feeds.

- Bybit linear `allLiquidation` is handled as the venue's published liquidation event stream.
- Binance USD-M `forceOrder` publishes the latest liquidation order for a symbol within an approximately 1000 ms window.

Consequences:

- totals retain source labels;
- Binance counts and notional are not proof of complete venue liquidation volume;
- similar events on different exchanges remain separate venue observations;
- models receive source identity or source-specific features;
- no unlabeled merged total is treated as a canonical volume measure.

## 6. Evidence layout and selection

### 6.1 Synology paths

Authoritative host root at the verified checkpoint:

```text
/volume1/docker/freqtrade-liquidations/data
```

Portal container root:

```text
/liquid20-data:ro
```

Supported discovery roots are the configured root itself or its fixed `runs/` child.

Valid run IDs match:

```text
liquid20-YYYYMMDDTHHMMSSZ-attempt
```

Fixed run children:

```text
bybit-linear.ndjson
binance-usdm.ndjson
bybit-linear-summary.json
binance-usdm-summary.json
multi-source-manifest.json
multi-source-acceptance-report.json   # only when final evaluation exists
```

No user-controlled request may select a host path, run path or filename.

### 6.2 Dataset selection rule

Before performance research, create a separate immutable dataset-selection record containing:

- run IDs and file hashes;
- collector, parser and evaluator commits;
- final acceptance status and failed gates;
- accepted, rejected and quarantined intervals;
- source clock and latency evidence;
- candle source, version and hashes;
- declared train, tune, validation and OOS windows;
- protected-holdout exclusion evidence;
- data-use classification.

A failed run may be used for diagnostics only when it remains labelled failed or quarantined. It cannot support a profitability claim.

## 7. Read-model architecture

Implementation root:

```text
ai_platform/portal/web/lib/liquidations/
```

The reader:

- discovers only fixed, valid, non-symlinked run directories;
- rejects paths that escape the configured root;
- reads fixed source files only;
- reads incrementally from remembered offsets;
- tolerates a partially written final line;
- detects inode change, file replacement, truncation and run rotation;
- removes stale source-cache entries after replacement;
- validates every event against its expected source;
- deduplicates only `source + source_event_id`;
- rejects conflicting records with the same identity;
- keeps a bounded in-memory cache;
- reports cache truncation explicitly;
- sorts deterministically by event time, source and source event ID;
- paginates with a stable cursor;
- bounds request, metadata and line sizes;
- never writes to the evidence tree.

Current default bounds:

```text
maximum cached events: 250000
stale threshold:       5 minutes
maximum query limit:   200
maximum metadata file: 2 MiB
maximum NDJSON line:   128 KiB
```

Any change must evaluate Synology memory, request latency, active-run growth and truncation semantics.

## 8. Portal contracts and UI

### 8.1 Endpoints

```text
GET /api/market/liquidations
GET /api/market/liquidations/summary
GET /api/market/liquidations/health
```

List parameters:

```text
source = all | bybit-linear | binance-usdm
symbol
side = long | short
since = non-negative epoch milliseconds
until = non-negative epoch milliseconds
limit = 1..200
cursor
```

The summary endpoint returns exact, source-labelled 5-minute, 1-hour and 24-hour aggregates, long/short split and 24-hour symbol ranking.

The health endpoint returns:

- selected run and data mode;
- current acceptance status and failed gates;
- latest completed acceptance evidence;
- active sources and observed-symbol count;
- source event, availability, disconnect and freshness fields;
- source-semantics descriptions;
- `research_preview: true`;
- `trading_authorized: false`.

### 8.2 Status semantics

Data mode:

- `live`: unfinished run with fresh source activity;
- `stale`: unfinished run beyond the freshness threshold;
- `historical`: run with a final acceptance report.

Acceptance status:

- `accepted`: current final report explicitly contains `passed: true`;
- `failed`: current final report explicitly contains `passed: false`;
- `in-progress`: current run has no final report;
- `missing`: no accepted final report can be derived for the current historical context.

The latest completed acceptance result remains visible while a newer run is active. An unfinished retry must not hide the last known failed gate.

### 8.3 BFF behavior

The BFF:

- runs in the Node.js server runtime;
- creates the reader only from server configuration;
- requires `PORTAL_LIQUIDATIONS_DATA_ROOT` outside explicit fixture mode;
- validates every parameter;
- returns `422` for invalid input;
- returns `503` when data is unavailable;
- returns a bounded `500` for unexpected failures;
- sets `cache-control: no-store`;
- never returns host paths, Docker metadata, credentials or unrestricted logs.

### 8.4 Browser page

Current page:

```text
/market/liquidations
```

It includes:

- data and acceptance status;
- failed gate names;
- 5-minute, 1-hour and 24-hour summaries;
- source, symbol, side and time filters;
- recent events;
- 24-hour symbol ranking;
- long/short split;
- source-semantics explanation;
- loading, empty, stale, unavailable, failed and responsive states;
- explicit research-preview and no-trading language.

It contains no buy, sell, long, short, order, DCA or leverage action.

## 9. Synology deployment boundary

### 9.1 Runtime topology

```text
Synology Container Manager / Docker daemon
  |
  +-- Liquid20 collector container
  |     writes /volume1/docker/freqtrade-liquidations/data
  |
  +-- portal candidate/final container
        reads /liquid20-data:ro
        binds to the verified private-LAN interface and port
```

### 9.2 Permission model

Observed evidence permissions:

```text
directories: root:root 750
files:       root:root 640
```

The deployment does not solve access by:

- running the portal as root;
- changing ownership or modes;
- copying evidence;
- adding evidence write access;
- mounting the Docker socket.

A short root-only metadata preflight verifies:

- valid non-symlinked run paths;
- fixed required files;
- group read and traverse bits;
- one consistent numeric GID.

The final non-root Node container receives only that supplementary group. The evidence bind remains read-only.

### 9.3 Deployment gates

Candidate validation checks:

- immutable image and exact commit identity;
- Docker health;
- health, summary, bounded list and page endpoints;
- `schema_version=1`;
- `research_preview=true`;
- `trading_authorized=false`;
- non-root UID;
- expected supplementary GID;
- read-only evidence mount;
- absence of `/var/run/docker.sock`;
- private-LAN reachability;
- rollback viability.

The private-LAN preview is not proof of Cloudflare P11 production-like staging and is not a public production deployment.

## 10. Security and authority boundaries

### 10.1 Browser boundary

The browser may call only same-origin portal routes. It must never receive or connect to:

- Synology file paths;
- the collector process;
- Bybit or Binance WebSocket endpoints for this module;
- Freqtrade REST or WebSocket endpoints;
- exchange credentials;
- secret-store endpoints;
- Docker socket access;
- private observability credentials.

### 10.2 Collector boundary

The collector:

- uses public market-data endpoints only;
- rejects common trading credential environment variables;
- contains no order or account logic;
- cannot create a signal or intent;
- cannot mutate completed evidence.

### 10.3 Research boundary

A research worker may read approved evidence and create immutable artifacts. It cannot:

- read production exchange credentials;
- mutate completed evidence;
- relabel failed evidence as accepted;
- promote its own model;
- submit orders;
- use protected holdout data for iterative tuning.

### 10.4 Capital authority

```text
prediction or observation
    -> deterministic strategy
    -> deterministic risk policy
    -> approved or rejected intent
    -> private execution adapter
    -> Freqtrade
```

A liquidation event is evidence, not authorization. Model confidence is not capital authority.

## 11. AI bot architecture

### 11.1 Stable layer split

A future liquidation-aware AI bot preserves:

1. **Data layer** — records observations and availability time.
2. **Feature layer** — derives versioned reproducible features.
3. **Model layer** — emits prediction, score, regime or ranking.
4. **Strategy layer** — deterministically interprets market context and optional model output.
5. **Risk layer** — approves, rejects or resizes under a versioned policy.
6. **Execution layer** — submits only approved dry-run or separately authorized intents.
7. **Post-trade layer** — records fills and outcomes without rewriting decision evidence.
8. **Learning layer** — creates candidates but cannot replace the active model silently.

### 11.2 Immutable attribution

Every decision must identify at least:

```text
tenant_id
bot_id
runtime_id
bot_config_revision_id
strategy_version_id
model_version_id or explicit no-model baseline
feature_schema_version
risk_policy_version_id
dataset_id or evidence manifest
collector commit
candle source and hashes
decision_id
correlation_id
```

Display names are not identities.

### 11.3 Bot and runtime isolation

Initial isolation remains:

```text
one BotInstance -> one isolated Freqtrade runtime
```

A `BotConfigRevision` is immutable. Changes to symbols, timeframes, thresholds, model assignment, risk limits, DCA, exits, leverage or data-source policy create a new revision.

Desired lifecycle state and observed runtime state remain separate.

### 11.4 Decision black box

Before execution outcome is known, persist a versioned decision snapshot containing only information available at decision time:

```text
decision_id
decision_available_at
bot, config, strategy, model and risk identities
market and liquidation evidence references
feature schema and feature artifact hash
model output and acceptance state
strategy result and reason codes
risk result and reason codes
proposed exposure
```

Later fills, fees, PNL, MFE, MAE, exit reason and diagnosis belong to separate outcome evidence.

### 11.5 AI is optional

The first valid candidate should have a deterministic non-AI baseline.

Add AI only for a declared question, for example:

- filter false reversals;
- estimate rebound probability;
- classify regime;
- rank candidate events;
- propose bounded holding-time or exit classes.

Compare AI against the same deterministic baseline using the same frozen evidence, fees, slippage, latency and execution assumptions. Data availability alone does not justify a complex model.

## 12. Deterministic event and candle synchronization

### 12.1 Required timestamps

For every event preserve:

```text
occurred_at_ms  # source event time
received_at_ms  # collector availability time
```

For every candle preserve source, timeframe, open time, close boundary and artifact identity.

### 12.2 Availability rule

A historical decision cannot occur before `received_at_ms`.

`occurred_at_ms` locates the event in market time but does not prove that the bot had received it at that time.

### 12.3 Completed-candle rule

For an event inside candle interval `[open, close)`:

- the containing candle may be linked as evidence;
- features may use only candles fully closed before event availability;
- final high, low, close or volume of the containing candle is forbidden unless a separately recorded intrabar stream proves the exact state available then.

The conservative current helper uses the last completed candle and decision availability from `received_at_ms`.

### 12.4 Replay contract to freeze prospectively

Before implementation, declare:

- primary event ordering key;
- tie-breakers for equal timestamps;
- handling of later-received but earlier-occurred events;
- maximum event age;
- duplicate and conflicting-ID behavior;
- missing-candle and missing-event behavior;
- source outage and quarantine behavior;
- exact entry-price sampling after decision availability;
- fees, slippage and latency model;
- train, tune, validation and OOS windows.

Do not choose these rules after observing strategy results.

### 12.5 No-lookahead proofs

Tests must prove that changing future values cannot alter an earlier decision:

- containing-candle final OHLCV;
- later liquidation events;
- later acceptance metadata;
- future labels;
- later outcomes or PNL;
- later source summaries.

## 13. Feature architecture

### 13.1 Candidate feature families

Potential features include:

- source-specific event count by rolling window;
- source-specific notional by rolling window;
- long/short liquidation imbalance;
- event size relative to recent source distribution;
- time since latest event;
- source availability and latency state;
- price distance from completed-candle VWAP or VWMA bands;
- completed-candle volatility and volume context;
- cross-source agreement with separate identities retained;
- cluster or burst descriptors.

These are candidate families, not approved features.

### 13.2 Feature schema requirements

Every feature schema states:

```text
name and version
input sources
availability timestamp rule
window boundaries
missing-data policy
source-outage policy
normalization or calibration window
numeric precision
warm-up requirement
training and inference equivalence test
```

Missing or stale source data must not silently become zero unless zero is the prospectively frozen semantic value.

### 13.3 Cross-source rules

Allowed:

- source-specific channels;
- explicitly labelled aggregate features;
- agreement and disagreement features;
- source-health inputs.

Forbidden:

- unlabeled summation;
- cross-source deduplication based only on approximate time and price;
- treating Binance sampled semantics as complete volume;
- training on fields unavailable at inference time.

## 14. Strategy architecture

### 14.1 Deterministic baseline

The baseline remains a pure testable decision function with explicit inputs:

```text
liquidation event
source health and age
allowed symbol, source and direction policy
minimum notional
completed-candle band values
optional declared volume or volatility filters
current position and cooldown state
```

Output:

```text
candidate action or IGNORE
reason codes
input evidence references
```

### 14.2 Separate policy packages

Declare and validate separately:

- entry and filter policy;
- position sizing;
- stop-loss;
- take-profit;
- time exit;
- trailing exit;
- cooldown and re-entry;
- DCA;
- leverage;
- portfolio and cross-bot limits.

Each changes the hypothesis and risk surface.

### 14.3 DCA

DCA remains disabled until a separate package defines:

- maximum additional entries;
- spacing rule;
- total exposure cap;
- margin and liquidation-distance stress tests;
- stop behavior after the final entry;
- correlated multi-symbol exposure;
- kill-switch behavior.

DCA must not hide a poor initial entry.

### 14.4 Exits and leverage

TP, SL, trailing, holding time and leverage are frozen before the evaluated window is read.

Leverage does not create edge. It increases liquidation, gap and operational risk.

## 15. Model lifecycle and evidence

Lifecycle:

```text
experiment
  -> candidate
  -> validated
  -> dry-run
  -> shadow
  -> live-small (owner-gated)
  -> production (separate authorization)
  -> retired
```

Training success does not equal promotion.

Minimum candidate evidence:

- exact code and artifact hash;
- frozen dataset manifest;
- feature schema version;
- target definition;
- train, tune, validation and OOS windows;
- fees, slippage, latency and entry rule;
- deterministic baseline comparison;
- deterministic repetition or declared seed policy;
- minimum event and trade count;
- drawdown and tail-risk gates;
- source-gap and latency stress;
- no-lookahead proofs;
- preserved negative results.

The protected final holdout remains isolated under current research policy. A period used for tuning or diagnosis cannot later be relabelled strict OOS.

## 16. Execution integration

### 16.1 Current state

The Liquidations portal module has no execution integration.

The general portal execution path remains fail-closed where private approved-intent submission is not implemented. Simulator evidence is not proof of real private Freqtrade submission.

### 16.2 First allowed execution stage

The first execution package remains:

```text
Freqtrade dry_run: true
DCA: disabled
no leverage or prospectively fixed bounded leverage
strict position and loss limits
new-entry kill switch
audit and decision snapshots enabled
credentials without withdrawal permission when credentials are required
```

It must respect portal credential-broker and approved-intent dependency order. No liquidation strategy may bypass PI-07 or PI-08 boundaries.

### 16.3 Shadow and live-small

Shadow mode compares hypothetical decisions and fills without capital.

Live-small requires a separate owner-approved package containing:

- exact capital cap;
- per-trade and total exposure;
- daily loss and drawdown stops;
- credentials with withdrawals disabled;
- alerts and operator runbook;
- rollback and kill-switch tests;
- approved strategy, model, risk and config identities;
- evidence that dry-run and shadow gates passed.

Nothing in this document authorizes live capital.

## 17. Observability and audit

### 17.1 Collector metrics

Track per source:

- connection intervals and availability;
- messages and events;
- parse failures;
- duplicates and conflicts;
- reconnects and disconnects;
- event latency distribution;
- latest message and event age;
- clock-probe state;
- storage growth;
- observed symbol coverage.

### 17.2 Read-model metrics

Track:

- refresh duration and failures;
- selected run ID;
- bytes and lines consumed per source;
- cache size and truncation;
- rejected records;
- run rotation and file replacement;
- endpoint rate, latency and status;
- stale and unavailable transitions.

### 17.3 Strategy and model metrics

Track with immutable attribution:

- observed events;
- accepted and rejected signals by reason;
- feature warm-up and missing-source rejects;
- prediction availability and rejection;
- strategy and risk decisions;
- intended and executed entries;
- event-receipt to decision and intent latency;
- fills, slippage, fees, MFE, MAE, exits and PNL;
- replay, signal-only, dry-run and shadow divergence.

### 17.4 Audit rules

Audit and operational logs remain separate.

Never log:

- exchange secrets;
- Freqtrade control credentials;
- session tokens;
- private keys;
- unrestricted sensitive request bodies.

## 18. Failure behavior

Fail closed or degrade explicitly for:

- missing data root;
- no valid run;
- symlink or path escape;
- unreadable files;
- malformed or oversized metadata;
- oversized NDJSON lines;
- invalid event schema;
- source mismatch;
- conflicting event identity;
- cache truncation;
- stale unfinished run;
- missing acceptance report;
- source clock failure;
- collector gap;
- unavailable candle evidence;
- feature warm-up failure;
- model artifact or hash mismatch;
- unavailable risk source;
- unavailable execution adapter.

Never convert an unavailable state into a healthy empty result or a trading signal.

## 19. Test architecture

### 19.1 Collector and parser

- valid Bybit and Binance messages;
- side normalization;
- exact decimal precision;
- deterministic IDs;
- malformed rows;
- reconnect and duplicate accounting;
- clock and latency evidence;
- credential-environment refusal;
- append-only output and immutable hashes.

### 19.2 Read-model

- fixed-path and symlink rejection;
- partial final line;
- malformed and conflicting records;
- incremental offsets;
- replacement and truncation;
- run rotation;
- source, symbol, side and time filtering;
- bounded limits and cursor validation;
- deterministic ordering;
- exact aggregation;
- no cross-source deduplication;
- cache truncation;
- live, stale, historical and acceptance states;
- read-only evidence access.

### 19.3 BFF and UI

- `422`, `503` and safe `500` responses;
- no-store headers;
- loading, empty, stale, failed and unavailable states;
- filters and pagination;
- source warning and failed gates;
- responsive 390 px viewport;
- no trading action;
- no direct collector, exchange or Freqtrade request;
- fixture data explicitly labelled.

### 19.4 Replay and strategy

Before promotion add:

- event and candle alignment;
- no-lookahead mutation tests;
- deterministic repeated replay;
- receive-time delayed decision;
- duplicate and out-of-order events;
- source outage and quarantine;
- fees, slippage and delayed-entry stress;
- rejected-signal reason reconciliation;
- deterministic baseline versus AI comparison;
- risk and kill-switch behavior.

### 19.5 Deployment

- exact image SHA;
- non-root UID;
- required supplementary GID only;
- read-only evidence mount;
- no Docker socket;
- no exchange credentials;
- internal API and page probes;
- private-LAN probes;
- rollback.

## 20. Dependency-ordered expansion plan

Use separate dated tasks and small reversible PRs.

### LQ-01 — Documentation and state closure

Delivered by the architecture task:

- canonical human-readable architecture;
- machine-readable versioned manifest;
- repaired stale checkpoints;
- portal documentation and ADR routing.

### LQ-02 — Accepted dataset selection

Entry gate:

- completed run explicitly passes the unchanged policy, or failed evidence is selected only for diagnostics.

Deliverables:

- immutable file hashes;
- collector and parser commits;
- accepted and quarantined intervals;
- candle source and hashes;
- data-use classification;
- holdout-contamination check.

### LQ-03 — Deterministic replay contract and engine

- freeze ordering, alignment, price sampling, fees, slippage, latency, gaps and windows;
- implement deterministic replay and evidence package;
- add no-lookahead and repeatability tests.

### LQ-04 — Deterministic strategy baseline

- freeze entry and filter policy;
- keep DCA, leverage optimization and adaptive exits out;
- compare with no-trade and declared conventional baselines;
- preserve negative results.

### LQ-05 — Signal-only live observation

- run collector plus signal engine;
- persist decisions and rejects;
- submit no orders;
- compare live timing with replay semantics.

### LQ-06 — Optional AI experiment

- declare one model question;
- freeze features, target, windows and baseline;
- train candidates only;
- use independent lifecycle promotion.

This package is optional and must not block a valid deterministic baseline.

### LQ-07 — Freqtrade dry-run integration

Dependencies:

- accepted replay and signal-only evidence;
- required credential and execution contracts;
- approved immutable strategy, model, risk and config versions.

Boundaries:

- dry-run only;
- no DCA first;
- strict position and loss limits;
- kill switch and audit.

### LQ-08 — Shadow review

- compare intended decisions, simulated fills and real market outcomes;
- measure latency, slippage, divergence and operational stability;
- no capital.

### LQ-09 — Live-small authorization package

Owner-gated and separate. Completion of previous packages does not authorize it automatically.

## 21. Agent start protocol

Before changing this area, a future agent must:

1. inspect current `develop`, open PRs, active branches and required checks;
2. read root `AGENTS.md` and `docs/agents/CONTEXT_HANDOFF.md`;
3. read this document, its JSON manifest and the latest task checkpoint;
4. inspect current collector and portal deployment evidence;
5. verify the newest completed acceptance report and active run;
6. identify exact owned paths and overlap with portal, research, deployment and bot-operation work;
7. declare one bounded task, branch, acceptance criteria and non-goals;
8. preserve source identity, immutable evidence, no-lookahead, risk, credential and capital gates;
9. use a PR and exact-current-head CI as the merge gate;
10. update durable checkpoints after every material state change.

## 22. Canonical file map

### Collector and research

```text
ai_platform/research/liquidations/
ai_platform/scripts/liquidation_collector.py
ai_platform/scripts/liquidation_staging_evaluator.py
docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
```

### Portal read-model and UI

```text
ai_platform/portal/web/lib/liquidations/
ai_platform/portal/web/app/api/market/liquidations/
ai_platform/portal/web/app/market/liquidations/
ai_platform/portal/web/components/liquidations-dashboard.tsx
ai_platform/portal/web/e2e/liquidation-read-model.spec.ts
ai_platform/portal/web/e2e/liquidations.spec.ts
docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
```

### Synology deployment

```text
deploy/synology/liquid20/
deploy/synology/portal/
.github/workflows/portal-synology-lan-preview.yml
```

### Architecture and governance

```text
docs/ai_platform/ARCHITECTURE.md
docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
docs/ai_platform/portal/AI_ML_AND_LEARNING_ARCHITECTURE.md
docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
docs/ai_platform/portal/liquidations-ai-bot-architecture-v1.json
```

## 23. Known facts, mutable facts and open decisions

### 23.1 Proven

- collector and multi-source acceptance contracts exist;
- portal read-model, BFF, UI and Synology read-only integration are merged;
- a non-root candidate read real Synology evidence successfully;
- the portal has no trading authority for liquidation data;
- the Wick Hunter-inspired foundation has a pure signal policy but no validated strategy;
- DCA, TP, SL, leverage, AI and execution remain separate work.

### 23.2 Must be reverified

- current `develop` head and path ownership;
- current portal image and deployment run;
- current collector image and state;
- newest run ID;
- newest final acceptance result;
- disk, memory and retention state;
- whether a replay dataset has been frozen;
- whether PI-07, PI-08 or related execution dependencies changed.

### 23.3 Unresolved decisions

These require prospective declarations:

- exact accepted dataset and candle source;
- replay ordering and entry-price rule;
- volume-filter definition;
- VWAP versus VWMA definition;
- exit and cooldown policy;
- position sizing and portfolio limits;
- DCA policy, if justified;
- leverage policy;
- whether AI adds measurable value;
- model target and validation gates;
- live-small capital and operator policy.

## 24. No-go conditions

Stop and record a blocker when work would:

- weaken or reinterpret the frozen acceptance policy after results are known;
- mutate completed evidence;
- expose files, collector, Freqtrade, Docker or credentials to the browser;
- remove source identity or deduplicate across exchanges;
- use unfinished-candle final values without intrabar evidence;
- use future outcome data in decision features;
- replace unavailable data with zero or healthy state silently;
- let a model bypass deterministic strategy or risk;
- enable DCA, leverage, order submission or live capital outside a separate package;
- use protected holdout data iteratively;
- mark a model promoted because training completed;
- bypass PR, review or CI gates.

## 25. Production-capable completion definition

A production-capable liquidation bot claim requires all of the following:

- accepted immutable source data;
- deterministic synchronization and replay;
- no-lookahead evidence;
- declared deterministic baseline;
- frozen features, target and model with independent validation;
- fees, slippage, latency, gaps and tail-risk stress;
- sufficient event and trade sample count;
- accepted dry-run and shadow operation;
- immutable strategy, model, config and risk attribution;
- private credential and execution boundaries;
- risk limits, kill switches, alerts and rollback;
- owner-approved live-small package;
- successful post-live review before broader promotion.

Until then, the correct product label is **read-only market-data and research preview**.
