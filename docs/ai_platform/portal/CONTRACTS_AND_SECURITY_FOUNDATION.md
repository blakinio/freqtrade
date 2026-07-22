# AI Trading Portal — Contracts and Security Foundation

## Scope

P1 establishes the first machine-readable shared contract boundary for the AI Trading Portal. It intentionally implements schemas and fail-closed policy helpers only; it does not implement the Control Plane runtime, Freqtrade integration, database/event infrastructure, public API, web portal, Cloudflare deployment or live-capital activation.

Canonical implementation paths:

```text
ai_platform/portal/contracts/
ai_platform/portal/security/
tests/ai_platform/portal/
```

All contracts inherit a `contract_version = "v1"` field, reject unknown fields and are frozen Pydantic v2 models. Business timestamps require timezone-aware values and are normalized to UTC. `canonical_json()` provides stable key-sorted compact JSON for fixtures, hashing and contract comparisons.

## Identity, tenancy and authorization

Tenant-owned contracts carry a required non-empty `tenant_id`. The v1 vocabulary includes:

- `Tenant`, `Organization`, `User`, `Actor`, `ServiceIdentity`, `Role`;
- actor types `user`, `service`, `agent`, `system`;
- base roles `user`, `trader`, `analyst`, `model_reviewer`, `admin`, `service`;
- explicit permission values such as `bot.start`, `trade.manual_execute`, `model.promote`, `risk.manage` and `admin.manage`.

Authorization helpers evaluate permissions, not frontend visibility or hardcoded page access. Unknown roles, unknown permissions and missing permissions grant nothing. Built-in roles only provide deterministic default permission sets; downstream application code must authorize the effective permission set server-side for every protected action.

## Environment and capital boundary

The v1 environment enum is closed to:

```text
research
test
staging
production
```

The initial execution-mode contract deliberately exposes only:

```text
simulated
dry_run
```

There is no live-capital execution mode in P1. Introducing one requires a later separately reviewed contract/work package.

`EnvironmentContext` carries tenant, environment, workload plane and execution mode. The secret-access policy requires exact tenant and environment match and denies production secret access to research, model-training and test/E2E workload planes.

## Secret references and exchange connections

`SecretRef` is opaque and contains only:

- provider;
- reference identity;
- secret version;
- environment;
- tenant identity;
- secret kind.

`ExchangeConnection` stores a `SecretRef`, never credential values. Pydantic `extra="forbid"` rejects undeclared raw credential fields. The exchange connection and secret reference must match tenant and environment, and withdrawal-enabled credentials are structurally rejected in the v1 contract.

The provider remains intentionally replaceable; Vault/KMS selection is outside P1.

## Bot contracts

P1 defines:

- `BotSpec`;
- `BotInstance`;
- `BotConfigRevision`;
- `BotDesiredState`;
- `BotObservedState`.

Desired and observed state are distinct. `BotSpec` pins tenant, strategy/model/risk versions, exchange connection reference, pair universe, timeframe, capital allocation, runtime version, config revision, environment and execution mode.

`BotConfigRevision` is immutable. Promoted revisions therefore cannot be edited in place; a material change must create a new revision identity.

## AI and model identity

P1 defines:

- `ModelFamily`;
- `ModelVersion`;
- `ModelLifecycleState`;
- `FeatureSchemaVersion`;
- `DatasetVersion`;
- `TrainingPipelineVersion`;
- `ExperimentReference`;
- `TrainingWindow` and canonical `ModelParameter` values.

`ModelVersion` pins model family, artifact identity and SHA-256, feature schema, dataset, training window, training pipeline, parameters, Git revision, creation timestamp and lifecycle state.

Changing identity-defining inputs creates a new immutable object. P1 does not implement lifecycle transitions or automatic promotion. Training and promotion remain separate actions.

Existing AI research boundaries remain unchanged: frozen thresholds `0.006/-0.009`, protected final holdout `20260801-20260930`, no final evaluation before `2026-10-01 UTC`, completed Phase 6 and authoritative `selected_model = null`.

