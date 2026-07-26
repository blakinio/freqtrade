# Liquidations Portal Module and AI Bot Architecture

## 1. Purpose

This document is the canonical continuation route for work involving:

- the Liquid20 public liquidation collectors;
- the read-only **Likwidacje** portal module;
- the Wick Hunter-inspired liquidation-reversal research track;
- a future liquidation-aware AI bot;
- later dry-run, shadow, and separately authorized live-small execution.

It exists to prevent future agents from treating these as one component or from assuming that a working market-data page is a validated trading strategy.

Repository state, merged pull requests, immutable run evidence, current task checkpoints, and current deployment evidence override this document when they conflict. Chat history is not authoritative.

## 2. Current verified implementation snapshot

Snapshot date: `2026-07-26`.

### 2.1 Portal integration

The first complete read-only portal integration has been delivered in three bounded packages:

1. PR `#307`, merge `aa2f193b970588e478b5d57f58d2ddfd7f4aab67`:
   - versioned server-side Liquid20 read-model;
   - bounded incremental NDJSON reader;
   - exact decimal aggregation;
   - health and acceptance-state contracts;
   - deterministic fixtures and contract tests.
2. PR `#311`, merge `228b5ad3eb12c6adab300ab86461d3fa67acaa47`:
   - same-origin BFF routes;
   - responsive `/market/liquidations` page;
   - filters, summaries, rankings, source semantics, and E2E coverage.
3. PR `#313`, merge `1bf106fb5919706cca4db4f8245e00d2a1932df9`:
   - read-only Synology evidence mount;
   - non-root portal access through a verified supplementary read group;
   - exact-SHA candidate validation, rollback, and private-LAN probes.

The exact feature deployment `e48c421aea4adb46854578264d80622803498a87` passed Synology workflow run `30191045808` against real Liquid20 files before PR `#313` was merged.

### 2.2 Research and collection foundation

The supporting research/data sequence includes:

- PR `#236`: canonical liquidation event, Bybit parser/collector, completed-candle alignment, pure counter-trade policy, disabled profile;
- PR `#247`: measurable data-only staging and a frozen acceptance policy;
- PR `#250`: Binance USD-M source with explicit sampled-feed semantics;
- PR `#254`: frozen `liquid20-v1` universe of 20 USDT perpetual symbols;
- PR `#256`: deterministic 24-hour multi-source acceptance package;
- PR `#258`: hardened Synology collector deployment project.

These packages establish data collection and evidence contracts. They do not establish strategy profitability or trading authorization.

### 2.3 Truthful current claim

The portal can display real source-labelled liquidation evidence from Synology as a research preview.

The following claims are not authorized merely because the page works:

- that the data set passed the frozen acceptance policy;
- that liquidation observations create trade signals;
- that the Wick Hunter-inspired strategy is profitable;
- that an AI model has been validated for this data;
- that any order submission, DCA, leverage, or live capital is enabled.

The most recent completed acceptance result and the current active-run state must always be re-read from the evidence tree. An earlier completed run failed only `binance-usdm.maximum_latency_over_threshold_ratio`; a later retry must not be assumed accepted without an explicit report containing `passed: true`.

## 3. Terminology and ownership

### 3.1 Liquid20 collector

A public-market-data process that:

- subscribes to fixed Bybit linear and Binance USD-M liquidation feeds;
- normalizes events into the canonical schema;
- writes source-separated append-only NDJSON;
- writes source summaries, a multi-source manifest, and acceptance evidence;
- has no exchange trading keys and no execution authority.

### 3.2 Liquid20 evidence

The immutable or append-only run directory containing raw normalized events and evidence metadata. It is the source of truth for the portal module and future research dataset selection.

### 3.3 Portal Liquidations module

A server-side read-model, same-origin BFF, and browser page that present bounded market-data observations. It is not a strategy and cannot submit intents or orders.

### 3.4 Wick Hunter-inspired research strategy

A separate, independently implemented research track whose proposed entry shape is:

```text
trusted liquidation event
AND event notional >= declared minimum
AND price is outside a declared VWAP or VWMA band
AND deterministic filters pass
=> create a counter-trade candidate
```

It is inspired only by publicly described behavior. It does not claim source-code compatibility with, or reproduction of, a third-party product.

### 3.5 AI bot

