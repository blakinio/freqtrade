# Portal Liquidations Integration — Autonomous Agent Prompt

Work autonomously to integrate Bybit and Binance liquidation data into the AI Trading Portal.

Repositories:

- `blakinio/freqtrade`
- `blakinio/Oteryn-Platform`

Your objective is to deliver a safe, read-only **Liquidations** module in the portal and deploy it through the existing Synology environment.

Do not rely blindly on this prompt or previous conversation history. Current repository state, Git history, open and closed pull requests, GitHub Actions, task records, `AGENTS.md`, portal documentation, collector code, and actual Synology runtime state are the sources of truth.

Continue autonomously until the bounded task is complete or a durable blocker requires user action.

---

## 1. Mandatory live-state preflight

Perform a fresh but efficient preflight before editing anything.

Verify at least:

- current default branches and HEADs of both repositories;
- open pull requests related to Liquid20, the portal, Synology, and portal preview deployment;
- current GitHub Actions workflows and required checks;
- actual self-hosted runner labels and availability;
- the current private-LAN portal port on Synology;
- current state of `blakinio/Oteryn-Platform#148`;
- current state of the `liquid20-collector` container;
- the actual Liquid20 data path on Synology;
- current AI Trading Portal structure;
- current portal API, BFF, Data Plane, and deployment contracts;
- `AGENTS.md` in every repository you modify;
- relevant durable task records and checkpoints.

Do not assume that pull request numbers, commits, ports, paths, or branches mentioned below are still current.

Earlier state that must be verified rather than assumed:

- one complete Liquid20 run collected 24 hours of data;
- it observed all 20 frozen symbols on both exchanges;
- acceptance failed only on `binance-usdm.maximum_latency_over_threshold_ratio`;
- the acceptance policy is frozen and must not be weakened;
- evidence was expected under a path similar to `/volume1/docker/freqtrade-liquidations/data/runs/`;
- the portal preview may have used private-LAN port `3031`.

---

## 2. Product goal

Add a new portal surface named **Liquidations**.

The module must present Liquid20 information as read-only market-data and research-preview information.

Minimum interface scope:

1. A stream of recent liquidation events.
2. Filters for:
   - source: Bybit, Binance, or all;
   - symbol;
   - liquidated position side: long or short;
   - time range.
3. Event columns:
   - event time;
   - exchange/source;
   - symbol;
   - liquidated position side;
   - price;
   - quantity;
   - notional value in USDT;
   - ingest latency.
4. Summary windows:
   - last 5 minutes;
   - last hour;
   - last 24 hours.
5. Symbol ranking by:
   - event count;
   - total notional;
   - long/short split.
6. Data status:
   - mode;
   - freshness;
   - latest event time;
   - active sources;
   - observed symbol count;
   - availability;
   - disconnect rate;
   - acceptance status when available.
7. Explicit source-semantics explanation:
   - Bybit and Binance do not have identical feed semantics;
   - Binance `forceOrder` publishes the latest liquidation order per symbol within an approximately 1000 ms window;
   - cross-exchange events must not be deduplicated or summed without retaining source identity.

The portal must truthfully classify data as:

- `historical` — a completed run;
- `live` — an actively written run;
- `stale` — no recent source update within the declared freshness window;
- `acceptance-failed` — data exists, but the run did not pass the frozen policy;
- `accepted` — only when a report explicitly contains `passed: true`.

Never present an unaccepted run as a production-quality live source.

---

## 3. Non-negotiable boundaries

Do not:

- change the frozen 20-symbol Liquid20 universe;
- change the 24-hour acceptance duration;
- change thresholds or the frozen acceptance policy;
- remove, bypass, or reinterpret the latency gate;
- change existing evidence schemas without a separate versioned contract;
- mutate existing evidence directories;
- delete or overwrite completed 24-hour evidence;
- expose Freqtrade REST or WebSocket surfaces directly to the browser;
- expose the Liquid20 collector directly to the public Internet;
- mount the Docker socket into the portal application or data adapter;
- add Binance, Bybit, or other exchange credentials;
- connect this module to order submission;
- generate buy, sell, long, or short recommendations;
- enable DCA, leverage, dry-run trading, or live trading;
- treat liquidation observations as trading authorization;
- return secrets, tokens, or private raw logs to the UI;
- modify completed Phase 5, Phase 6, RL, or protected-holdout contracts.

This module is strictly read-only market-data and research-preview functionality.

---

## 4. Target architecture

Preserve the portal architecture boundary:

```text
Bybit / Binance
        ↓
Liquid20 collector
        ↓
immutable NDJSON + summaries + manifest + acceptance report
        ↓
private read model / data adapter
        ↓
portal control plane / BFF
        ↓
browser
```

