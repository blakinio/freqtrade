# AI Trading Portal — Bot Management Product Architecture

## 1. Purpose

Define the product and technical architecture required to evolve the current safe portal foundation into a complete dry-run bot creation and bot-management product.

This document is an additive specialization of `SYSTEM_ARCHITECTURE.md`. It does not replace the portal program, the PI package backlog or the live-capital gates.

The target is functional completeness for:

- creating a bot from approved server-side catalogs;
- configuring entry, sizing, DCA, exit, risk and runtime policies;
- managing bot lifecycle, positions and orders through audited commands;
- receiving authenticated external signals;
- operating specialized dry-run bot families such as directional, DCA, signal and grid bots;
- reconciling every command with authoritative runtime evidence.

## 2. Current boundary

The existing portal already provides:

- tenant-scoped `BotInstance` resources;
- immutable configuration revisions;
- desired-state start, pause and stop commands;
- bot-scoped positions, orders, trades, valuation, risk, logs and audit evidence;
- advisory signal persistence;
- bounded dry-run grid configuration;
- deterministic risk-gated manual intent;
- simulated execution through the deterministic simulator.

The current concrete Freqtrade submission path remains fail-closed with `ORDER_SUBMISSION_NOT_IMPLEMENTED`. Exchange credential brokering, private approved dry-run submission, position/order mutations and advanced bot policy execution remain separate gated work.

## 3. Non-goals and protected boundaries

This architecture does not authorize:

- live capital;
- withdrawal-enabled exchange credentials;
- direct browser access to Freqtrade, an exchange or a secret store;
- copying proprietary third-party code, assets or private captures;
- automatic model promotion;
- automatic strategy promotion from liquidation, signal or AI research evidence;
- bypassing deterministic risk, tenant isolation, audit or reconciliation;
- combining PI-07 credential work and PI-08 execution work into an unreviewed feature package.

Product behavior may be inspired by common trading-automation workflows, but names, schemas, implementation and visual design must remain independently owned.

## 4. Product capability domains

### 4.1 Bot catalog and compatibility

The server owns immutable catalogs for:

- bot templates;
- strategy versions;
- model versions;
- risk policies;
- exchange capabilities;
- supported market types, pairs and timeframes;
- runtime versions;
- supported configuration policy families.

The browser selects catalog entries. It must not type arbitrary internal version identifiers as the primary production workflow.

A compatibility decision is authoritative and versioned:

```text
BotTemplate
  + StrategyVersion
  + ModelVersion | null
  + ExchangeCapabilityProfile
  + MarketPolicy
  + RuntimeVersion
  + RiskPolicyVersion
  -> Compatible | Rejected(reason_codes)
```

### 4.2 Bot configuration composition

A complete bot revision composes immutable policy objects rather than one unstructured JSON object.

Required policy families:

```text
BotConfigRevision
  identity
  template_ref
  strategy_ref
  model_ref | null
  exchange_connection_ref
  market_policy
  entry_policy
  position_sizing_policy
  dca_policy | null
  exit_policy
  risk_policy_ref
  signal_policy | null
  grid_policy | null
  runtime_policy
  execution_mode = dry_run
```

Every policy must have:

- a versioned schema;
- deterministic validation;
- explicit defaults;
- compatibility checks;
- normalized canonical serialization;
- immutable revision attribution;
- no secret values.

### 4.3 Entry and position-sizing policies

The architecture must support bounded configuration for:

- long, short or declared direction policy;
- fixed amount, fixed quote allocation or percentage allocation;
- maximum concurrent positions;
- maximum exposure per pair, bot and tenant;
- optional leverage only where separately authorized and supported;
- cross or isolated margin only where the exchange capability profile allows it;
- entry cooldown and duplicate-signal behavior;
- order-type preferences with server-side exchange compatibility validation.

### 4.4 DCA policy

`DcaPolicyVersion` defines:

- maximum DCA steps;
- trigger basis and spacing;
- order-size schedule or multiplier;
- maximum cumulative allocation;
- cooldown;
- health, liquidity and risk veto behavior;
- whether a command is strategy-driven, signal-driven or manually requested.