A portal-managed `BotInstance` with immutable configuration, strategy, model, feature-schema, and risk-policy identities. An AI model may produce predictions, but only deterministic strategy and risk layers may convert them into an approved execution intent. Freqtrade owns the order and trade lifecycle.

## 4. System context

### 4.1 Current read-only data path

```text
Bybit linear public feed          Binance USD-M public feed
             |                               |
             +---------------+---------------+
                             |
                             v
                  Liquid20 collector process
                  - no trading credentials
                  - source-specific adapters
                  - canonical event schema
                             |
                             v
             append-only / immutable run evidence
             - source NDJSON
             - source summaries
             - multi-source manifest
             - acceptance report when completed
                             |
                  read-only Synology bind mount
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
             +-------------------------+
             |                         |
             v                         v
deterministic baseline          optional AI prediction
             |                         |
             +------------+------------+
                          |
                          v
                deterministic strategy
                          |
                          v
                 deterministic risk gate
                          |
                          v
            approved intent in dry-run only
                          |
                          v
               private ExecutionAdapter
                          |
                          v
               isolated Freqtrade runtime
```

No component may shortcut the risk gate or call an exchange directly from the browser, research worker, or model.

## 5. Current component architecture

### 5.1 Source adapters and canonical event

The canonical event preserves:

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

Important invariants:

- `liquidated_position_side` describes the position that was liquidated, not the exchange order-side token;
- `price`, `quantity`, and `notional_usd` remain decimal strings or exact decimal values;
- source identity is part of event identity;
- cross-exchange observations are never silently deduplicated;
- malformed records are rejected, not repaired with invented values;
- missing intervals remain gaps.

### 5.2 Source semantics

Bybit and Binance are not interchangeable feeds.

- Bybit linear `allLiquidation` is handled as the venue's published liquidation event stream.
- Binance USD-M `forceOrder` publishes the latest liquidation order for a symbol within an approximately 1000 ms window.

Consequences:

- totals must retain `source` labels;
- a Binance count or notional is not proof of complete venue liquidation volume;
- identical-looking events on two exchanges remain two venue observations;
- future models must receive source identity or source-specific features, not an unlabeled merged total.

### 5.3 Evidence layout

The authoritative Synology root is currently:

```text
/volume1/docker/freqtrade-liquidations/data
```

The portal container sees:

```text
/liquid20-data:ro
```

Supported run roots are either the configured root itself or its `runs/` child. Valid run IDs match:

```text
liquid20-YYYYMMDDTHHMMSSZ-attempt
```

Fixed children of a run include:

```text
bybit-linear.ndjson
binance-usdm.ndjson
bybit-linear-summary.json
binance-usdm-summary.json
multi-source-manifest.json
multi-source-acceptance-report.json   # when final evaluation exists
```

No browser parameter can select a host path, run path, or filename.

### 5.4 Read-model

Current implementation location:

```text
ai_platform/portal/web/lib/liquidations/
```

The reader:

- discovers only fixed, valid, non-symlinked run directories;
- rejects paths that escape the configured root;
- reads fixed source files only;
- reads incrementally from remembered offsets;
- tolerates a partially written final line;
- detects file replacement, inode change, truncation, and run rotation;
- removes stale source-cache entries after source replacement;
- validates every event against its expected source;
- deduplicates only `source + source_event_id`;
- rejects conflicting records with the same identity;
- keeps a bounded in-memory cache;
- reports truncation explicitly;
- sorts deterministically by event time, source, and source event ID;
- paginates with a stable cursor;
- limits one list request to 200 records;
- bounds metadata and line sizes;
- never writes to the evidence tree.

Default implementation bounds are currently:

```text
maximum cached events: 250000
stale threshold:       5 minutes
maximum query limit:   200
maximum metadata file: 2 MiB
maximum NDJSON line:   128 KiB
```

Any future change to these values must consider Synology memory, request latency, active-run growth, and explicit cache-truncation semantics.

### 5.5 Versioned portal contracts

List endpoint:

```text
GET /api/market/liquidations
```

Accepted query fields:

```text
source = all | bybit-linear | binance-usdm
symbol
side = long | short
since = non-negative epoch milliseconds
until = non-negative epoch milliseconds
limit = 1..200
cursor
```

Summary endpoint:

```text
GET /api/market/liquidations/summary
```

Returns:

- 5-minute, 1-hour, and 24-hour windows;
- total event count and exact notional;
- long/short split;
- source-specific totals;
- 24-hour symbol ranking;
- `truncated` when the read cache cannot represent the complete requested history.