The browser must not read Synology files directly and must not connect directly to the collector.

Prefer the smallest safe implementation that fits current code. Acceptable approaches include:

- a read-model module inside the existing portal control plane;
- a private read-only adapter on Synology;
- a server-side Next.js reader only when current architecture and deployment isolation make that safe.

Do not introduce a new microservice without a demonstrated need.

Mount Liquid20 evidence read-only, using the verified current path. The expected shape is similar to:

```text
/volume1/docker/freqtrade-liquidations/data:/liquid20-data:ro
```

The portal or adapter must not receive:

- `/var/run/docker.sock`;
- exchange keys;
- strategy directories;
- live-trading configuration;
- write access to Liquid20 evidence.

If indexing or caching is required, write it only to a separate adapter-state directory, never to the evidence volume.

---

## 5. Data contract

Preserve the canonical liquidation event fields:

- `schema_version`;
- `source`;
- `source_event_id`;
- `symbol`;
- `liquidated_position_side`;
- `occurred_at_ms`;
- `received_at_ms`;
- `price`;
- `quantity`;
- `notional_usd`;
- `raw_side`.

Add a versioned portal read-model contract without mutating the original event.

Example portal event:

```json
{
  "schema_version": 1,
  "source": "binance-usdm",
  "source_event_id": "string",
  "symbol": "BTCUSDT",
  "liquidated_position_side": "long",
  "occurred_at_ms": 0,
  "received_at_ms": 0,
  "ingest_latency_ms": 0,
  "price": "0.0",
  "quantity": "0.0",
  "notional_usd": "0.0"
}
```

Keep decimal values as strings or a safe decimal type. Do not introduce floating-point precision loss.

Minimum BFF endpoints:

```text
GET /api/market/liquidations
GET /api/market/liquidations/summary
GET /api/market/liquidations/health
```

Minimum list parameters:

```text
source
symbol
side
since
until
limit
cursor
```

Requirements:

- enforce a maximum result limit;
- deterministic sorting;
- stable cursor or pagination;
- strict parameter validation;
- no path traversal;
- no user-selected arbitrary file paths;
- no return of complete logs or unrestricted manifests;
- no full scan of large evidence files on every request.

---

## 6. File handling and performance

Do not load an entire NDJSON file into memory for every request.

Implement a bounded read model that supports:

- detection of the newest valid run;
- reading completed and active NDJSON files;
- persisted or recoverable offsets;
- a bounded cache of recent events;
- an optional SQLite index in a separate state directory only when justified;
- safe handling of a partially written final line;
- restart recovery;
- run rotation and `run_id` changes;
- explicit memory and record-count limits;
- zero mutation of source evidence.

Server-side polling every few seconds is acceptable for the first delivery. Do not require WebSocket or SSE unless the portal already has a suitable secure event mechanism.

---

## 7. Health and data quality

The health endpoint must return safe aggregates only. A representative shape is:

```json
{
  "mode": "historical",
  "run_id": "string",
  "acceptance_status": "failed",
  "failed_gates": [
    "binance-usdm.maximum_latency_over_threshold_ratio"
  ],
  "sources": {
    "bybit-linear": {
      "events": 0,
      "observed_symbols": 0,
      "availability_ratio": 0,
      "disconnects_per_hour": 0,
      "last_event_at_ms": 0
    },
    "binance-usdm": {
      "events": 0,
      "observed_symbols": 0,
      "availability_ratio": 0,
      "disconnects_per_hour": 0,
      "last_event_at_ms": 0
    }
  },
  "stale": false
}
```

Do not obtain health through the Docker socket.

Derive health from bounded reads of:

- source summaries;
- the multi-source manifest;
- the acceptance report;
- file freshness or latest event timestamps;
- an existing safe status file when one is already part of the trusted control path.

The UI must clearly show:

- `Acceptance failed` when applicable;
- failed gate names;
- that data remains available as research preview;
- that the result does not authorize trading.

---

## 8. UI and user experience

Use the existing portal design system and information architecture.

Prefer navigation similar to:

```text
Market Data
└── Liquidations
```

The surface should include:

- a **Liquidations** heading;
- source-health status;
- acceptance status;
- 5-minute, 1-hour, and 24-hour summary cards;
- an event table;
- filters;
- symbol ranking;
- long/short liquidation split;
- last-updated timestamp;
- loading, empty, stale, and error states;
- responsive behavior.

Do not use trading-call language such as “buy,” “sell,” “long signal,” “short signal,” or “market edge.”