A DCA step is always a new `TradeIntent`; it never bypasses current runtime evidence or the risk engine.

### 4.5 Exit policy

`ExitPolicyVersion` may include:

- single take profit;
- multiple take-profit levels with close fractions;
- stop loss;
- trailing stop;
- break-even transition;
- time-based exit;
- strategy exit;
- emergency close behavior.

All exit actions are represented as commands and attributed to the exact bot revision and position evidence used for evaluation.

### 4.6 Signal and webhook control

A complete signal integration owns:

- a tenant-scoped endpoint identity;
- a versioned payload schema;
- HMAC or equivalent signed authentication;
- secret reference only, never a returned secret value;
- timestamp and replay window;
- idempotency key;
- command mapping;
- test/simulator mode;
- delivery and rejection evidence.

Supported command vocabulary is versioned and initially bounded to:

```text
OPEN
DCA
CLOSE_POSITION
PARTIAL_CLOSE
CLOSE_ALL
TAKE_PROFIT
ENABLE_BOT
PAUSE_BOT
STOP_BOT
```

Receiving a valid signal creates an advisory event or a `TradeIntent` according to the endpoint policy. It never creates direct execution authority.

### 4.7 Grid bot policy

`GridPolicyVersion` owns:

- lower and upper bounds;
- level count;
- arithmetic or geometric spacing;
- allocation per level or total allocation;
- direction/mode;
- optional trailing range;
- take-profit and stop behavior;
- volatility or ATR guard where independently validated;
- runtime activation state.

The UI may render a visual preview, but the server produces the canonical levels and validates the final immutable revision.

### 4.8 Bot and runtime operations

Lifecycle commands remain separate from trade commands.

Lifecycle command families:

```text
START
PAUSE_NEW_ENTRIES
RESUME
STOP_KEEP_POSITIONS
STOP_AFTER_EXIT
RESTART_RUNTIME
RETIRE
```

Trade-operation command families:

```text
CLOSE_POSITION
PARTIAL_CLOSE
CLOSE_ALL
CANCEL_ORDER
CANCEL_ALL_ORDERS
REPLACE_ORDER
FORCE_TAKE_PROFIT
```

Every command requires:

- tenant and actor context;
- capability authorization;
- current immutable revision;
- expected desired/observed revision where applicable;
- idempotency key;
- optional step-up MFA according to impact;
- deterministic risk evaluation where exposure changes;
- append-only audit evidence;
- terminal reconciliation status.

### 4.9 Exchange connections and credential boundary

The portal product owns exchange-connection metadata and status. PI-07 owns secret retrieval, injection, rotation and revocation.

The browser may receive:

- connection display name;
- exchange and market type;
- capability status;
- verification result;
- last successful check;
- opaque connection reference;
- rotation/revocation status without secret material.

The browser must never receive an API secret, passphrase, resolved secret-store path or runtime credential.

### 4.10 Performance, dashboard and operational evidence

Bot management requires authoritative views for:

- equity and PNL by bot and revision;
- realized/unrealized separation;
- fees and slippage where authoritative evidence exists;
- drawdown;
- positions and orders;
- command lifecycle;
- exchange health;
- runtime health;
- risk denials;
- stale, partial, unavailable and unreconciled states.

All lists must support bounded pagination, stable ordering, time range and tenant/bot filters before production-like staging acceptance.

## 5. Canonical command flow

```text
Browser
  -> same-origin BFF
  -> product command API
  -> identity / tenant / capability / CSRF / step-up checks
  -> immutable bot-revision and source-evidence resolution
  -> deterministic risk evaluation where required
  -> ApprovedExecutionIntent or lifecycle command
  -> private execution adapter
  -> isolated Freqtrade dry-run runtime
  -> runtime acknowledgement or ambiguous outcome
  -> private collector / reconciliation
  -> operational mirror
  -> audit + event + notification evidence
  -> portal state
```