Health endpoint:

```text
GET /api/market/liquidations/health
```

Returns:

- run ID and data mode;
- current acceptance status and failed gates;
- latest completed acceptance evidence;
- active sources and observed-symbol count;
- per-source event, availability, disconnect, and freshness fields;
- source-semantics descriptions;
- `research_preview: true`;
- `trading_authorized: false`.

### 5.6 Status semantics

Data mode:

- `live`: latest run has no final acceptance report and activity is fresh;
- `stale`: latest unfinished run exceeded the freshness threshold;
- `historical`: latest run has a final acceptance report.

Acceptance status:

- `accepted`: current run report explicitly contains `passed: true`;
- `failed`: current run report explicitly contains `passed: false`;
- `in-progress`: current run is live or stale and has no final report;
- `missing`: no accepted final report can be derived for the current historical context.

The latest completed acceptance result remains visible while a newer run is active. This prevents an unfinished retry from hiding the last known failed gate.

### 5.7 BFF and UI

Current server routes:

```text
ai_platform/portal/web/app/api/market/liquidations/
```

Current page:

```text
/market/liquidations
```

The BFF:

- runs in the Node.js server runtime;
- creates the reader only from server configuration;
- requires `PORTAL_LIQUIDATIONS_DATA_ROOT` outside explicit fixture mode;
- returns `422` for invalid query input;
- returns `503` when data is unavailable;
- returns a bounded `500` response for unexpected failures;
- sets `cache-control: no-store`;
- never returns the host path, Docker metadata, credentials, or raw unrestricted logs.

The UI includes:

- current data and acceptance status;
- failed gate names;
- 5-minute, 1-hour, and 24-hour summaries;
- source, symbol, side, and time filters;
- recent events;
- 24-hour symbol ranking;
- long/short split;
- source-semantics explanation;
- loading, empty, stale, unavailable, failed, and responsive states;
- explicit research-preview and no-trading language.

## 6. Synology deployment architecture

### 6.1 Runtime topology

```text
Synology Container Manager / Docker daemon
  |
  +-- liquid20 collector container
  |     writes /volume1/docker/freqtrade-liquidations/data
  |
  +-- portal candidate/final container
        reads the same root through /liquid20-data:ro
        binds only to 192.168.1.2:3031
```

### 6.2 Permission boundary

Observed evidence permissions were:

```text
directories: root:root 750
files:       root:root 640
```

The deployment does not solve this by:

- running the portal as root;
- changing ownership or modes;
- copying evidence;
- adding write access;
- mounting the Docker socket.

Instead, a short root-only metadata preflight container verifies:

- valid non-symlinked run paths;
- required fixed files;
- group read/traverse bits;
- one consistent numeric GID.

The final non-root Node container receives only that numeric supplementary group and the evidence bind remains read-only.

### 6.3 Deployment gates

The deployment builds an exact-commit image, starts an isolated candidate, and checks:

- Docker health;
- health, summary, bounded list, and page endpoints;
- `schema_version=1`;
- `research_preview=true`;
- `trading_authorized=false`;
- non-root UID;
- expected read group;
- read-only evidence mount;
- absence of `/var/run/docker.sock`;
- private-LAN reachability;
- rollback viability.

The private preview URL is currently:

```text
http://192.168.1.2:3031
```

This is not proof of Cloudflare P11 production-like staging and is not a public production deployment.

## 7. Security and authority boundaries

### 7.1 Browser boundary

The browser may call only same-origin portal routes. It must never receive or connect to:

- Synology file paths;
- the collector WebSocket/process;
- Bybit or Binance WebSocket endpoints for this module;
- Freqtrade REST or WebSocket endpoints;
- exchange credentials;
- a secret store;
- the Docker socket;
- an observability backend credential.

### 7.2 Collector boundary

The collector uses public market-data endpoints only. It must reject common trading credential environment variables and must not contain order or account code.

### 7.3 Research boundary

A research worker can read approved evidence and create immutable artifacts. It cannot:

- read production exchange credentials;
- alter completed evidence;
- relabel a failed run as accepted;
- promote its own model;
- submit orders;
- use protected holdout data for iterative tuning.

### 7.4 Capital authority

Capital authority remains outside the model and outside the portal market-data page.

