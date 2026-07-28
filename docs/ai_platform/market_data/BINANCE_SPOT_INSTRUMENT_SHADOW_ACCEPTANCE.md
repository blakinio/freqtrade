# Binance Spot Instrument Shadow Acceptance

## Purpose

This package performs a separately reviewed operational acceptance window for the public Binance Spot instrument catalog. It builds on the successful reduced-payload smoke artifact `8686988992` but does not reinterpret one snapshot as continuous source acceptance.

The acceptance package is research and integration evidence only. Even an `accepted` outcome keeps:

```text
production_source_enabled = false
source_acceptance = false
orders_submitted = 0
```

An accepted package may support a later pull request proposing a production integration contract. It does not itself enable a recurring production collector, strategy research, replay, model training, WebSockets, order submission, trading authority or live capital.

## Frozen source contract

The source is public and credential-free:

```text
https://api.binance.com/api/v3/exchangeInfo?showPermissionSets=false
```

The query parameter is retained because the reviewed smoke showed that the unfiltered response exceeded the frozen 16 MiB limit, while the reduced-payload response completed successfully at 6,629,829 bytes and normalized 3,659 instruments.

The acceptance policy keeps:

- one HTTP attempt per scheduled sample;
- zero retries per sample;
- a 20-second timeout;
- a 16 MiB maximum response;
- redirect refusal;
- JSON content-type validation;
- exact raw response persistence for successful samples;
- normalized catalog persistence for successful samples;
- bounded metadata only for failed samples;
- credential and proxy refusal.

A later scheduled sample is a distinct observation slot, not a retry of an earlier failed request.

## Observation window

The frozen window is:

- duration: **24 hours**;
- interval: **15 minutes**;
- scheduled samples: **97**, including the observations at offset zero and at the 24-hour boundary;
- exact runner: `freqtrade-synology-staging`;
- routing label: `freqtrade-staging`;
- protected environment: `synology-staging`.

The workflow is inert until a separate pull request adds exactly:

`ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260728-v1.json`

The trigger workflow responds only to the initial `opened` event. Synchronizing, reopening or rerunning the pull request is not an authorized retry path. Any new completed acceptance attempt requires a new reviewed request identity.

## Durable evidence root

Raw evidence is retained under:

```text
/var/lib/freqtrade-staging-state/binance-spot-instrument-acceptance/<run_id>
```

Before network activity, the workflow:

1. validates the exact runner name, Linux OS and allowed architecture;
2. requires `/var/lib/freqtrade-staging-state` to exist and be writable;
3. permits creation only of the canonical acceptance child directory;
4. excludes runner-temporary and workspace paths;
5. performs an atomic write, `fsync`, rename and read-back probe;
6. removes the probe before the first source request.

The GitHub Actions artifact contains bounded metadata and sample reports. It intentionally excludes the large raw and normalized snapshot series. Ephemeral CI storage alone is insufficient for acceptance.

## Per-sample evidence

Every successful sample stores:

```text
samples/NNNN/raw-response.json
samples/NNNN/instrument-catalog-snapshot.json
samples/NNNN/sample-report.json
```

The sample report records transport metadata, response size and duration, raw hash, instrument counts, required anchor-symbol presence, source snapshot identity, catalog snapshot hash, one attempt, zero redirects, zero orders and disabled production state.

A failed sample stores only:

```text
samples/NNNN/sample-report.json
```

The failure report records the stage and bounded error metadata. A failed or partial response is not persisted as accepted raw evidence and is not normalized.

## Acceptance thresholds

The frozen gates require:

- at least 86,400 observed seconds;
- all 97 scheduled request slots attempted;
- at least 95 successful samples;
- availability ratio of at least 0.98;
- no more than one consecutive failure;
- no more than two transport failures;
- zero parse failures;
- zero integrity failures;
- maximum successful response duration of 15 seconds;
- every successful response below 16 MiB;
- instrument count between 3,000 and 10,000;
- at least 1,000 active instruments;
- `BTCUSDT` and `ETHUSDT` active in every successful sample;
- no consecutive instrument-count movement greater than 2%;
- `production_source_enabled = false`;
- `orders_submitted = 0`.

The count and anchor floors are deliberately below the reviewed smoke values of 3,659 total and 1,369 active instruments. They detect severe truncation or semantic drift without treating ordinary listing changes as an automatic failure.

## Package sealing and independent evaluation

The durable package contains:

- `run-request.json`;
- `policy.json`;
- the complete successful raw and normalized sample series;
- all sample reports;
- `binance-spot-instrument-acceptance-summary.json`;
- `binance-spot-instrument-acceptance-manifest.json`;
- `binance-spot-instrument-acceptance-report.json`;
- `artifact-sha256.txt`.

The runner computes summary metrics, manifest entries, self hashes and the terminal report. A separate evaluator then:

- reloads the frozen external policy;
- verifies the packaged policy is identical;
- verifies request identity and safety fields;
- verifies every manifest path, size and SHA-256 digest;
- verifies sample-report self hashes and required files;
- recomputes the summary from sample reports;
- verifies the complete checksum index;
- recomputes every gate and terminal outcome;
- rejects any attempt to set source acceptance or production enablement.

The workflow fails if the runner and evaluator return different outcomes.

## Outcomes

### `accepted`

Every safety, identity, duration, availability, transport, parsing, normalization, anchor-symbol, catalog-stability and integrity gate passes.

This outcome authorizes only a later separately reviewed integration proposal. Production remains disabled.

### `rejected`

A safety, transport, parsing, normalization, catalog, latency or integrity gate fails.

The source is not accepted and the workflow must not retry automatically.

### `inconclusive_incomplete_window`

The package is internally valid but does not complete the minimum observation window or required scheduled sample count.

This outcome neither accepts nor rejects source quality. A later attempt requires a new request identity and separate trigger pull request.

## Explicit exclusions

This work does not authorize:

- private Binance endpoints or API credentials;
- alternate Binance hosts;
- proxy, VPN or runner-region bypasses;
- WebSocket collection;
- trades, orders, withdrawals, DCA or leverage;
- replay or performance claims;
- strategy or model research;
- automatic production source registration;
- live-capital use.
