# Binance Spot Instrument Shadow Acceptance Runtime V3

## Why v3 exists

Runtime v2 executed all 97 observations inside one GitHub Actions job. The process slept between observations and occupied the only `freqtrade-synology-staging` runner for the full acceptance window. Workflow `30459738848`, job `90602377126`, was manually cancelled after five successful public observations. Its bounded metadata artifact is `8729171100` with digest `sha256:584f8051e87a1a44a6a3daf2efd77baf9ac8a54d8e992a5d3a58edfb39dc5acb`. The run has no terminal accepted, rejected or inconclusive outcome.

The blocking v2 workflow is removed. It must not be restored, reopened or rerun.

## Non-blocking execution model

Runtime v3 preserves the frozen source policy while splitting execution into short jobs:

1. An exact-one-file trigger PR initializes immutable state under the approved Synology durable root.
2. A scheduled workflow runs every 15 minutes.
3. Each scheduled job collects at most one due observation and exits.
4. The next observation cannot occur less than 900 seconds after the previous completed observation.
5. After observation 97, the same short job seals the complete package, runs the independent evaluator and uploads bounded metadata.

Both the initializer and sampler have a ten-minute job timeout. There is no sleep loop and no job can reserve the runner for the 24-hour window.

## Durable state and concurrency

The scheduler uses:

```text
/var/lib/freqtrade-staging-state/binance-spot-instrument-acceptance/
```

An active-pointer document selects exactly one run. The run contains a self-hashed incremental state document, immutable request and policy copies, and the existing raw, normalized and sample-report evidence. A Linux file lock and one global GitHub Actions concurrency group prevent overlapping initialization or sampling.

The active pointer is removed only after the package is sealed and independently evaluated. A completed state can therefore be finalized again after an interrupted terminal job without recollecting observations.

## Frozen v3 identity

A later separately reviewed trigger may add exactly:

```text
ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260729-v3.json
```

with:

```text
request_id = binance-spot-instrument-shadow-acceptance-20260729-v3
run_id     = binance-spot-instrument-shadow-acceptance-20260729-v3-r1
```

The runtime repair PR contains no trigger request and performs no Binance call.

## Unchanged safety and acceptance boundary

Runtime v3 retains:

- the exact public reduced-payload Binance Spot URL;
- 97 observations with at least 900 seconds between completed observations;
- one request attempt and zero retries per observation;
- 20-second timeout, redirect refusal and 16 MiB response limit;
- exact approved Synology staging runner and durable evidence root;
- credential and proxy refusal for every initializer and sampler job;
- raw and normalized durable evidence plus independent final evaluation;
- `source_acceptance = false`, `production_source_enabled = false` and `orders_submitted = 0` for every outcome.

No strategy research, model training, replay, order execution, production source enablement or live-capital authority is introduced.
