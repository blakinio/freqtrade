# OKX Shadow Acceptance Staging Preflight v1

## Purpose

Verify the existing Synology self-hosted GitHub Actions runner and durable state path before creating the canonical 24-hour OKX shadow acceptance request.

The preflight is operationally separate from collection. It performs no WebSocket subscription, liquidation capture, replay, model work, strategy work or trading. It exists because the merged acceptance workflow originally declared generic staging names that do not match the established Synology runner configuration.

## Existing staging identity

The bounded preflight targets the runner identity proven by the successful Synology executions recorded in `docs/agents/tasks/FTAI-20260725-portal-synology-lan-staging.md` and workflow run `30205769267`:

```text
runner name:        freqtrade-synology-staging
routing label:      freqtrade-staging
GitHub Environment: synology-staging
state variable:     OTERYN_STAGING_STATE_DIR
expected state dir: /var/lib/oteryn-staging-state
```

The repository runner list proves the unique custom label `freqtrade-staging`. The workflow routes only by that label because GitHub assigns a multi-label `runs-on` job only to a runner that possesses every requested label. After assignment, the probe independently rejects any runner whose exact name is not `freqtrade-synology-staging` or whose `runner.os` is not Linux.

The future OKX durable root is prospectively mapped to:

```text
/var/lib/oteryn-staging-state/okx-liquidation-acceptance
```

The corresponding credential-free storage identity is:

```text
file:///var/lib/oteryn-staging-state/okx-liquidation-acceptance
```

The runner identity and custom label are established by prior terminal Synology evidence. The environment variable and durable path remain prospective until this preflight executes. This mapping does not authorize the 24-hour run.

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

- GitHub scheduled the job through the proven custom `freqtrade-staging` routing label;
- the actual runner name is `freqtrade-synology-staging`;
- the runner OS is Linux;
- the protected `synology-staging` environment exposes the expected state directory;
- the state directory is absolute, existing and writable;
- the dedicated OKX durable root is outside the runner workspace and temporary directory;
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