```text
prediction or observation
    -> deterministic strategy
    -> deterministic risk policy
    -> approved or rejected intent
    -> private execution adapter
    -> Freqtrade
```

A liquidation event is evidence, not authorization.

## 8. AI bot architecture assumptions

### 8.1 Stable authority split

A future AI-enabled liquidation bot must preserve this split:

1. **Data layer** records what was observed and when it became available.
2. **Feature layer** derives only versioned, reproducible features from allowed information.
3. **Model layer** produces a prediction, score, regime, or desired-position proposal.
4. **Strategy layer** deterministically interprets model output and market context.
5. **Risk layer** approves, rejects, or resizes the candidate under a versioned policy.
6. **Execution layer** sends only approved dry-run or separately authorized intents to Freqtrade.
7. **Post-trade layer** records outcomes and diagnoses without rewriting decision-time evidence.
8. **Learning layer** may create candidates but cannot silently replace the active model.

### 8.2 Immutable identities

Every decision must be attributable to at least:

```text
tenant_id
bot_id
runtime_id
bot_config_revision_id
strategy_version_id
model_version_id or explicit no-model baseline
feature_schema_version
risk_policy_version_id
dataset_id / evidence manifest
collector commit
candle source and hashes
decision_id
correlation_id
```

Display names are not identities.

### 8.3 BotInstance and runtime

Initial isolation remains:

```text
one BotInstance -> one isolated Freqtrade runtime
```

A `BotConfigRevision` is immutable. Changing symbols, timeframes, thresholds, model assignment, risk limits, DCA, exits, leverage, or data-source policy creates a new revision.

Desired lifecycle state and observed runtime state remain separate.

### 8.4 Decision black box

Before execution outcome is known, persist a versioned decision snapshot containing only information available at decision time:

```text
decision_id
occurred_at / decision_available_at
bot/config/strategy/model/risk identities
market and liquidation evidence references
feature schema and feature artifact hash
model output and acceptance state
strategy result and reason codes
risk result and reason codes
proposed exposure
```

Later trade fills, PNL, MFE/MAE, exit reason, and post-trade diagnosis belong to separate outcome evidence.

### 8.5 AI is optional

The first valid strategy candidate should have a deterministic non-AI baseline. An AI component should be added only when it answers a declared question such as:

- filter false reversals;
- estimate rebound probability;
- classify market regime;
- rank candidate events;
- propose bounded holding-time or exit classes.

The AI model must be compared against the deterministic baseline using the same frozen evidence and execution assumptions. A complex model is not justified merely because data exists.

## 9. Deterministic event and candle synchronization contract

This contract is required before historical strategy claims.

### 9.1 Required timestamps

For every liquidation event preserve:

```text
occurred_at_ms  # source event time
received_at_ms  # local collector availability time
```

For every candle preserve a versioned source, timeframe, open time, close boundary, and artifact identity.

### 9.2 Availability rule

A historical decision cannot occur before `received_at_ms`.

The source occurrence timestamp may locate the event in market time, but it does not prove that the bot had received the event at that moment.

### 9.3 Completed-candle rule

For an event inside candle interval `[open, close)`:

- the containing candle may be recorded for evidence linkage;
- strategy features may use only candles that were fully closed before the event became available;
- the final high, low, close, or volume of the containing candle is forbidden unless a separately recorded intrabar stream proves the exact state available at decision time.

The conservative current helper uses the last completed candle and sets decision availability from `received_at_ms`.

### 9.4 Deterministic replay ordering

Before a replay package is implemented, prospectively freeze:

- the primary event ordering key;
- tie-breakers for equal timestamps;
- whether a later-received but earlier-occurred event can affect an already made decision;
- maximum event age;
- duplicate and conflicting-ID behavior;
- missing-candle and missing-event behavior;
- source outage and quarantine behavior;
- the exact entry-price sampling rule after decision availability.

Do not invent these rules after observing strategy results.

### 9.5 No-lookahead tests

Required tests must prove that changing future values cannot alter an earlier decision:

- containing-candle final OHLCV;
- later liquidation events;
- later acceptance metadata;
- future model labels;
- outcome or PNL fields;
- later source summaries.

## 10. Future feature architecture

### 10.1 Feature groups

Potential liquidation feature families include:

- source-specific event count by rolling window;
- source-specific notional by rolling window;
- long/short liquidation imbalance;
- event size relative to recent source distribution;
- time since latest event;
- source availability and latency state;
- price distance from completed-candle VWAP or VWMA bands;
- completed-candle volatility and volume context;
- cross-source agreement while retaining separate identities;
- cluster or burst descriptors.

