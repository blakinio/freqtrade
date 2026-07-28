# OKX Shadow Acceptance Execution Infrastructure v1

## Purpose

This package runs one guarded 24-hour, public and credential-free OKX liquidation
shadow acceptance on the dedicated Freqtrade Synology staging runner.

The acceptance remains isolated from `liquid20-v1`, replay, models, strategies,
orders and live capital. A successful run is operational source evidence only.

## Components

Runner and deterministic evaluator:

```text
ai_platform/scripts/liquidation_okx_shadow_acceptance.py
```

Independent package verifier:

```text
ai_platform/scripts/liquidation_okx_shadow_acceptance_evaluator.py
```

Guarded trigger workflow:

```text
.github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
```

The runner writes an immutable instrument snapshot, start and end clock probes,
raw normalized events, a self-hashed manifest, a self-hashed report and
`artifact-sha256.txt` over the evidence package.

The independent evaluator does not rewrite evidence. It recomputes the report,
verifies the stored report and its self-hash, and verifies all checksum entries.

## Outcome and exit-code contract

```text
0  accepted
1  rejected or incomplete evidence
2  inconclusive_insufficient_activity
```

`inconclusive_insufficient_activity` is allowed only when every non-activity gate
passes and one or more frozen event, symbol or latency-sample minimums fail.
Identity, safety, clock, health, normalization, latency-quality or artifact
failures produce `rejected`.

Every outcome remains research-only evidence. Exit code `0` does not authorize
Liquid20 membership, replay, model training, strategy work or trading.

## Verified Synology runner contract

The staging preflight workflow run `30308573877` completed successfully on the
following frozen mapping:

```text
runner name:        freqtrade-synology-staging
routing label:      freqtrade-staging
runner OS:          Linux
GitHub environment: synology-staging
state directory:    /var/lib/freqtrade-staging-state
durable root:       /var/lib/freqtrade-staging-state/okx-liquidation-acceptance
durable URI:        file:///var/lib/freqtrade-staging-state/okx-liquidation-acceptance
```

The 24-hour workflow binds directly to this reviewed mapping. It does not depend
on mutable `OKX_ACCEPTANCE_*` variables.

## Durable-root preparation

The first exact trigger PR `#606` ran workflow `30352834444` and job
`90254107799`. The dedicated runner accepted the job and exact-one-file scope
passed, but validation stopped before credentials, dependency installation or
collector execution because the durable acceptance root was not ready at that
moment. No WebSocket subscription started, no report or raw artifact was
created, and orders remained zero.

The repaired workflow now validates and prepares storage in this order:

1. assert the exact runner name and Linux OS;
2. require the canonical absolute state directory;
3. require the canonical durable root to be directly below that state directory;
4. require the state directory to exist and be writable;
5. create only the missing canonical durable root with `umask 027`;
6. require the durable root to be a writable directory outside runner-temporary
   and workspace paths;
7. perform an atomic write, `fsync`, rename and read-back probe inside a temporary
   child directory;
8. remove the probe directory before any collector dependency or network work.

Named fail-closed markers include:

```text
OKX_ACCEPTANCE_STATE_DIR_MISSING
OKX_ACCEPTANCE_STATE_DIR_NOT_WRITABLE
OKX_ACCEPTANCE_DURABLE_ROOT_CREATE_FAILED
OKX_ACCEPTANCE_DURABLE_ROOT_NOT_WRITABLE
OKX_ACCEPTANCE_DURABLE_ROOT_ATOMIC_IO_FAILED
```

The workflow cannot create an arbitrary path because the durable root must remain
directly below `/var/lib/freqtrade-staging-state` and must equal the frozen
request URI mapping.

## Canonical trigger

Create a new branch from the current `develop` and add exactly:

```text
ai_platform/research/liquidations/run-requests/okx-shadow-acceptance-20260727-v1.json
```

The request must be the only diff and must have this exact operational shape:

```json
{
  "schema_version": 1,
  "request_id": "okx-shadow-acceptance-20260727-v1",
  "run_id": "okx-shadow-acceptance-20260727-v1",
  "host_id": "freqtrade-synology-staging",
  "host_class": "always_on_nonrestricted_linux_staging",
  "github_hosted_runner": false,
  "durable_storage_uri": "file:///var/lib/freqtrade-staging-state/okx-liquidation-acceptance",
  "policy_id": "okx-liquidation-shadow-acceptance-v1",
  "symbols": [
    "BTCUSDT",
    "ETHUSDT"
  ],
  "duration_seconds": 86400,
  "execution_enabled": false,
  "performance_research_authorized": false,
  "replay_authorized": false,
  "model_training_authorized": false,
  "orders_submitted": 0
}
```

The workflow checks that the pull request adds exactly this file, belongs to the
same repository and matches the frozen runner/storage identity. A modified or
repeated request cannot silently reuse an existing output directory.

## Evidence handling

The durable run directory is:

```text
/var/lib/freqtrade-staging-state/okx-liquidation-acceptance/${run_id}
```

It contains:

```text
okx-usdt-swap.ndjson
okx-usdt-swap-summary.json
okx-usdt-swap-instruments.json
okx-shadow-acceptance-manifest.json
okx-shadow-acceptance-report.json
artifact-sha256.txt
```

Only bounded metadata is uploaded as a GitHub artifact. The raw NDJSON remains
on durable Synology storage and is not uploaded by the workflow.

If collection fails before a complete package can be evaluated, the runner
preserves bounded failure evidence. Such evidence is rejected or incomplete;
it is never relabelled as inconclusive.

## Trigger closure and next boundary

After the workflow reaches a terminal outcome:

1. independently verify the durable package;
2. record the exact request head, workflow run, durable URI, sizes and SHA-256
   identities;
3. close the trigger pull request without merge;
4. publish a separate compact repository evidence envelope without raw NDJSON;
5. use a new request identity for any completed collection rerun.

Only an `accepted` package may support a later, separately reviewed source
integration proposal. It still does not authorize Liquid20, replay, models or
trading.
