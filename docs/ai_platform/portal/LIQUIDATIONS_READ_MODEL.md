# Portal Liquidations read-model

## Status

The first package defines a versioned, bounded, server-side read-model for Liquid20 market-data evidence. It does not yet add the portal page, route handlers or Synology mount; those are separate bounded packages.

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

The Next.js server process owns the read-model because the current Synology preview deploys the web application without the Python control plane. A later BFF package may expose only the versioned event, summary and health contracts.

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

Health also carries the latest completed acceptance evidence. Therefore the known failed Binance latency gate remains visible while a newer retry is still in progress.

## Security boundary

The read-model contains no exchange credentials, Freqtrade control credentials, Docker socket access, strategy configuration, order submission, signal generation or execution authority. Returned health records state `research_preview: true` and `trading_authorized: false`.

Bybit and Binance semantics remain source-labelled. Binance USD-M `forceOrder` represents the latest liquidation order per symbol in an approximately 1000 ms window and is not semantically identical to Bybit `allLiquidation`.