These are candidate families, not approved features.

### 10.2 Feature contract requirements

Every feature schema must state:

```text
name and version
input sources
availability timestamp rule
window boundaries
missing-data policy
source-outage policy
normalization/calibration window
numeric precision
warm-up requirement
training/inference equivalence test
```

Missing or stale source data must not silently become zero unless zero is explicitly the frozen semantic value.

### 10.3 Cross-source policy

Allowed:

- source-specific channels;
- explicitly labelled aggregate features;
- agreement/disagreement features;
- source-health inputs.

Forbidden:

- unlabeled summation;
- cross-source event deduplication based only on approximate time/price;
- treating Binance sampled semantics as complete liquidation volume;
- training on a source field that is unavailable at inference time.

## 11. Strategy architecture

### 11.1 Deterministic baseline

The baseline should remain a pure, testable decision function with explicit inputs:

```text
liquidation event
source health and age
allowed symbol/source/direction policy
minimum notional
completed-candle band values
optional declared volume/volatility filters
current position and cooldown state
```

Output:

```text
candidate action or IGNORE
reason codes
input evidence references
```

### 11.2 Separate policy packages

Do not combine all behavior in one experiment. Declare separately:

- entry/filter policy;
- position sizing;
- stop-loss;
- take-profit;
- time exit;
- trailing exit;
- cooldown/re-entry;
- DCA;
- leverage;
- portfolio and cross-bot limits.

Each package changes the hypothesis and risk surface and requires its own frozen declaration and evidence.

### 11.3 DCA

DCA remains disabled until a separate package prospectively defines:

- maximum additional entries;
- spacing rule;
- total exposure cap;
- margin and liquidation-distance stress tests;
- stop behavior after the final DCA;
- correlated multi-symbol exposure;
- kill-switch behavior.

DCA must never be introduced merely to hide a poor initial entry.

### 11.4 Exits and leverage

TP, SL, trailing, holding-time, and leverage must be frozen before the evaluated window is read. Leverage does not create edge and materially increases liquidation and gap risk.

## 12. Model lifecycle

A future liquidation-aware model follows:

```text
experiment
  -> candidate
  -> validated
  -> dry-run
  -> shadow
  -> live-small (owner-gated)
  -> production (separate evidence and authorization)
  -> retired
```

Training success does not equal promotion.

Minimum candidate evidence:

- exact code and artifact hash;
- frozen dataset manifest;
- feature schema version;
- target definition;
- train/tune/OOS windows;
- fees, slippage, latency, and entry rule;
- deterministic baseline comparison;
- repeated-run determinism or declared seed policy;
- minimum sample/trade count;
- drawdown and tail-risk gates;
- source-gap stress;
- latency stress;
- no-lookahead tests;
- negative-result preservation.

The protected final holdout must remain isolated according to the current research policy. Earlier use of a period for tuning or diagnosis cannot later be relabelled as strict OOS.

## 13. Execution integration

### 13.1 Current state

The portal Liquidations module has no execution integration.

The general portal execution path remains fail-closed where private approved-intent submission is not implemented. Deterministic simulator evidence is not proof of private Freqtrade order submission.

### 13.2 First allowed execution stage

The first execution package must remain:

```text
Freqtrade dry_run: true
DCA: disabled
fixed bounded leverage or no leverage
strict exposure limits
new-entry kill switch
audit and decision snapshots enabled
separate credentials without withdrawal permission when credentials become required
```

It must respect the portal's credential-broker and approved-intent dependency order. A liquidation strategy must not create a side channel that bypasses PI-07 or PI-08 security contracts.

### 13.3 Shadow and live-small

Shadow mode compares hypothetical decisions and fills without capital.

Live-small requires a separate owner-approved package containing:

- exact capital cap;
- per-trade and total exposure;
- daily loss and drawdown stops;
- exchange credentials with withdrawals disabled;
- alerting and operator runbook;
- rollback and kill-switch tests;
- approved model/strategy/risk/config identities;
- evidence that dry-run and shadow gates passed.

Nothing in this document authorizes live capital.

## 14. Observability and audit

### 14.1 Collector metrics

Track per source:

