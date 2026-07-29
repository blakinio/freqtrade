# Binance Spot Instrument Shadow Acceptance Runtime V2

## Purpose

Runtime v2 repairs only the execution wrapper for the separately reviewed Binance Spot
instrument-catalog acceptance package. The policy, source URL, observation schedule,
thresholds, parser, evidence model and production-disabled boundary remain unchanged.

The first canonical trigger, PR 687 at request identity
`binance-spot-instrument-shadow-acceptance-20260728-v1`, stopped during the no-network
preflight because the isolated Python environment did not contain `jsonschema`. The runner,
exact-one-file scope, durable-storage and credential/proxy gates passed. No Binance request,
acceptance observation or durable evidence package was created. The PR was closed without
merge and its request and run identities are permanently consumed.

## Runtime repair

The v2 workflow is:

```text
.github/workflows/ai-platform-binance-spot-instrument-shadow-acceptance-v2.yml
```

It retains the exact approved runner `freqtrade-synology-staging`, protected environment
`synology-staging`, canonical durable root and one-opened-event trigger model. Before importing
the acceptance package it creates an isolated Python 3.12 environment and installs exactly:

```text
jsonschema==4.26.0
```

The workflow verifies the installed version before the package preflight. This is the same
pinned dependency used by the successful no-network replacement proof. No exchange SDK,
credential, proxy, alternate host or trading dependency is introduced.

A standard-library-only preflight guard validates runner identity, exact request contents,
storage mapping, atomic durable I/O and non-reuse of the run directory before dependency
installation or source network activity:

```text
tools/market_data/binance_spot_instrument_acceptance_v2_preflight.py
```

## New canonical request identity

A later trigger PR may add exactly:

```text
ai_platform/market_data/run-requests/binance-spot-instrument-shadow-acceptance-20260729-v2.json
```

The complete request identity is frozen as:

```text
request_id = binance-spot-instrument-shadow-acceptance-20260729-v2
run_id     = binance-spot-instrument-shadow-acceptance-20260729-v2-r1
```

The v2 workflow does not accept the consumed v1 path or identities. Synchronizing, reopening
or rerunning the v1 trigger is not an authorized retry. Any later attempt after v2 would require
another separately reviewed identity and workflow contract.

## Unchanged acceptance contract

Runtime v2 preserves:

- exact public URL `https://api.binance.com/api/v3/exchangeInfo?showPermissionSets=false`;
- 24 hours, 15-minute interval and 97 scheduled observations;
- one public request attempt and zero retries per observation;
- 20-second timeout, redirect refusal and 16 MiB response limit;
- durable successful raw and normalized snapshots;
- bounded failure metadata without partial raw payloads;
- independent accepted, rejected or inconclusive evaluation;
- `source_acceptance = false` and `production_source_enabled = false` for every outcome;
- `orders_submitted = 0` and no strategy, replay, model or live-capital authority.

## Required sequence

The runtime repair must first merge after exact-head CI and security validation. A separate
no-network proof must then check out the exact merged repair on `freqtrade-synology-staging`,
exercise the v2 static preflight and the full injected 97-slot acceptance/evaluator paths, and
leave no durable package. Only after that terminal proof succeeds may a separately reviewed
exact-one-file v2 trigger PR be opened.

The trigger PR must be closed without merge after its one `opened`-event execution. Its
terminal evidence may support only an acceptance conclusion under the frozen policy; it cannot
enable a production source or trading capability.