Use neutral terms such as “liquidated long positions,” “liquidated short positions,” “market observation,” and “research preview.”

---

## 9. Tests

Add focused tests for at least:

- valid NDJSON parsing;
- partial final lines;
- malformed records;
- source filtering;
- symbol filtering;
- side filtering;
- time ranges;
- result limits;
- deterministic ordering;
- 5-minute, 1-hour, and 24-hour aggregation;
- notional aggregation with source identity retained;
- absence of cross-source deduplication;
- historical, live, and stale classification;
- failed and passed acceptance states;
- path-traversal rejection;
- read-only evidence access;
- absence of credentials from contracts;
- UI loading, empty, stale, and error states;
- rendering a known liquidation fixture;
- explicit Binance feed-semantics warning.

Add portal E2E coverage for:

1. opening the Liquidations page;
2. loading fixture or read-model data;
3. filtering by symbol;
4. filtering by source;
5. displaying acceptance status;
6. verifying there is no trading action;
7. verifying data is not fetched directly from a public Freqtrade API.

Fixtures must be explicitly labeled and must never be presented as live data.

---

## 10. Synology deployment

Use the existing portal deployment path. Do not create a competing deployment mechanism when the repository already provides a self-hosted runner, exact-SHA image build, candidate container, health check, rollback, and private-LAN binding.

Extend the existing deployment minimally.

The deployment must:

- build an immutable image;
- mount Liquid20 data read-only;
- mount a separate read-write adapter-state directory only when required;
- avoid a Docker socket mount in the application;
- avoid unnecessary new public ports;
- preserve private-LAN exposure;
- preserve the current verified portal port;
- run candidate health checks;
- preserve rollback;
- validate the Liquidations page;
- validate the health endpoint;
- verify absence of exchange credentials;
- verify the evidence mount is read-only.

Do not restart or delete the Liquid20 collector unless a verified dependency requires it. Do not rerun acceptance merely to build the portal UI.

---

## 11. Pull request strategy

Do not deliver the entire integration as one oversized pull request.

Preferred sequence:

### PR 1 — Contract and read model

- versioned contracts;
- bounded parser and reader/index;
- summaries and health;
- focused tests.

### PR 2 — Portal API and UI

- BFF endpoints;
- Liquidations page;
- filters and summaries;
- quality and acceptance status;
- UI tests and E2E.

### PR 3 — Synology deployment

- read-only mount;
- exact-SHA image;
- health checks;
- rollback preservation;
- private-LAN deployment validation.

Each pull request must be small, reversible, based on current repository state, fully reviewed, and green before merge. Do not bypass branch protection or required checks.

---

## 12. Documentation and durable checkpoint

Create a separate task record for the portal liquidation integration.

The task record must include:

- goal;
- owned paths;
- dependencies;
- context routes;
- proven facts;
- derived conclusions;
- unknowns;
- blockers;
- conflicts;
- first failure;
- rejected hypotheses;
- changed paths;
- validation evidence;
- exactly one `next_action` while work remains.

Update the checkpoint after each material milestone.

Update relevant portal documentation for:

- architecture;
- UI delivery status;
- data ownership;
- deployment;
- security boundaries;
- research-preview classification.

---

## 13. Completion criteria

The task is complete only when:

- the portal has a working Liquidations page;
- the page uses real Liquid20 files on Synology;
- all browser access goes through a private read model or BFF;
- the browser does not connect directly to the collector or Freqtrade;
- the Liquid20 volume is mounted read-only;
- no exchange credentials are provided;
- no Docker socket is mounted into the application;
- filters and summaries work;
- acceptance status is displayed truthfully;
- the Binance failed gate remains visible until a later run passes;
- historical, live, and stale states are distinguished correctly;
- unit, integration, and E2E tests pass;
- Synology deployment and candidate health checks pass;
- rollback remains available;
- the portal is reachable on the verified private-LAN URL;
- the task checkpoint is completed and archived;
- no frozen acceptance policy was changed;
- no trading was enabled or authorized.

---

## 14. Reporting

Do not send frequent narration of routine actions.

Report only material milestones, merged pull requests, successful Synology deployment, meaningful failures, durable blockers, or final completion.

The final report must include:

- pull request numbers;
- merge SHAs;
- relevant workflow runs;
- current private-LAN portal URL;
- implemented endpoints;
- read-only mount confirmation;
- confirmation that no credentials or Docker socket were added;
- confirmation that real Liquid20 data is used;
- current acceptance status;
- test results;
- remaining limitations;
- exactly one next step only when the task is not complete.

Begin with the live-state preflight and continue autonomously.