## Deterministic risk gate

The shared flow is frozen as:

```text
Prediction
  -> TradeIntent
  -> RiskDecision
  -> ApprovedExecutionIntent | RejectedExecutionIntent
  -> ExecutionAdapter (approved only)
```

`RiskDecision` requires a risk-policy version, decision result, reason codes, evaluated limits, UTC timestamp and correlation context.

`ApprovedExecutionIntent` validates that:

- the decision is `APPROVED`;
- tenant identity matches across intent and decision;
- the decision references the same trade intent;
- the correlation ID propagates across intent, decision and execution intent.

A rejected decision cannot construct an approved execution intent.

## Execution adapter boundary

`ExecutionAdapter` is a private internal protocol with the following v1 operations:

- `provision_bot`;
- `start_bot`;
- `pause_bot`;
- `stop_bot`;
- `get_health`;
- `get_runtime_status`;
- `submit_approved_intent`;
- `get_open_positions`;
- `get_orders`;
- `get_trades`.

The submit operation accepts `ApprovedExecutionIntent`, not `TradeIntent`. No Freqtrade REST/WebSocket address, credential or browser-facing control contract is present.

The concrete Freqtrade adapter belongs to P3.

## Events

`EventEnvelope` v1 contains:

- event ID/type/version;
- UTC occurrence time;
- tenant and actor identity;
- request/correlation/causation identity;
- aggregate type/ID;
- payload.

Defined event types include bot lifecycle, prediction, trade intent, risk decision, order/trade lifecycle, model lifecycle and insight creation events required by P1. The additive P2 contract change also distinguishes control-plane command intent from observed runtime outcomes with `bot.config_revised`, `bot.start_requested`, `bot.pause_requested` and `bot.stop_requested`; these request/configuration events must not be interpreted as proof that a runtime already started, paused or stopped.

The envelope is suitable for later outbox, idempotency, replay and observability work. P1 does not implement the event bus. Public event payload validation fails closed on keys representing raw secret/password/token/key values.

## Audit

`AuditEvent` is immutable and append-oriented. It records who, what, when, tenant, resource, action, result, request/correlation/causation identity and optional reason/details.

The privileged action vocabulary covers:

- exchange connection changes;
- bot creation and immutable configuration revision;
- bot start/pause/stop requests separately from observed start/stop outcomes;
- manual trade intent;
- risk policy changes;
- model promotion;
- role/permission changes;
- kill-switch activation/release.

Audit detail payloads use the same sensitive-field guard as event payloads.

## Correlation and observability identity

`CorrelationContext` carries:

```text
request_id
correlation_id
causation_id
```

These identifiers are propagated through trade intent, risk decision and approved/rejected execution intent. Event and audit envelopes expose the same identity fields directly. This supports the future trace:

```text
Browser
  -> Portal API
  -> Control Plane
  -> Risk Engine
  -> ExecutionAdapter
  -> Freqtrade
  -> Trade
  -> Post-Trade Intelligence
```

OpenTelemetry transport/instrumentation remains P4 scope; P1 only freezes compatible domain identity.

## Versioning and change policy

P1 is the shared-contract serialization point for downstream workstreams. After merge:

- P2 may own `control_plane/**`;
- P3 may own `execution/**`;
- P4 may own `events/**` and `observability/**`;
- P5 may own `model_control/**`;
- P10a may own simulator core.

A downstream workstream that discovers an incompatible shared-contract requirement must stop redefining schemas locally and use the contract-change protocol in `AGENT_EXECUTION_PLAN.md`.

## Security invariants preserved

- Cloudflare/Zero Trust is defense in depth, not application authorization.
- No public/browser path to Freqtrade is introduced.
- No exchange or Freqtrade secret value is represented in public/domain contracts.
- No withdrawal permission is allowed by the exchange connection contract.
- Research/training/E2E cannot access production secret references.
- AI output cannot bypass deterministic risk approval.
- No test-only security bypass exists.
- No live-capital activation or autonomous production patching is introduced.
