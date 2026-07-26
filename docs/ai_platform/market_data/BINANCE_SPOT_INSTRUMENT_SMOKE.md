# Binance Spot Instrument Catalog Smoke v1

Status: **bounded public smoke infrastructure; no source acceptance**

## Scope

This package authorizes one public REST request to Binance Spot `exchangeInfo` through an exact-one-file pull-request trigger. The smoke exercises the merged deterministic `binance-spot` instrument adapter and uploads immutable evidence as a GitHub Actions artifact.

It does not authorize recurring execution, retries, another venue or product family, WebSockets, trades, order books, broad capture, source acceptance, deployment, replay, models, portal access or trading.

## Frozen request

The only authorized URL is:

`https://api.binance.com/api/v3/exchangeInfo`

The policy freezes:

- one attempt and zero retries;
- a 20-second timeout;
- a 16 MiB response limit;
- public access without credentials;
- JSON response content;
- no accepted redirect;
- exact raw payload preservation in the workflow artifact;
- `source_acceptance = false`.

The workflow runs only when a pull request adds exactly:

`ai_platform/market_data/run-requests/binance-spot-instrument-smoke-v1.json`

The trigger request is never merged. Its sole purpose is to execute the frozen smoke against the exact PR head and publish temporary evidence.

## Evidence

A successful run uploads:

- `raw-response.json` — exact response bytes;
- `instrument-catalog-snapshot.json` — deterministic adapter output;
- `run-request.json` and `policy.json` — canonical execution inputs;
- `report.json` — request timing, transport metadata, counts, provenance and self-hash;
- `checksums.sha256` — exact hashes for every evidence file.

The report records one attempt, zero redirects, response byte count and SHA-256, active/inactive instrument counts, source snapshot identity, catalog snapshot hash and exact collector commit.

Raw response bytes remain in the workflow artifact and are not committed to Git. A later publication task may commit only bounded machine-readable summary evidence and exact artifact metadata.

## Failure semantics

The smoke fails closed before transport when recognized trading credentials are present. It also rejects:

- any request or policy drift;
- a non-200 response;
- a redirect;
- unexpected content type;
- invalid `Content-Length`;
- an empty or oversized response;
- invalid UTF-8 or non-object JSON;
- any adapter mapping, identity, hash or contract failure;
- an existing output directory.

A successful smoke proves only that one public request completed and the exact response could be mapped under adapter v1 at that time. It does not prove historical completeness, continuous availability, capacity, WebSocket semantics or broad source acceptance.