The initial synchronous response may be `ACCEPTED`, `REJECTED`, `BLOCKED` or `PENDING_RECONCILIATION`. It must not claim execution success solely from an HTTP acknowledgement.

## 6. Canonical domain records

New work should converge on explicit versioned records:

```text
BotTemplateVersion
BotCompatibilityDecision
MarketPolicyVersion
EntryPolicyVersion
PositionSizingPolicyVersion
DcaPolicyVersion
ExitPolicyVersion
SignalPolicyVersion
GridPolicyVersion
RuntimePolicyVersion
BotCommand
PositionCommand
OrderCommand
ExecutionAttempt
ExecutionAcknowledgement
ReconciliationRecord
ExchangeCapabilityProfile
ExchangeConnectionMetadata
```

Shared records belong in `contracts/`. Feature-specific persistence and behavior belong to the owning module.

## 7. Target repository structure

The structure below is an additive target and ownership map. Directories are created only when a bounded task is activated. Existing code must not be moved merely to match this diagram.

```text
ai_platform/portal/
  contracts/
    bot_management/
      templates.py
      compatibility.py
      configuration.py
      policies.py
      commands.py
      exchange_connections.py
      signals.py
      execution.py

  bot_catalog/
    schema.py
    repository.py
    service.py
    compatibility.py

  bot_builder/
    schema.py
    repository.py
    service.py
    normalization.py
    validation.py

  bot_operations/
    schema.py
    service.py
    command_store.py
    lifecycle.py
    position_commands.py
    order_commands.py

  exchange_connections/
    schema.py
    repository.py
    service.py
    verification.py

  signal_control/
    schema.py
    repository.py
    service.py
    authentication.py
    replay.py
    command_mapping.py

  grid_control/
    schema.py
    repository.py
    service.py
    level_generation.py
    validation.py

  execution/
    adapter.py
    freqtrade/
      lifecycle.py
      submission.py
      command_mapping.py
      response_mapping.py
    reconciliation/
      service.py
      repository.py
      state_machine.py

  credential_broker/
    interfaces.py
    policy.py
    redaction.py
    providers/

  control_plane/
    api/
      routers/
        bots.py
        bot_catalog.py
        bot_operations.py
        exchange_connections.py
        signals.py
        grid.py
        terminal.py
    app.py

  web/
    app/
      bots/
        new/
        templates/
        signals/
        grid/
        detail/[botId]/
      operations/
        commands/
      platform/
        exchanges/
    components/
      bot-builder/
      bot-operations/
      exchange-connections/
      signals/
      grid/
    lib/
      api/
      contracts/

  e2e/
    scenarios/
      bot_creation/
      bot_lifecycle/
      signal_commands/
      position_order_commands/
      grid/
      execution_reconciliation/

tests/ai_platform/portal/
  contracts/bot_management/
  bot_catalog/
  bot_builder/
  bot_operations/
  exchange_connections/
  signal_control/
  grid_control/
  execution/
  credential_broker/
  web/
  e2e/
```

## 8. API composition rules

Feature agents must not continue growing one monolithic control-plane API file.

Rules:

1. Each capability owns a router or router factory in its declared module.
2. One integration owner composes routers in the application factory.
3. Public schemas import versioned contracts rather than internal persistence models.
4. Mutations require idempotency and audit semantics in the application service, not only in the BFF.
5. BFF routes translate browser concerns only; they do not reimplement domain validation.
6. No feature router resolves secrets directly.
7. Pagination and filtering contracts are frozen before multiple feature agents implement list endpoints.

## 9. Persistence and migrations

Feature modules own their tables and repositories, but migration sequencing is serialized.

Recommended ownership:

- feature agent proposes schema and migration requirements;
- migration coordinator assigns the next revision and resolves ordering;
- shared contract migration is separate from feature persistence migration;
- destructive migrations require an explicit compatibility and rollback plan;
- command and reconciliation evidence is append-only except for explicit terminal state transitions.

## 10. Security and risk requirements

Every new capability must test:

