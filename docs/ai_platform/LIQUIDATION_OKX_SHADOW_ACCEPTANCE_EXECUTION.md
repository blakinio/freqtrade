# OKX Shadow Acceptance Execution Infrastructure v1

## Purpose

Implement the inert runner, independent evaluator and guarded self-hosted workflow for
the prospectively frozen policy in
`okx-liquidation-shadow-acceptance-policy-v1.json`.

This infrastructure does not contain the canonical operational request and cannot start
the 24-hour run by itself. It does not add OKX to `liquid20-v1`, authorize replay or
model work, or provide order authority.

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

The runner reuses the isolated public OKX collector. It writes an immutable instrument
snapshot, captures start and end clock probes, collects the declared symbols, writes a
self-hashed manifest, evaluates every frozen gate, writes a self-hashed report and
creates `artifact-sha256.txt` over the five evidence files.

The independent evaluator does not rewrite evidence. It recomputes the report from the
manifest, raw NDJSON, summary and instrument snapshot, verifies the stored report is
identical, checks the report self-hash and verifies all checksum-index entries.

## Outcome and exit-code contract

```text
0  accepted
1  rejected or incomplete evidence
2  inconclusive_insufficient_activity
```

`inconclusive_insufficient_activity` is produced only when every non-activity gate
passes and one or more of the frozen event, observed-symbol or latency-sample minimums
fail. Any identity, safety, clock, health, normalization, latency-quality or artifact
failure produces `rejected`.

All outcomes remain research-only evidence. Even exit code `0` does not authorize
Liquid20 membership, replay, model training, strategy work or trading.

## Self-hosted runner contract

The workflow runs only on a runner carrying these labels:

```text
self-hosted
Linux
okx-liquidation-staging
```

Configure the protected GitHub environment `okx-liquidation-staging` with repository or
environment variables:

```text
OKX_ACCEPTANCE_HOST_ID
OKX_ACCEPTANCE_DURABLE_ROOT
OKX_ACCEPTANCE_DURABLE_URI
```

Requirements:

- `OKX_ACCEPTANCE_HOST_ID` is the exact non-sensitive identity of the intended host;
- `OKX_ACCEPTANCE_DURABLE_ROOT` is an existing writable absolute directory outside the
  runner workspace and temporary directory;
- `OKX_ACCEPTANCE_DURABLE_URI` is the credential-free immutable storage URI published
  in the request and manifest;
- the runner environment contains no recognized exchange or Freqtrade trading
  credentials;
- the durable root is covered by the host's immutable retention or snapshot policy.

A GitHub-hosted runner cannot satisfy the labels or durable-storage checks.

## Canonical trigger

After this infrastructure is merged, create a new branch from the then-current
`develop` and add exactly:

```text
ai_platform/research/liquidations/run-requests/okx-shadow-acceptance-20260727-v1.json
```

The request must be the only diff and must declare the exact host configuration. The
expected shape is:

```json
{
  "schema_version": 1,
  "request_id": "okx-shadow-acceptance-20260727-v1",
  "run_id": "okx-shadow-acceptance-20260727-v1",
  "host_id": "<OKX_ACCEPTANCE_HOST_ID>",
  "host_class": "always_on_nonrestricted_linux_staging",
  "github_hosted_runner": false,
  "durable_storage_uri": "<OKX_ACCEPTANCE_DURABLE_URI>",
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

The workflow checks that the pull request adds exactly this one file, that request host
and durable-storage identity match the protected environment variables, and that the
branch belongs to the same repository. A modified or repeated request cannot silently
reuse an existing output directory.

## Evidence handling

The durable directory is:

```text
${OKX_ACCEPTANCE_DURABLE_ROOT}/${run_id}
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

The workflow uploads only bounded metadata evidence for convenience. It deliberately
does not upload the raw NDJSON as the durable authority. The configured immutable URI
and actual raw file identity remain authoritative.

If collection fails before a complete package can be evaluated, the runner preserves a
bounded failure manifest and all artifacts already produced. Such evidence is rejected
or incomplete; it is never relabelled as inconclusive.

## Trigger closure and next boundary

After the workflow reaches a terminal outcome:

1. independently verify the durable package on the staging host;
2. record the exact request head, workflow run, durable URI, file sizes and SHA-256
   identities;
3. close the trigger pull request without merge;
4. publish a separate compact repository evidence envelope without raw NDJSON;
5. create a new request identity for any rerun.

Only an `accepted` package may support a later source-integration research proposal.
That later proposal remains separately reviewed and may still reject Liquid20
membership or any replay/model use.
