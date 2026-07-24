# AI Trading Portal — Execution Adapter

## Scope

P3 implements the first concrete private execution boundary behind the P1 `ExecutionAdapter` protocol. PI-01 adds the first authoritative read-only private runtime path for open positions, orders and trades while preserving the operational mirror as the only portal-facing read boundary.

The implementation provides deterministic runtime identity, isolated per-bot workspaces, dry-run-only configuration enforcement, a Docker CLI runtime driver, explicit lifecycle/health mapping and a separately versioned private collector/read-batch interface.

PI-01 does not expose Freqtrade to browser-facing code, publish runtime ports, retrieve exchange credentials, enable live capital or implement order submission.

Canonical implementation paths:

```text
ai_platform/portal/execution/
ai_platform/portal/operations/
```

## One bot to one runtime

Runtime identity is deterministic from the tuple:

```text
(tenant_id, bot_id)
```

The external runtime identifier is a SHA-256-derived opaque value. Tenant and bot values are not placed directly into Docker labels.

Each runtime receives one isolated workspace:

```text
<workspace-root>/<runtime-id>/
  config.json
  runtime-manifest.json
```

`runtime-manifest.json` stores only private operational metadata needed to verify tenant/bot identity, immutable config revision, image/strategy identity, configuration hash, correlation context and the latest machine-readable driver error code. It stores no exchange credential values or private collector endpoint.

## Artifact resolver boundary

`RuntimeArtifactResolver` is injected into `FreqtradeExecutionAdapter` and resolves a `BotInstance` to:

- a Freqtrade runtime image;
- a strategy name;
- a non-secret base configuration.

P3 intentionally does not choose the final artifact registry, deployment controller or exchange-connection metadata provider. Those remain replaceable integration decisions.

The resolver cannot bypass P3 safety policy. Before a runtime configuration is written, P3:

1. rejects credential-bearing configuration fields;
2. requires non-secret `exchange.name` metadata;
3. forces `dry_run = true`;
4. forces `api_server.enabled = false`;
5. forces `telegram.enabled = false`;
6. pins the pair whitelist, timeframe, stake currency and dry-run wallet from the immutable `BotSpec`.

P3 accepts only `ExecutionMode.DRY_RUN`. `simulated` belongs to the P10a exchange simulator and live-capital execution is not represented by the P1/P3 contract.

## Immutable runtime revision

A provisioned runtime record pins:

- `tenant_id` and `bot_id`;
- deterministic `runtime_id`;
- `config_revision`;
- runtime image;
- strategy name;
- SHA-256 of canonical runtime configuration.

Provisioning the same bot/revision is idempotent when those identities remain unchanged.

Changing config revision, image, strategy identity or generated runtime configuration is rejected. P3 does not silently mutate a provisioned immutable revision. A later orchestration work package must define explicit teardown/recreate or replacement-runtime semantics.

## Private Docker boundary

`DockerCliRuntimeDriver` uses argument-array subprocess execution and never invokes a shell.

Provisioning creates a container with:

- deterministic private runtime name;
- private correlation/request labels;
- hashed tenant/bot labels;
- one bind mount for the bot-specific workspace;
- no `-p`, `--publish` or `--publish-all` option;
- fixed Freqtrade config path inside `/freqtrade/user_data`.

The driver implements private lifecycle operations using Docker create/start/unpause/pause/stop/inspect. No public Freqtrade REST or WebSocket route is introduced.

## Desired runtime lifecycle

P3 maps driver state to the P1 observed-state vocabulary:

| Driver state | Observed state |
| --- | --- |
| missing | `ERROR` |
| created | `CREATED` |
| restarting | `STARTING` |
| running | `RUNNING` |
| paused | `PAUSED` |
| exited/dead | `STOPPED` |

Start, pause and stop operations are idempotent at the driver boundary. A pause request against a non-running created/stopped runtime does not fabricate a `PAUSED` state.

## Private runtime read boundary

PI-01 keeps the shared `ExecutionAdapter` v1 protocol unchanged. The tuple-returning v1 query methods cannot represent page completeness, freshness or source availability, so PI-01 introduces a separately versioned private collector/read-batch interface.

The collector is injected server-side into `FreqtradeExecutionAdapter`. It is not a browser, BFF or public-ingress interface.

Each request is scoped by:

- `tenant_id`;
- `bot_id`;
- `source_runtime_id`;
- read kind: open positions, orders or trades;
- bounded page size and timeout;
- opaque pagination cursor.

Every returned page must echo the same tenant, bot, runtime and read kind. Any mismatch fails closed before ingestion.

The collector preserves:

- source position/order/trade identity;
- source update and observation timestamps;
- portal observation and last-reconciled timestamps;
- batch completeness;
- `CURRENT`, `STALE`, `PARTIAL` or `SOURCE_UNAVAILABLE` freshness;
- `SYNCED`, `PENDING`, `SOURCE_UNAVAILABLE` or `MISMATCH` reconciliation status;
- deterministic reason codes without private endpoint or credential details.

