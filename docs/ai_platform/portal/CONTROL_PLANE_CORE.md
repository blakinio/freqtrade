# AI Trading Portal — Control Plane Core

## Scope

P2 implements the first executable Control Plane boundary on top of the P1 contracts. It is intentionally limited to application authorization, tenant-scoped bot metadata, immutable configuration revisions, desired-state commands, append-oriented audit records and a transactional outbox.

It does not implement a concrete Freqtrade adapter, exchange connectivity, secret retrieval, event-bus delivery, live trading or public Freqtrade access.

Canonical implementation path:

```text
ai_platform/portal/control_plane/
```

## Trusted identity boundary

`create_app()` accepts an explicitly configured trusted identity-context provider. The provider supplies a `RequestContext` containing:

- `tenant_id`;
- `actor_id` and actor type;
- explicit P1 permissions;
- `request_id`, `correlation_id` and optional `causation_id`.

When no provider is configured, protected Control Plane routes return `401` and fail closed. The implementation does not derive trusted application identity from arbitrary browser-supplied tenant, actor or role headers.

Cloudflare Access remains defense in depth. Application identity and permission checks remain mandatory inside the Control Plane.

## HTTP surface

P2 exposes only modular portal Control Plane routes:

```text
POST /v1/bots
GET  /v1/bots
GET  /v1/bots/{bot_id}
POST /v1/bots/{bot_id}/revisions
POST /v1/bots/{bot_id}/desired-state
```

There is no route for raw Freqtrade REST/WebSocket access, exchange credential values, runtime addresses or live-capital activation.

The application is provided as a FastAPI factory. P2 does not start or deploy a production server.

## Tenant isolation and permissions

Every repository lookup and mutation includes `tenant_id` from the trusted `RequestContext`. A bot with the same `bot_id` in a different tenant is not visible through another tenant's repository, service or HTTP boundary.

Capabilities are evaluated server-side with the P1 fail-closed permission model:

| Operation | Required permission |
| --- | --- |
| create bot | `bot.create` |
| list/read bot | `bot.read` |
| create immutable config revision | `bot.create` |
| request running desired state | `bot.start` |
| request paused desired state | `bot.pause` |
| request stopped desired state | `bot.stop` |

P1 does not define a separate `bot.configure` permission. P2 therefore treats creation of a new immutable configuration identity as the existing `bot.create` capability rather than inventing a private downstream permission. A future permission split requires a shared-contract change.

Missing or unknown permissions grant no access.

## Persistence model

P2 defines SQLAlchemy metadata for four tenant-aware persistence surfaces:

- `portal_bots` — current bot metadata and current immutable spec pointer;
- `portal_bot_config_revisions` — append-only configuration revision identities;
- `portal_audit_events` — append-oriented privileged-operation evidence;
- `portal_outbox_events` — durable domain-event envelope storage for later publication.

The initial PostgreSQL-compatible migration is:

```text
ai_platform/portal/control_plane/migrations/0001_control_plane.sql
```

The bot primary key is `(tenant_id, bot_id)`. Configuration revisions use `(tenant_id, bot_id, revision)` with an additional tenant-scoped unique `revision_id`. Outbox `event_id` and audit `audit_id` are unique identities.

P2 does not select the final production migration runner or database deployment topology.

## Immutable configuration revisions

Bot creation requires `config_revision = 1` and atomically persists:

1. the `BotInstance`;
2. revision 1 as `BotConfigRevision`;
3. a `bot.created` audit event;
4. a `bot.created` outbox event.

A material configuration change must supply the next monotonically increasing revision number. P2 inserts a new immutable revision row and moves only the bot's current spec pointer. Existing revision rows are never updated in place.

Concurrent duplicate revision identities are rejected by database uniqueness constraints and surfaced as conflicts.

## Desired versus observed state

P2 changes desired intent only.

```text
Control Plane command
  -> desired_state update
  -> *_requested audit event
  -> *_requested outbox event
```

The corresponding observed runtime state is not changed by P2. In particular:

- `bot.start_requested` is not `bot.started`;
- `bot.pause_requested` is not `bot.paused`;
- `bot.stop_requested` is not `bot.stopped`.

Observed-state transitions belong to the later Execution Adapter/runtime reconciliation boundary.

## Transactional audit and outbox

Each state-changing service operation writes its domain mutation, `AuditEvent` and `EventEnvelope` outbox row in one SQLAlchemy transaction. An outbox or audit write failure rolls back the domain mutation.

The outbox is storage only in P2. Publication, retry, idempotent consumers, replay infrastructure and observability pipelines remain P4 scope.

Correlation identity from the trusted request context is copied into audit and outbox contracts so later traces can preserve:

```text
Browser
  -> Portal API
  -> Control Plane
  -> Risk Engine
  -> ExecutionAdapter
  -> Freqtrade
```

## Security invariants

P2 preserves the program boundaries:

- no public Freqtrade API or WebSocket;
- no Freqtrade or exchange credential values in browser-facing contracts;
- no test-only authorization bypass endpoint;
- no live-capital activation;
- no withdrawal capability;
- no research access to production credentials;
- no direct model-to-execution bypass;
- no autonomous production patching.

Frozen AI research state is untouched: thresholds `0.006/-0.009`, protected holdout `20260801-20260930`, no final evaluation before `2026-10-01 UTC`, completed Phase 6 and authoritative `selected_model = null`.
