# Portal WickHunter Market Evidence read model

## Scope

The Market Evidence surface is a tenant-safe, read-only projection of durable WickHunter market-evidence runs. It is separate from exchange acquisition and does not proxy private exchange APIs.

The page is available at:

```text
/market/evidence
```

The same existing Portal identity, RBAC and tenant-isolation boundary applies to the page and every API route.

## Data boundary

The server reads the configured durable root:

```text
PORTAL_MARKET_EVIDENCE_DATA_ROOT=<container-visible read-only root>
```

In fixture mode only, the default is:

```text
ai_platform/portal/web/fixtures/market-evidence
```

Production and staging deployments must set an explicit container path. The host path is never returned by an API.

The read model accepts either layout:

```text
<root>/<run-id>/...
```

or:

```text
<root>/runs/<run-id>/...
```

An active pointer may exist at:

```text
<root>/active-wickhunter-production-market-evidence-v1.json
```

The reader:

- resolves fixed child paths beneath the configured root;
- rejects symlinked roots, runs, files and intermediate package-member directories;
- accepts only versioned run-ID patterns;
- bounds metadata, NDJSON, run count and response page size;
- verifies the v1 or v2 manifest self-hash, checksum index, every declared artifact SHA-256 and byte size, package/request/binding identities, completion state, authority boundary and declared row geometry before parsing normalized rows;
- projects normalized rows only from the immutable byte buffers that passed verification, preventing a second unverified file read;
- reads normalized package rows, not raw exchange payloads;
- validates all authority fields before returning a completed run.

Any incomplete, corrupt, substituted, escaping or symlinked completed package fails closed as Market Evidence unavailable. The reader does not return rows from a partially verified package and does not fall back to unverified v1 or v2 content.

## API

All responses use `cache-control: no-store`.

### Summary

```http
GET /api/market/evidence/summary
```

Returns:

- global status;
- last update;
- active run ID;
- latest immutable run ID;
- capture start and end;
- pre-roll;
- completeness;
- instrument, completed-candle and quality-observation counts;
- gap count and duration;
- WH-01 readiness and exact blocker;
- request, policy, code and manifest identities;
- false authority boundary.

### Source status

```http
GET /api/market/evidence/sources
```

Returns one row for each source:

```text
binance-usdm
bybit-linear
okx-swap
```

The route overlays the existing Liquid20 health model on immutable market-evidence metadata. This makes liquidation availability visible without claiming that liquidation availability is equivalent to WH-01 candle evidence.

Each source returns:

- connection and health state;
- last event, ticker and completed candle;
- freshness;
- active symbol count;
- bounded errors;
- reconnect count;
- gaps and records written;
- required scope;
- separate liquidation, candle, market-quality and instrument-history capabilities;
- WickHunter availability;
- exact exclusion reason.

OKX returns `OKX_CANDLE_EVIDENCE_NOT_CONFIGURED` while it remains liquidation-only.

### Instruments

```http
GET /api/market/evidence/instruments
```

Supported query parameters:

| Parameter | Values |
| --- | --- |
| `source` | `all`, `binance-usdm`, `bybit-linear`, `okx-swap` |
| `symbol` | uppercase alphanumeric search term |
| `market` | exact market identity |
| `active` | `true`, `false` |
| `included` | `true`, `false` |
| `quality` | `healthy`, `degraded`, `stale`, `unavailable` |
| `sort` | `symbol`, `source`, `spread`, `volume`, `freshness` |
| `direction` | `asc`, `desc` |
| `page` | positive integer |
| `page_size` | 1 through 100 |

The response includes normalized source-separated instruments only. Raw exchange catalogue payloads are not exposed.

### Runs

```http
GET /api/market/evidence/runs
```

Supported parameters:

```text
page
page_size
```

The response contains active and immutable runs with:

- interval and pre-roll;
- completeness;
- source coverage;
- record counts;
- gaps;
- verification result;
- shortened identities for display;
- WH-01 eligibility and reason codes.

## Status derivation

| Status | Meaning |
| --- | --- |
| `LIVE` | active evidence is fresh or WH-01 is fully ready |
| `DEGRADED` | a verified projection contains a quality or verification problem |
| `STALE` | active acquisition has not updated within the configured freshness threshold |
| `BLOCKED` | immutable market evidence is valid but WH-01 requirements are incomplete |
| `UNAVAILABLE` | no safe active or immutable evidence can be projected |

The default stale threshold is 15 minutes and may be changed with:

```text
PORTAL_MARKET_EVIDENCE_STALE_MS
```

The variable must be a positive safe integer.

## UI

The page contains:

1. status and WH-01 readiness bar;
2. exact blocker detail;
3. active and immutable run metrics;
4. separate source cards for Binance USD-M, Bybit Linear and OKX Swap;
5. searchable, sortable, filterable and paginated instrument table;
6. run table and immutable identity detail;
7. loading, empty, stale, unavailable and error states.

Source cards explicitly separate:

- liquidation feed;
- completed-candle evidence;
- market-quality evidence;
- instrument history;
- WickHunter eligibility.

The page has no trade, order, execution, dataset-acceptance or evidence-mutation action.

## Error contract

Invalid query values return:

```json
{
  "code": "MARKET_EVIDENCE_QUERY_INVALID"
}
```

with HTTP 422.

Unavailable or unsafe durable data returns:

```json
{
  "code": "MARKET_EVIDENCE_UNAVAILABLE"
}
```

with HTTP 503. The response does not include the host path or parser detail.

Unexpected server failures return:

```json
{
  "code": "MARKET_EVIDENCE_READ_FAILED"
}
```

with HTTP 500.

Existing identity errors remain authoritative, including unauthenticated and cross-tenant denial responses.

## Bounded response policy

The reader applies these hard bounds:

- metadata file: 8 MiB;
- normalized NDJSON file: 32 MiB;
- normalized NDJSON rows: 20,000 per file;
- run directories: 50;
- instrument or run page size: 100;
- source errors: 20 returned per source;
- string-array reason data: 50 entries.

These bounds prevent the Portal from becoming a raw evidence download endpoint.

## Deployment

The Synology preview script mounts:

```text
/liquid20-data:ro
/market-evidence-data:ro
```

and sets:

```text
PORTAL_LIQUIDATIONS_DATA_ROOT=/liquid20-data
PORTAL_MARKET_EVIDENCE_DATA_ROOT=/market-evidence-data
```

The script checks group readability, runs a candidate container, authenticates through the fixture preview identity, probes the page and all APIs, checks bounded payloads and rejects host-path or secret-like content before replacing the existing preview.

## Tests

The critical browser flow covers:

```text
identity boundary
→ page open
→ three source cards
→ instrument filtering
→ run detail
→ WH-01 blocker
→ absence of trading controls
```

Additional component-state coverage verifies loading, empty, unavailable, stale and API-error rendering. API assertions cover pagination, query rejection, cross-tenant denial, bounded payloads and absence of host paths or secrets.

Focused integrity coverage additionally verifies valid v1/v2 compatibility, manifest and artifact identity failures, missing or inconsistent checksums, normalized-row substitution, row-count mismatch, unsafe logical paths, symlink components and fail-closed no-partial-row behavior.