Bounded behavior includes:

- per-request timeout;
- retry only for explicitly retryable transport failures;
- maximum page count and response body size;
- duplicate suppression for identical source records;
- `MISMATCH` for conflicting duplicate identities;
- `PARTIAL` for mid-pagination failure or invalid pagination;
- `STALE` when the source observation exceeds the configured age threshold;
- `SOURCE_UNAVAILABLE` when no authoritative source page can be read.

The v1 adapter getters return records only for complete, `CURRENT`, `SYNCED` results. Stale, partial, unavailable or mismatched reads raise deterministic runtime-read errors and never fall back to fixtures or fabricated records.

## Operational mirror and reconciliation

The portal-facing boundary remains the tenant-scoped operational mirror. Private transport details never enter portal serialization.

PI-01 reconciliation:

- upserts records idempotently by deterministic runtime/source identity;
- preserves source IDs and timestamps;
- removes absent open positions only after a complete, current, synced source read;
- retains missing historical orders/trades and marks them `MISMATCH` rather than deleting evidence;
- preserves existing records while marking them stale, partial or source-unavailable after a degraded read;
- marks unattributed runtime orders and incomplete closed-trade outcomes as `MISMATCH`;
- persists one source status per tenant, bot, runtime and read kind.

`GET /v1/runtime-evidence` exposes only normalized operational evidence and explicit freshness/reconciliation metadata. It does not expose runtime URLs, authorization headers, exchange credentials, private collector configuration or secret-bearing payloads.

## Health and deterministic failures

Driver failures carry machine-readable reason codes such as:

```text
DOCKER_CREATE_FAILED
DOCKER_START_FAILED
DOCKER_PAUSE_FAILED
DOCKER_STOP_FAILED
DOCKER_INSPECT_FAILED
DOCKER_STATE_UNKNOWN
RUNTIME_MISSING
```

A lifecycle driver failure returns `RuntimeStatus(observed_state=ERROR)` and persists the reason code in the private runtime manifest. `get_health()` reports the persisted failure as `UNHEALTHY` until a successful lifecycle/status observation clears it.

Healthy-state mapping is:

- running: `HEALTHY`;
- created/starting/paused/stopped: `DEGRADED` with an explicit reason code;
- missing or driver failure: `UNHEALTHY`.

Runtime read failures use stable reason codes for missing/not-ready runtime, collector unavailable, authentication failure, timeout, malformed/oversized response, invalid pagination, stale source and reconciliation mismatch. Error serialization excludes private URLs, authorization headers and response bodies.

## Correlation

Provisioning propagates P1 correlation identity into private Docker labels and the runtime manifest:

```text
request_id
correlation_id
causation_id
```

Raw tenant and bot identifiers are represented in Docker labels only as short SHA-256-derived hashes. The private manifest retains authoritative tenant/bot identity for server-side isolation checks.

## Fail-closed trading boundary

`submit_approved_intent` still raises `UnsupportedExecutionOperationError` with `ORDER_SUBMISSION_NOT_IMPLEMENTED`.

`get_open_positions`, `get_orders` and `get_trades` are functional only through the private collector and only for complete/current/synced evidence. Missing runtime, cross-tenant/cross-runtime scope, authentication failure, timeout, partial pagination, stale source or mismatch never produces a fabricated successful result.

This preserves the deterministic risk-approved execution boundary. PI-01 adds no execution command path.

## Validation

PI-01 validation covers:

- adapter read success;
- missing runtime and collector;
- authentication failure and timeout;
- pagination and partial-page failure;
- identical and conflicting duplicate identities;
- stale source and source unavailable;
- tenant and runtime isolation;
- secret-bearing payload rejection and error redaction;
- idempotent operational reconciliation;
- missing-history and outcome mismatch behavior;
- API/OpenAPI freshness representation;
- browser-safe serialization with no private endpoint or credential fields;
- unchanged fail-closed `submit_approved_intent` behavior.

## Security invariants preserved

- no upstream `freqtrade/` core modification;
- no public Freqtrade REST/WebSocket port;
- no browser-facing Freqtrade credential or endpoint path;
- no raw exchange credential persistence;
- no production-secret retrieval or brokering;
- no withdrawal capability;
- no live-capital execution mode;
- no execution command submission;
- no model-to-execution bypass;
- no protected-holdout evaluation or Phase 6 changes;
- frozen thresholds `0.006/-0.009` and authoritative `selected_model = null` remain untouched.

## Remaining limitations

PI-01 does not implement:

- execution command submission;
- credential brokering or rotation;
- public Freqtrade REST or WebSocket exposure;
- current-price valuation or unrealized PNL;
- live-capital activation;
- P14 or any promotion-policy change.

Private collector endpoint discovery and authorization delivery remain deployment-owned private configuration. They must be provided without making the endpoint or credential portal-facing.
