# OKX Shadow Acceptance Staging Preflight v1

## Purpose

Verify the Freqtrade-owned Synology self-hosted GitHub Actions runner and durable state path before creating the canonical 24-hour OKX shadow acceptance request.

The preflight is operationally separate from collection. It performs no WebSocket subscription, liquidation capture, replay, model work, strategy work or trading.

## Freqtrade staging identity

The bounded preflight targets the dedicated runner contract established by the Synology runner-isolation and state-path cutover work:

```text
runner name:        freqtrade-synology-staging
routing label:      freqtrade-staging
GitHub Environment: synology-staging
runner state dir:   /var/lib/freqtrade-staging-state
host state dir:     /volume1/docker/freqtrade/state
```

The workflow continues to enter the protected `synology-staging` environment. The runner-visible state path is not supplied by a mutable GitHub variable: it is the canonical mount point declared by the dedicated runner package, frozen in the exact request and independently verified at runtime.

The future OKX durable root is prospectively mapped to:

```text
/var/lib/freqtrade-staging-state/okx-liquidation-acceptance
```

The corresponding credential-free storage identity is:

```text
file:///var/lib/freqtrade-staging-state/okx-liquidation-acceptance
```

This mapping does not authorize the 24-hour run. The directory must exist through the runner mount, be writable, remain outside workspace and temporary storage, pass the atomic filesystem probe and have sufficient free space.

## Guarded trigger

The workflow is:

```text
.github/workflows/ai-platform-okx-liquidation-shadow-acceptance-staging-preflight.yml
```

It reacts only when a same-repository pull request against `develop` adds exactly:

```text
ai_platform/research/liquidations/run-requests/okx-shadow-acceptance-staging-preflight-20260727-v1.json
```

The request must be the only changed path. Synchronizing or reopening the trigger cancels any stale preflight for the same pull request, so only the newest request HEAD may proceed. The trigger PR is closed without merge after the terminal report is captured.

## Verified properties

The job proves that:

- GitHub scheduled the job through the unique `freqtrade-staging` routing label;
- the actual runner name is `freqtrade-synology-staging`;
- the runner OS is Linux;
- the job passed through the protected `synology-staging` environment;
- the canonical state directory equals the exact request contract, is absolute, exists and is writable;
- the dedicated OKX durable root is directly below the canonical state directory and outside the runner workspace and temporary directory;
- an atomic create, fsync, rename and read-back cycle succeeds under the durable root;
- at least 1 GiB is free;
- the public OKX time and SWAP instrument endpoints are reachable and return OKX code `0`;
- no recognized exchange or Freqtrade trading credential is present;
- no collection or execution occurs.

The bounded artifact contains only the resulting non-sensitive JSON report. It does not contain raw market data.

## What it does not prove

A passing preflight does not itself prove:

- 24-hour WebSocket stability;
- activity, latency or disconnect thresholds;
- accepted OKX source quality;
- immutable snapshot or evidence-retirement enforcement after the run;
- Liquid20 membership;
- replay, model, strategy or trading authorization.

After a passing preflight, the acceptance workflow may be mapped in a separate PR to the verified runner, environment and durable path. The canonical 24-hour request remains a later exact-one-file trigger.
