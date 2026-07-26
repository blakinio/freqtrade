# Portal Liquidations read-model

## Status

The bounded Liquid20 server-side read-model is implemented and merged through PR `#307` as `aa2f193b970588e478b5d57f58d2ddfd7f4aab67`.

Its same-origin BFF and responsive Likwidacje page were merged through PR `#311` as `228b5ad3eb12c6adab300ab86461d3fa67acaa47`. The real-data Synology read-only deployment boundary was merged through PR `#313` as `1bf106fb5919706cca4db4f8245e00d2a1932df9`.

Use `LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md` for the complete current architecture, research separation, AI-bot assumptions, future package ordering and agent handoff rules. This file remains the focused reader contract.

## Ownership and source of truth

Liquid20 immutable run directories remain the authoritative source. The portal does not modify them and does not reinterpret the frozen acceptance policy.

Fixed source artifacts are read from the latest valid `liquid20-<timestamp>-<attempt>` directory:

- `bybit-linear.ndjson`;
- `binance-usdm.ndjson`;
- `bybit-linear-summary.json`;
- `binance-usdm-summary.json`;
- `multi-source-acceptance-report.json`, when final evaluation exists.

No browser-controlled path or filename is accepted.

## Read boundary

The Next.js server process owns the read-model because the current Synology preview deploys the web application without the Python control plane. The same-origin BFF exposes only the versioned event, summary and health contracts.

The reader:

- rejects symlinked runs and source files;
- resolves only fixed children below the configured data root;
- reads NDJSON incrementally from remembered offsets;
- keeps a bounded in-memory event cache;
- tolerates an incomplete final line from an active writer;
- rejects malformed or source-mismatched records;
- detects file replacement, truncation and run rotation;
- limits query results to 200 records;
- uses deterministic ordering and cursor pagination;
- preserves decimal values as strings and aggregates with exact integer scaling;
- deduplicates only the same `source + source_event_id` identity;
- never deduplicates between Bybit and Binance;
- never writes to the Liquid20 evidence directory.

A truncated cache is reported explicitly. It must not be represented as a complete 24-hour aggregate.

## Status semantics

- `live`: the latest run has no final acceptance report and source activity is fresh;
- `stale`: the latest unfinished run has exceeded the configured freshness threshold;
- `historical`: a final acceptance report exists;
- `in-progress`: the active run has no final acceptance result;
- `failed`: a final report exists with `passed: false`;
- `accepted`: a final report exists with `passed: true`.

Health also carries the latest completed acceptance evidence. Therefore a known failed gate remains visible while a newer retry is still in progress.

## API and UI boundary

The same-origin routes are:

```text
GET /api/market/liquidations
GET /api/market/liquidations/summary
GET /api/market/liquidations/health
```

The browser page is:

```text
/market/liquidations
```

The BFF validates source, symbol, side, time range, cursor and bounded limit parameters. It returns explicit unavailable or invalid-input states and never exposes a file path, collector endpoint, exchange endpoint, Docker metadata or Freqtrade control surface.

## Synology boundary

The authoritative host root is mounted read-only:

```text
/volume1/docker/freqtrade-liquidations/data -> /liquid20-data:ro
```

The portal remains non-root and receives only the verified supplementary group required to read the existing `root:root` evidence tree. Host permissions are not changed, the Docker socket is not mounted, and no data is copied into a writable portal path.

## Security boundary

The read-model contains no exchange credentials, Freqtrade control credentials, Docker socket access, strategy configuration, order submission, signal generation or execution authority. Returned health records state `research_preview: true` and `trading_authorized: false`.

Bybit and Binance semantics remain source-labelled. Binance USD-M `forceOrder` represents the latest liquidation order per symbol in an approximately 1000 ms window and is not semantically identical to Bybit `allLiquidation`.
