# OKX Liquidation Staging Readiness Probe v1

## Purpose

Verify the protected staging environment and labelled self-hosted Linux runner before a
24-hour OKX liquidation shadow acceptance request is created.

The probe is deliberately inert. It does not install the collector dependency, connect
to OKX, start collection, authorize execution, submit orders or write into the durable
acceptance directory.

## Workflow

```text
.github/workflows/ai-platform-okx-liquidation-staging-readiness.yml
```

The workflow runs only for a same-repository pull request against `develop` that adds
exactly:

```text
ai_platform/research/liquidations/readiness-requests/okx-liquidation-staging-readiness-20260727-v1.json
```

The request payload is frozen to:

```json
{
  "schema_version": 1,
  "request_id": "okx-liquidation-staging-readiness-20260727-v1",
  "collector_authorized": false,
  "network_probe_authorized": false,
  "execution_enabled": false,
  "orders_submitted": 0
}
```

## Readiness checks

The job requires the same runtime boundary as the 24-hour acceptance workflow:

```text
runs-on: [self-hosted, Linux, okx-liquidation-staging]
environment: okx-liquidation-staging
```

It verifies that:

- `OKX_ACCEPTANCE_HOST_ID`, `OKX_ACCEPTANCE_DURABLE_ROOT` and
  `OKX_ACCEPTANCE_DURABLE_URI` are configured;
- the durable root is an existing writable absolute directory outside the workspace and
  runner temporary directory;
- no recognized exchange or Freqtrade trading credential is present;
- the readiness request is the only pull-request diff.

A job that starts proves an online runner satisfies the required labels. A successful job
also proves the protected environment variables and durable-root checks pass.

## Bounded evidence

The workflow uploads a seven-day convenience artifact containing:

```text
okx-liquidation-staging-readiness.json
okx-liquidation-staging-readiness.sha256
```

The JSON publishes only the already-declared non-sensitive host identity, the
credential-free durable storage URI, runner metadata and boolean readiness results. It
does not publish the durable filesystem root, secrets or environment-variable inventory.

After successful verification, close the readiness request pull request without merge and
create the separate canonical 24-hour acceptance request using the exact `host_id` and
`durable_storage_uri` from the readiness evidence.
