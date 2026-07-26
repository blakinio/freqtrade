# OKX Liquidation Shadow Acceptance v1

## Purpose

Freeze the acceptance contract for one unchanged 24-hour OKX USDT-swap liquidation shadow run before any runner, evaluator, workflow or operational request is implemented.

This declaration is prospective. It does not execute the collector, mutate Synology, create a run request, add OKX to `liquid20-v1`, authorize replay, train a model or enable trading.

## Frozen scope

Policy:

```text
ai_platform/research/liquidations/okx-liquidation-shadow-acceptance-policy-v1.json
```

Source and symbols:

```text
source:  okx-usdt-swap
symbols: BTCUSDT, ETHUSDT
duration: at least 86400 seconds
```

The first long-run acceptance keeps the same two-symbol contract that passed the short transport smoke. Expanding to a larger universe or a future `liquid20-v2` is a separate package after operational acceptance.

## Host boundary

The run must execute on an always-on, non-restricted Linux staging host with a persisted exact `host_id`.

A GitHub-hosted runner is not eligible because the package requires a continuous 24-hour capture and durable raw evidence beyond an expiring CI artifact. Declaring this host class does not authorize deployment or mutation of any specific Synology or other staging host.

## Public source contract

```text
WebSocket:   wss://ws.okx.com:8443/ws/v5/public
Channel:     liquidation-orders
Scope:       instType=SWAP
Time:        https://www.okx.com/api/v5/public/time
Instruments: https://www.okx.com/api/v5/public/instruments?instType=SWAP
```

The run must use public endpoints only and refuse recognized exchange or Freqtrade trading credentials.

OKX `sz` is a contract count. Canonical base quantity remains:

```text
base_quantity = contracts * frozen_ctVal
notional_usd  = base_quantity * bankruptcy_price
```

The exact public instrument snapshot must be written before collection and bound by SHA-256.

## Frozen gates

Health and integrity gates include:

- at least 86400 seconds of collection;
- availability ratio of at least `0.995`;
- at most `2.0` disconnects per hour;
- zero parser failures and zero invalid normalized events;
- duplicate ratio at most `0.01`;
- start and end clocks synchronized within `2000 ms`;
- exact run, host, collector commit, endpoints, symbols and instrument snapshot identity;
- self-hashed manifest and report plus a checksum index over all artifacts;
- an immutable raw package with a durable storage URI.

Latency and activity gates include:

- ingest-latency threshold `5000 ms`;
- at most `0.01` of latency samples over the threshold;
- at least 10 latency samples;
- at least 10 accepted normalized events;
- at least one observed declared symbol;
- at least one event for every observed symbol.

These activity minima are intentionally modest. The package must prove that real events pass normalization and latency gates, but it must not reject a healthy transport merely because the market was quiet.

## Outcome model

The evaluator must produce exactly one terminal outcome:

### `accepted`

Every safety, identity, clock, health, activity, normalization, latency and artifact-integrity gate passes.

### `rejected`

Any safety, identity, clock, health, normalization, latency or artifact-integrity gate fails.

### `inconclusive_insufficient_activity`

All non-activity gates pass, but minimum event, symbol or latency-sample activity is not reached.

An inconclusive run neither accepts nor rejects the source. It must be preserved unchanged and followed only by a separately declared rerun; thresholds may not be changed after seeing the result.

## Required evidence package

The implementation must preserve and hash at least:

```text
okx-usdt-swap.ndjson
okx-usdt-swap-summary.json
okx-usdt-swap-instruments.json
okx-shadow-acceptance-manifest.json
okx-shadow-acceptance-report.json
artifact-sha256.txt
```

The raw NDJSON does not need to be committed to Git. Its immutable storage URI, size and SHA-256 must be published in the final repository evidence package. An expiring workflow artifact alone is insufficient.

## Implementation sequence

1. Merge this declaration without a runner or operational request.
2. Implement an inert evaluator, runner and guarded execution workflow in a separate PR.
3. Merge that infrastructure without a canonical run request.
4. Open a separate exact-one-file trigger PR on the intended staging host.
5. Capture terminal artifacts and close the trigger PR without merge.
6. Publish a compact repository evidence envelope and retain the raw package durably.

## Explicit non-authorization

Even an `accepted` result does not directly add OKX to `liquid20-v1` and does not authorize:

- replay or feature-dataset generation;
- model training or selection;
- profitability or coverage claims across exchanges;
- strategy promotion;
- exchange credentials, orders, DCA, leverage or live capital;
- access to a protected holdout.

Acceptance permits only a later, separately reviewed source-integration research proposal.
