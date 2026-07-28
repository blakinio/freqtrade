# WickHunter first-party live archive acceptance

## Purpose

The continuously running Liquid20 collector already stores real Bybit and Binance Futures liquidation events with separate exchange event and first-party receive timestamps. This bridge converts one **closed** daily/restart run into the unchanged immutable historical package consumed by the WH-01 dataset builder.

Tardis remains useful as an optional long historical backfill. It is no longer the only possible source of real accepted WickHunter evidence.

## Input boundary

The bridge reads one existing run directory without modifying it:

```text
<live-root>/runs/liquid20-YYYYMMDDT000000Z-N/
  run-state-v1.json
  bybit-linear.ndjson
  bybit-linear-summary.json
  binance-usdm.ndjson
  binance-usdm-summary.json
```

The run is eligible only when:

- the directory and every required artifact are regular files, not symlinks;
- `run-state-v1.json` uses `liquidation-live-state-v1`;
- `run_state = completed` and `data_mode = historical`;
- execution, trading authorization and trading credentials are all false;
- the collector commit is an exact Git SHA;
- each source summary matches the final source state exactly;
- source parser rejection count is zero;
- every NDJSON row is a canonical source-matching liquidation event;
- every source event ID is a SHA-256 identity;
- `received_at_ms >= occurred_at_ms` and notional equals price times quantity;
- the files and run state do not change while acceptance is running;
- at least one real event exists before the protected final holdout.

Any mismatch fails closed and no output directory is published.

## Historical normalization

The accepted historical event preserves:

- `source_event_id` from the live collector;
- `occurred_at_ms` as exchange/event time;
- `available_at_ms = received_at_ms` as the first-party availability boundary;
- original source, symbol, liquidation side, price, quantity and raw side;
- original source-file SHA-256 and line number;
- exact Liquid20 collector commit and final run-state/source-summary hashes;
- the existing `first-party` Bybit/Binance semantic eras.

Bybit maps to provider exchange `bybit` and native channel `allLiquidation`. Binance maps to `binance-futures` and `forceOrder`.

## Output contract

Publication is temporary-directory-first, atomic and no-overwrite:

```text
<accepted-root>/
  manifest.json
  acceptance.json
  artifacts.json
  events.jsonl
  rejections.json
  source-run.json
```

The four artifacts required by WH-01 retain their existing identities and hashes. `source-run.json` additionally binds the accepted package to the exact closed live run, collector commit, run-state hash and both source artifact hashes.

A package is published only when the unchanged historical acceptance contract returns:

- `acceptance.status = pass`;
- at least one accepted event;
- zero rejected events;
- zero duplicate fingerprints;
- protected holdout excluded.

`load_accepted_import()` then independently revalidates manifest identity, artifact hashes, deterministic event order, accepted event identity hash and zero-rejection status.

## Safety and authority

The bridge:

- performs no network request;
- does not restart or mutate the collector;
- never writes under the live run directory;
- does not use exchange credentials;
- produces no labels, replay result, model, score or profitability claim;
- sets execution, trading, live-capital and model-execution authority to false;
- does not access the protected final holdout.

## Operational evidence boundary

The repository package proves deterministic conversion using synthetic closed-run fixtures. It does **not** claim that a production Synology run has already been converted and accepted.

The next operational action after reviewed merge is a separate read-only conversion of the first eligible closed production run into a new immutable output root. WH-02 may start only after that real package passes both this bridge and the existing WH-01 loader unchanged.