- connection intervals and availability;
- message and event counts;
- parse failures;
- duplicates and conflicts;
- reconnects/disconnects;
- event latency distribution;
- latest message/event age;
- clock-probe state;
- storage growth;
- observed symbol coverage.

### 14.2 Read-model metrics

Track:

- refresh duration and failures;
- active run ID;
- bytes and lines consumed per source;
- cache size and truncation;
- rejected records;
- run rotation/file replacement;
- endpoint request rate, latency, and status;
- stale/unavailable transitions.

### 14.3 Strategy/model metrics

Track with immutable attribution:

- observed events;
- accepted/rejected signals by reason;
- feature warm-up and missing-source rejects;
- prediction availability and rejection;
- strategy and risk decisions;
- intended and executed entries;
- latency from event receipt to decision and intent;
- fills, slippage, fees, MFE/MAE, exits, and PNL;
- divergence between replay, signal-only, dry-run, and shadow.

### 14.4 Audit rules

Audit and operational logs are separate. Never log:

- exchange secrets;
- Freqtrade control credentials;
- session tokens;
- private keys;
- unrestricted raw request bodies containing sensitive data.

## 15. Failure behavior

Fail closed or degrade explicitly for:

- missing data root;
- no valid run directory;
- symlink/path escape;
- unreadable files;
- malformed metadata;
- oversized metadata or line;
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
- model artifact/hash mismatch;
- risk source unavailable;
- execution adapter unavailable.

Never convert an unavailable state into a healthy empty result or a trading signal.

## 16. Test architecture

### 16.1 Collector and parser

- valid Bybit and Binance messages;
- side normalization;
- decimal precision;
- deterministic IDs;
- malformed rows;
- reconnect and duplicate accounting;
- clock and latency evidence;
- credential-environment refusal;
- append-only output and immutable hashes.

### 16.2 Read-model

- fixed-path and symlink rejection;
- partial final line;
- malformed and conflicting records;
- incremental offsets;
- file replacement/truncation;
- run rotation;
- source/symbol/side/time filtering;
- bounded limit and cursor validation;
- deterministic ordering;
- exact aggregation;
- no cross-source deduplication;
- cache truncation;
- live/stale/historical and acceptance states;
- read-only file access.

### 16.3 BFF and UI

- 422, 503, and safe 500 responses;
- no-store headers;
- loading, empty, stale, failed, and unavailable states;
- filters and pagination;
- source warning and failed gates;
- responsive 390 px viewport;
- no trading action;
- no direct collector/Freqtrade/public data-plane request;
- fixture data clearly labelled.

### 16.4 Replay and strategy

Before strategy promotion add:

- event/candle alignment;
- no-lookahead mutation tests;
- deterministic repeated replay;
- receive-time delayed decision;
- duplicate/out-of-order events;
- source outage/quarantine;
- fees, slippage, and delayed-entry stress;
- rejected-signal reason reconciliation;
- baseline versus AI comparison;
- risk and kill-switch behavior.

### 16.5 Deployment

- exact image SHA;
- non-root UID;
- required supplementary GID only;
- read-only evidence mount;
- no Docker socket;
- no exchange credentials;
- internal page/API probes;
- LAN probes;
- rollback.

## 17. Dependency-ordered expansion plan

Future work should use separate dated tasks and small PRs.

### LQ-01 — Documentation and state closure

- keep this architecture document current;
- close stale task checkpoints;
- record exact merged PR/CI/deployment evidence;
- add portal delivery-status routing.

### LQ-02 — Accepted dataset selection

Entry gate:

- a completed run report explicitly passes the unchanged frozen policy, or a failed/quarantined result is selected only for non-performance diagnostics.

Deliverables:

- immutable run and file hashes;
- collector/parser commits;
- accepted and quarantined intervals;
- candle source and hashes;
- declared data-use classification;
- no protected-holdout contamination.

### LQ-03 — Deterministic replay contract and engine

- prospectively freeze ordering, alignment, price sampling, fees, slippage, latency, gaps, and split windows;
- implement deterministic replay and evidence package;
- add no-lookahead and repeatability tests.

### LQ-04 — Deterministic strategy baseline

- freeze entry and filter policy;
- keep DCA, leverage optimization, and adaptive exits out;
- compare against simple no-trade and declared conventional baselines;
- preserve negative results.

### LQ-05 — Signal-only live observation

- run collector plus signal engine;
- persist decisions and rejects;
- submit no orders;
- compare live timing with replay semantics.