- cross-tenant denial;
- missing capability denial;
- expired/revoked session denial;
- CSRF denial for browser mutations;
- step-up MFA where required;
- secret exclusion from API, logs, events and audit details;
- replay and duplicate-command handling;
- stale/revision-conflict handling;
- kill-switch behavior;
- unavailable runtime behavior;
- fail-closed behavior when credential, exchange or telemetry sources are missing.

## 11. Execution and reconciliation requirements

PI-08 private dry-run submission is complete only when:

- an approved intent is bound to the exact tenant, bot, config revision, runtime and idempotency key;
- runtime credentials are resolved only through PI-07;
- duplicate delivery cannot create unproven duplicate exposure;
- ambiguous runtime responses remain unresolved until authoritative reconciliation;
- runtime mismatch, degraded health or kill switch blocks submission;
- position/order/trade evidence converges through the operational mirror;
- no browser can address Freqtrade directly;
- dry-run is independently enforced by configuration and runtime verification.

## 12. Test architecture

Each product package adds:

- contract tests;
- service/unit tests;
- persistence/integration tests;
- tenant and capability security tests;
- idempotency and conflict tests;
- deterministic simulator scenarios;
- same-origin BFF tests;
- Playwright user-journey tests;
- unavailable/stale/partial/reconciliation states;
- evidence-preserving failure artifacts.

The final bot-management journey must prove:

```text
real product session
  -> choose compatible template/catalog entries
  -> create immutable dry-run bot revision
  -> provision/start private runtime
  -> receive or create a trade intent
  -> risk approve/reject
  -> submit privately to dry-run runtime
  -> reconcile order/position/trade
  -> perform an audited management command
  -> display PNL, command status and evidence
```

This journey does not authorize live capital.

## 13. Delivery packages and dependencies

Suggested bounded package sequence:

| Package | Outcome | Depends on |
|---|---|---|
| `BM-00` shared bot-management contracts | frozen policy, command, pagination and compatibility contracts | current portal contracts |
| `BM-01` bot catalog and compatibility | authoritative selectable templates and compatibility decisions | BM-00 |
| `BM-02` bot builder and immutable configuration | complete entry/sizing/DCA/exit configuration | BM-00, BM-01 |
| `BM-03` bot operations command model | lifecycle, position and order command persistence/audit | BM-00 |
| `BM-04` signal/webhook control | authenticated, replay-safe command mapping | BM-00, BM-03 |
| `BM-05` grid product capability | canonical grid policy, preview and persistence | BM-00, BM-02 |
| `BM-06` exchange connection product surface | metadata, capability and verification workflow | BM-00 |
| `PI-07` credential broker | secret-safe runtime credential resolution/rotation | security decision and BM-06 |
| `PI-08` private dry-run submission | approved intent submission and reconciliation | PI-07, BM-03, existing risk/audit |
| `BM-07` position/order management activation | close/cancel/replace commands through private execution | PI-08 |
| `BM-08` dashboard and analytics completion | complete bot-management evidence and filters | authoritative runtime/valuation sources |
| `BM-09` product E2E and quality closure | complete browser/API/security journey | all required packages |

No package is active merely because it is listed here. Each requires a dated task, branch, owned paths, acceptance criteria and current repository ownership check.

## 14. Completion definition

Bot creation and management is product-complete for the dry-run milestone only when:

1. users select compatible server-owned catalogs instead of typing internal references;
2. entry, sizing, DCA, exit, risk, signal and optional grid policies are versioned and validated;
3. every material change creates an immutable revision;
4. lifecycle, position and order commands are permission-gated, idempotent and audited;
5. exchange credentials are brokered through PI-07 without browser exposure;
6. approved commands reach only the exact private dry-run runtime through PI-08;
7. ambiguous outcomes reconcile before success is claimed;
8. dashboard, bot detail, positions, orders, trades and command history show authoritative freshness states;
9. real identity, target observability and protected external staging acceptance are proven through their separate gates;
10. live capital remains separately blocked until explicit P14 authorization.
