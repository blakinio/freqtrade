# Liquidations live/shadow stream architecture

Status: implementation contract for `FTAI-20260727-liquidations-live-stream-repair`.

## Root cause

The previously deployed Liquid20 container was an evidence collector, not a service:

- `deploy/synology/liquid20/compose.yaml` used `restart: "no"`;
- `entrypoint.sh` accepted only a bounded smoke run or an exact 24-hour acceptance run;
- after collection it evaluated the run, wrote the acceptance report and artifact hashes, then exited;
- the portal selected the newest directory under `runs/` and treated a run with an acceptance report as historical.

The accepted run therefore remained correctly immutable, but no independent process continued to append current events. The portal polling time was exposed as `Aktualizacja`, even though it proved only that the portal had reread the same files.

## Separate data concepts

### Historical accepted evidence

Path:

```text
PORTAL_LIQUIDATIONS_DATA_ROOT/runs/liquid20-*/
```

Properties:

- produced only by the bounded evidence workflow;
- completed before evaluation;
- acceptance report and hashes retained;
- never reopened or appended by the live service;
- selected only when no explicit live-state contract exists;
- represented as `HISTORICAL`, never as `LIVE`.

### Continuous live/shadow stream

Paths:

```text
PORTAL_LIQUIDATIONS_DATA_ROOT/live/live-state-v1.json
PORTAL_LIQUIDATIONS_DATA_ROOT/live/runs/liquid20-*/run-state-v1.json
PORTAL_LIQUIDATIONS_DATA_ROOT/live/runs/liquid20-*/bybit-linear.ndjson
PORTAL_LIQUIDATIONS_DATA_ROOT/live/runs/liquid20-*/binance-usdm.ndjson
```

Properties:

- public Bybit Linear and Binance USD-M market-data endpoints only;
- no exchange trading credentials and no execution authority;
- dynamically discovers bounded USDT perpetual symbol universes;
- source-labelled deterministic event identifiers are retained from the canonical parsers;
- append-only NDJSON with newline-delimited records, periodic flush and `fsync`;
- readers ignore a partial final line until it is completed;
- daily UTC rotation creates a new live run without modifying the completed segment;
- collector and source heartbeat, reconnect, parse-error and source-error counters are written atomically;
- OKX is present in the health contract as disabled and can be enabled later without changing the portal shape.

## Explicit lifecycle contract

`live-state-v1.json` is the fixed, bounded pointer read by the portal. It contains a complete copy of the active state and identifies the current run.

Important fields:

```text
contract: liquidation-live-state-v1
run_state: active | completed
data_mode: live | historical
collector_started_at_ms
collector_heartbeat_at_ms
last_event_at_ms
last_event_received_at_ms
completed_at_ms
sources.<source>.connected
sources.<source>.last_heartbeat_at_ms
sources.<source>.last_event_at_ms
sources.<source>.last_event_received_at_ms
sources.<source>.ingest_lag_ms
sources.<source>.reconnect_count
sources.<source>.observed_symbol_count
sources.<source>.subscription_symbol_count
sources.<source>.latest_error
execution_enabled: false
trading_authorized: false
trading_credentials_present: false
```

The portal validates the fixed pointer, contract version, run identifier, newest live run, regular-file/directory requirements, size bound and no-trading assertions before reading NDJSON. Symlink and path-containment protections remain in force.

## Portal selection and status

Selection is explicit:

1. When a valid live-state contract exists, the portal reads `data/live` and requires its selected run to equal the pointer run.
2. A lexicographically newer accepted historical run under `data/runs` cannot hide the active live run because the roots are separate.
3. When no live-state contract exists, the portal falls back to the existing completed historical read-model.
4. A completed or expired live pointer is represented as `OFFLINE`, not silently relabelled as historical evidence.

Default configurable thresholds:

```text
PORTAL_LIQUIDATIONS_COLLECTOR_STALE_MS=30000
PORTAL_LIQUIDATIONS_COLLECTOR_OFFLINE_MS=120000
PORTAL_LIQUIDATIONS_EVENT_STALE_MS=300000
PORTAL_LIQUIDATIONS_SOURCE_STALE_MS=45000
```

Status inputs:

- `LIVE`: active run, fresh collector heartbeat, fresh event/receive reference and fresh connected configured sources;
- `STALE`: active run, but a configured freshness threshold is exceeded or a configured source is delayed/disconnected;
- `OFFLINE`: completed live run or collector heartbeat older than the offline threshold;
- `HISTORICAL`: no live contract and a completed dataset is selected.

Portal time labels are intentionally separate:

- `Ostatnie zdarzenie` uses exchange event time;
- `Ostatni heartbeat collectora` uses collector state time;
- `Ostatnie sprawdzenie przez portal` uses BFF read time.

Portal read time is not evidence of market-data freshness.

## Runtime and restart behavior

The default Compose service is `liquid20-live` with `restart: unless-stopped`. The former one-shot behavior remains available as the separate `liquid20-evidence` Compose profile with `restart: "no"`.

The live process:

- reconnects each exchange independently;
- uses bounded exponential backoff capped at 60 seconds;
- refreshes the dynamic symbol universe periodically;
- survives process/container restarts through Docker restart policy;
- marks an abandoned active live segment completed on a subsequent start;
- creates a new append-only live segment after restart;
- records disconnect and error state without exposing credentials or unbounded exception text.

A Docker or Synology reboot is handled by `unless-stopped`. Temporary DNS, network or WebSocket failures remain inside the reconnect loop.

## Security boundaries

Unchanged boundaries:

- browser -> same-origin portal BFF only;
- portal -> read-only bind mount only;
- browser never reads Synology files directly;
- browser never connects to collector or exchanges directly;
- portal remains non-root and has no Docker socket;
- collector remains non-root, has no published ports and has a read-only root filesystem;
- collector data mount is writable only because it owns the separate `live/` append path;
- no API keys, secrets, signals, trade recommendations, order routes or live capital.

## Controlled Synology deployment

`.github/workflows/liquidations-live-synology.yml` runs only for `develop` pushes or an explicit protected dispatch. It:

- checks out the exact reviewed SHA;
- builds an image tagged by that SHA;
- validates an isolated candidate against a separate temporary data directory;
- proves heartbeat advancement and dynamic source subscriptions;
- replaces the production live container only after candidate success;
- preserves rollback to the prior image;
- verifies non-root UID, `unless-stopped`, no Docker-socket mount and unchanged digest of accepted historical evidence;
- writes an operational JSON evidence artifact;
- labels a quiet exchange window honestly when no real liquidation event is observed.

The portal continues to mount `/volume1/docker/freqtrade-liquidations/data` at `/liquid20-data:ro`, with `PORTAL_LIQUIDATIONS_DATA_ROOT=/liquid20-data`.

## Migration and rollback

Migration does not move, rename, chmod, chown or rewrite accepted runs. The new service creates only `data/live/`.

To retain the old bounded evidence workflow:

```text
docker compose --profile evidence run --rm liquid20-evidence
```

Collector rollback restores the previous exact image through `deploy-live.sh`. Portal rollback restores the previous portal image through the existing portal deployment script. Rolling the portal back causes the old read-model to ignore `data/live/` and continue showing historical evidence; it does not delete live files. Rolling the collector back leaves the last live pointer to age naturally into `STALE` and then `OFFLINE`.