### LQ-06 — Optional AI experiment

- declare a specific model question;
- freeze features, target, windows, and baseline;
- train candidates only;
- require independent lifecycle promotion.

This package is optional and must not block a valid deterministic baseline.

### LQ-07 — Freqtrade dry-run integration

Dependencies:

- accepted replay and signal-only evidence;
- portal credential/execution contracts where applicable;
- approved immutable strategy/model/risk/config versions.

Boundaries:

- dry-run only;
- no DCA first;
- strict position and loss limits;
- kill switch and audit.

### LQ-08 — Shadow review

- compare intended decisions, simulated fills, and real market outcomes;
- measure latency, slippage, divergence, and operational stability;
- no capital.

### LQ-09 — Live-small authorization package

Owner-gated and separate. It cannot be inferred from completion of any prior package.

## 18. Agent start protocol

Before changing this area, a future agent must:

1. inspect current `develop`, open PRs, active branches, and required checks;
2. read root `AGENTS.md` and `docs/agents/CONTEXT_HANDOFF.md`;
3. read this document and the latest active task checkpoint;
4. inspect current Liquid20 collector and portal deployment evidence;
5. verify the newest completed acceptance report and active run instead of trusting a status sentence;
6. identify exact owned paths and overlap with portal, research, deployment, and bot-operation work;
7. declare one bounded task, branch, acceptance criteria, and non-goals;
8. preserve source identity, immutable evidence, no-lookahead, risk, credential, and capital gates;
9. open a PR and use current-head CI as the merge gate;
10. update durable checkpoints after every material state change.

## 19. Canonical file map

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

### Platform architecture and governance

```text
docs/ai_platform/ARCHITECTURE.md
docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
docs/ai_platform/portal/AI_ML_AND_LEARNING_ARCHITECTURE.md
docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
```

## 20. Known facts, unknowns, and decisions

### Proven

- the collector/data contracts and multi-source acceptance evaluator exist;
- the portal read-model, BFF, UI, and Synology read-only integration are merged;
- real files were read successfully by a non-root candidate on Synology;
- the portal has no trading authority for liquidation data;
- the Wick Hunter-inspired foundation has a pure signal policy but no validated trading strategy;
- DCA, TP/SL, leverage, and execution remain separate work.

### Must be reverified before new work

- current `develop` head and open path ownership;
- current running portal image and deployment run;
- current collector container/image;
- current newest run ID;
- current completed acceptance result;
- current available disk/memory and retention state;
- whether a replay dataset has since been frozen;
- whether PI-07/PI-08 or related execution dependencies have changed.

### Unresolved design decisions

These must be made prospectively in separate tasks:

- exact accepted dataset and candle source;
- replay ordering and entry-price rule;
- volume filter definition;
- VWAP versus VWMA candidate definition;
- exit and cooldown policies;
- position sizing and portfolio limits;
- DCA policy, if ever justified;
- leverage policy;
- whether and where AI adds measurable value;
- model target and validation gates;
- live-small capital and operator policy.

## 21. Non-negotiable no-go conditions

Stop and record a blocker when work would:

- weaken or reinterpret a frozen acceptance policy after seeing results;
- mutate completed Liquid20 evidence;
- expose file paths, collector, Freqtrade, Docker, or credentials to the browser;
- remove source identity or deduplicate across exchanges;
- use unfinished-candle final values without intrabar evidence;
- use future outcome data in decision features;
- silently replace unavailable data with zero or healthy state;
- let a model bypass strategy or deterministic risk;
- enable DCA, leverage, order submission, or live capital outside a separately declared package;
- use protected holdout data iteratively;
- mark an experiment promoted because training completed;
- bypass required PR, review, or CI gates.

## 22. Completion definition for a future production-capable liquidation bot

A production-capable claim requires all of the following, not merely a working page:

- accepted and immutable source data;
- deterministic synchronization and replay;
- no-lookahead evidence;
- declared deterministic baseline;
- frozen features/target/model and independent validation;
- fees, slippage, latency, gaps, and tail-risk stress;
- sufficient event/trade sample count;
- accepted dry-run and shadow operation;
- immutable strategy/model/config/risk attribution;
- private credential and execution boundaries;
- risk limits, kill switches, alerts, and rollback;
- owner-approved live-small package;
- successful post-live review before any broader promotion.

Until then, the correct product label remains **read-only market-data and research preview**.