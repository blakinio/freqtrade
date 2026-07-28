# WickHunter production live archive conversion

## Purpose

This package performs the first separately governed production operation after the WickHunter live-archive acceptance bridge. It selects one completed, non-empty Liquid20 run from the production live archive, converts it read-only into a new immutable accepted-import package, and independently verifies that package with the unchanged WH-01 `load_accepted_import()` contract.

The operation is a data-evidence gate only. It produces no labels, replay result, model, score, strategy-quality claim, profitability claim, execution authority or live-capital authorization.

## Trigger contract

The workflow runs only when an internal pull request against `develop` adds exactly:

```text
ai_platform/wickhunter/run-requests/production-live-archive-conversion-v1.json
```

The request freezes:

- a bounded lowercase operation identifier;
- deterministic selection policy `latest-completed-nonempty-before-holdout`;
- protected holdout start `2026-08-01T00:00:00Z`;
- read-only helper path `/liquid20-data`;
- writable isolated state path `/output`;
- the canonical Synology Liquid20 archive storage identity;
- false execution, trading, credential, model-execution and live-capital authority.

The trigger PR must contain no other file and must be closed without merge after terminal evidence is captured.

## Synology boundary

The job runs on exact runner `freqtrade-synology-staging` in protected environment `synology-staging`.

Host paths:

```text
production Liquid20 input:
  /volume1/docker/freqtrade-liquidations/data

immutable WickHunter operation roots:
  /volume1/docker/freqtrade/state/wickhunter-accepted-imports/<operation-id>/
```

The converter executes in a disposable helper created from the exact immutable image ID of the running repository runner. The helper has:

- no network;
- read-only root filesystem;
- bounded tmpfs;
- all Linux capabilities dropped;
- `no-new-privileges`;
- bounded memory;
- the production Liquid20 root mounted read-only;
- only the isolated WickHunter state root mounted writable;
- no trading credentials.

The exact request commit source is staged through the existing runner-state host mapping and removed after the operation. The accepted output is retained.

## Deterministic selection

The operator scans only:

```text
<liquid20-data>/live/runs/liquid20-*/
```

A preliminary candidate must have:

- a non-symlink run directory and regular state/source files;
- the `liquidation-live-state-v1` contract;
- `run_state = completed` and `data_mode = historical`;
- false execution, trading authorization and trading-credential state;
- a completion time before the protected holdout;
- both required Bybit and Binance source states and files;
- at least one recorded event.

Among preliminary candidates, the newest completion time and then run ID win deterministically. The selected run must still pass the full bridge validation. The operator does not silently fall back to an older run after a selected candidate fails; it fails closed instead.

## Atomic output

One operation publishes atomically and never overwrites:

```text
<operation-id>/
  request.json
  report.json
  operation-artifacts.json
  accepted/
    manifest.json
    acceptance.json
    artifacts.json
    events.jsonl
    rejections.json
    source-run.json
```

`accepted/` is created by `accept_closed_live_run()`. Before publication, the operator calls unchanged `load_accepted_import()` and verifies provider, import identity, accepted count and source-run identity. `operation-artifacts.json` binds the copied request, bounded report and every accepted artifact hash.

A second isolated helper mounts the completed state root read-only and independently repeats all operation-index and WH-01 checks.

## Evidence and privacy

GitHub Actions uploads only bounded metadata:

- copied request;
- conversion report;
- operation artifact index;
- accepted manifest, acceptance, artifact index and source-run provenance;
- bounded converter and verifier result summaries.

The potentially large `events.jsonl` is retained only in the durable Synology operation root and is not uploaded to GitHub Actions.

## Next gate

A successful terminal conversion proves that one real immutable production source package is consumable by WH-01. It does not by itself prove enough duration, regime diversity or feature coverage for WH-02. The terminal evidence must be reviewed and the durable program/task checkpoint updated before a separate WH-02 implementation package is opened.
