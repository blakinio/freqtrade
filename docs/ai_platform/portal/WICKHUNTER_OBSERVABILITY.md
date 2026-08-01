# WickHunter Portal Observability v1

## Purpose

WH-08 exposes the frozen WH-07 `PortalObservabilitySnapshot` through an authenticated,
read-only Portal API and dashboard. It does not control the runtime and does not add an exchange
client, credential provider, order adapter, trading action or live-capital authority.

## Producer input

WH-07 atomically publishes `portal-observability-snapshot.json`. Production Portal instances set:

```text
PORTAL_WICKHUNTER_SNAPSHOT_PATH=/absolute/path/to/portal-observability-snapshot.json
```

The configured path must resolve to a regular file and must not be a symbolic link. The reader
limits the file to 2 MiB, parses one JSON object and validates every field against
`wickhunter-portal-observability-snapshot-v1`.

Fixture deployments use:

```text
PORTAL_WEB_DATA_MODE=fixture
```

and read the committed bounded fixture at
`fixtures/wickhunter/portal-observability-snapshot.json`.

## Fail-closed validation

The Portal refuses the snapshot when any of the following is true:

- schema, enum, hash, timestamp, decimal, sorting or identity validation fails;
- the runtime mode is not `research`, `shadow` or `paper`;
- model or parameter identity is incomplete;
- the source path is a symlink, not a regular file or exceeds the size limit;
- the snapshot is too far in the future outside fixture mode;
- `read_only` is not true;
- trading credentials or an order adapter are present;
- submitted orders are not zero;
- live-capital authority is enabled.

Unavailable or rejected evidence returns a sanitized `503` response with `cache-control: no-store`.
No filesystem path or raw invalid snapshot is returned.

## Authorization

`GET /api/market/wickhunter` uses the existing Portal browser-session and tenant authorization
boundary used by Market Evidence. Anonymous sessions receive `401`; unauthorized or cross-tenant
members receive `403`. Successful responses always include `cache-control: no-store`.

## Dashboard

`/market/wickhunter` displays only current accepted state:

- runtime mode, health, snapshot age and circuit-breaker reasons;
- dynamic universe and liquidation-source freshness;
- model, parameter, dataset and code identities;
- validation, retraining and drift state;
- candidate/risk decision summaries and rejection reasons;
- simulated positions, realized/unrealized PnL, equity and drawdown;
- the explicit zero-authority boundary.

The only interactive control is refresh. The page contains no trade, order, submit, execute,
buy or sell control.

## Validation

The bounded Playwright scenario verifies authentication, cross-tenant denial, the fixture fields,
risk rejection visibility, simulated-position visibility, no-store responses, secret/path
redaction, zero-authority fields and absence of trading controls.
