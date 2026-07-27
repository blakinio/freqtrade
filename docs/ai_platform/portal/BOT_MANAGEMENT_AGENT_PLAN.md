# AI Trading Portal — Bot Management Agent Plan

## 1. Purpose

Provide a bounded ownership and sequencing plan for implementing `BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md` with multiple autonomous agents without allowing shared-contract drift, migration conflicts or unsafe execution shortcuts.

This plan extends `AGENT_EXECUTION_PLAN.md`. Global rules, protected research boundaries, branch/PR discipline and context-checkpoint requirements remain authoritative.

## 2. Can multiple agents work in parallel?

Yes, but not from the first commit and not on the same paths.

Recommended model:

1. one lead contract/integration agent freezes shared schemas and the composition seams;
2. after that merge, four to six feature agents work in parallel on disjoint modules;
3. one integration owner serializes shared API registration, migrations, documentation status and final E2E convergence;
4. PI-07 credential activation precedes PI-08 real private dry-run submission;
5. live capital remains outside all workstreams.

Using one agent for the entire program is possible but inefficient. Running many agents without a contract lead and path ownership is unsafe and will produce conflicting schemas, migrations and BFF behavior.

## 3. Recommended concurrency

Practical concurrency after BM-00:

- **minimum:** 3 agents;
- **recommended:** 5–6 agents;
- **maximum without additional coordination:** 7 agents.

Above seven concurrent agents, the shared integration overhead around contracts, migrations, `control_plane` composition, BFF routes and E2E usually outweighs the speed gain.

## 4. Mandatory lead and integration roles

### 4.1 Contract lead

Only the contract lead may modify shared bot-management contracts while BM-00 is active.

Owned paths:

```text
ai_platform/portal/contracts/bot_management/**
tests/ai_platform/portal/contracts/bot_management/**
docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
```

Responsibilities:

- freeze policy and command schemas;
- freeze pagination/filter shapes;
- freeze compatibility reason codes;
- freeze idempotency and reconciliation states;
- define capability names;
- coordinate versioning and compatibility.

### 4.2 Integration owner

Only the integration owner modifies shared composition hot spots unless a task explicitly delegates one exact file.

Reserved hot paths:

```text
ai_platform/portal/control_plane/api.py
ai_platform/portal/control_plane/app.py
ai_platform/portal/control_plane/database.py
ai_platform/portal/control_plane/migrations/**
ai_platform/portal/web/proxy.ts
ai_platform/portal/web/lib/client-fetch.ts
ai_platform/portal/web/lib/identity.ts
ai_platform/portal/web/playwright.config.ts
docs/ai_platform/portal/UI_DELIVERY_STATUS.md
docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
```

Feature agents should add routers, services, repositories, components and tests in their own paths. The integration owner wires them into shared entry points after narrow feature validation passes.

## 5. Workstream ownership matrix

| Workstream | Suggested task | Primary owned paths | Depends on | Parallel status |
|---|---|---|---|---|
| Shared contracts | `BM-00` | `contracts/bot_management/**`, matching contract tests | current contracts | serial first |
| Catalog and compatibility | `BM-01` | `bot_catalog/**`, `tests/.../bot_catalog/**` | BM-00 | parallel wave 1 |
| Bot builder/configuration | `BM-02` | `bot_builder/**`, `tests/.../bot_builder/**` | BM-00, BM-01 contract | parallel wave 1 |
| Bot command persistence | `BM-03` | `bot_operations/**`, `tests/.../bot_operations/**` | BM-00 | parallel wave 1 |
| Signal/webhook control | `BM-04` | `signal_control/**`, `tests/.../signal_control/**` | BM-00, BM-03 command contract | parallel wave 1 |
| Grid capability | `BM-05` | `grid_control/**`, `tests/.../grid_control/**` | BM-00, BM-02 policy contract | parallel wave 1 |
| Exchange connection product | `BM-06` | `exchange_connections/**`, matching tests | BM-00 | parallel wave 1 |
| Web bot builder | `BMW-01` | `web/app/bots/new/**`, `web/components/bot-builder/**` | frozen BM-00/BM-01 API | parallel wave 1 |
| Web operations | `BMW-02` | bot-detail command components and feature-local BFF routes | BM-03 contracts | parallel wave 1 |
| Web signals/grid/exchanges | `BMW-03` | feature-specific app/components paths | relevant frozen APIs | parallel wave 1 |
| Credential broker | `PI-07` | `credential_broker/**`, provider tests and deployment config | secret-backend decision, BM-06 | wave 2 |
| Dry-run submission/reconciliation | `PI-08` | `execution/freqtrade/**`, `execution/reconciliation/**` | PI-07, BM-03, risk/audit | wave 3 activation |
| Position/order command activation | `BM-07` | command mappings and feature services | PI-08 | wave 3 |
| Dashboard/read models | `BM-08` | bounded analytics/read-model paths and web surfaces | authoritative sources | wave 2/3 |
| Full product E2E | `BM-09` | `e2e/scenarios/bot_*`, Playwright feature specs | integrated features | continuous, closes last |

## 6. Execution waves

### Wave 0 — architecture and contracts

Use one lead agent.

Deliver:

- BM-00 task record;
- versioned domain contracts;
- capability vocabulary;
- pagination/filter contract;
- command/idempotency/reconciliation state model;
- contract tests;
- feature router composition protocol.

No feature implementation should invent its own replacement schema.

### Wave 1 — safe parallel product foundations

Run up to six agents in parallel:

1. catalog and compatibility;
2. bot builder/configuration;
3. bot command persistence;
4. signal/webhook control;
5. grid capability;
6. exchange-connection product metadata.

Web agents may work in parallel against frozen contracts and explicit fixture/API modes. They must not change the shared identity boundary or claim private execution exists.

### Wave 2 — security and evidence integrations

Parallel work may include:

- PI-07 credential broker after the secret-store decision;
- dashboard/read-model completion;
- external notification delivery under PI-05;
- target observability integration;
- real PI-06 identity acceptance on owner-managed infrastructure;
- BFF convergence for merged feature APIs.

PI-07 has one security owner. No adjacent agent may add an alternate secret-resolution path.

### Wave 3 — private dry-run execution

The PI-08 implementation owner activates:

- approved intent submission;
- exact runtime/config binding;
- acknowledgement mapping;
- ambiguous-result state;
- reconciliation;
- dry-run enforcement;
- duplicate-delivery protection.

After the PI-08 contract and implementation are green, separate agents may activate:

- close/partial-close/close-all;
- cancel/cancel-all/replace;
- DCA execution mapping;
- TP/SL execution mapping;
- grid runtime commands.

These command activations may run in parallel only if they own disjoint mappings and tests and use the same frozen execution/reconciliation contract.

### Wave 4 — external acceptance and product closure

Close with:

- full browser/API/security E2E;
- real Authentik target acceptance;
- real target observability;
- P11 protected Cloudflare External E2E;
- performance, accessibility and responsive checks;
- documentation status convergence.

P14 live-small remains a separate blocked package.

## 7. Shared-path protocol

Before editing any shared hot path, an agent must:

1. search open PRs and active task records;
2. confirm the integration owner or receive an explicit exact-file delegation;
3. record the delegation in both task checkpoints;
4. keep the change minimal and feature-neutral;
5. return ownership after merge.

Two agents must never edit the same migration chain, shared contract file or root API composition file concurrently.

## 8. Router and API registration protocol

Feature agents add feature-owned routers, for example:

```text
bot_catalog/router.py
bot_builder/router.py
bot_operations/router.py
signal_control/router.py
grid_control/router.py
exchange_connections/router.py
```

The integration owner alone registers them in the application factory.

For the web BFF:

- feature agents own routes under their feature path;
- common cookie, CSRF, identity and error translation remain shared and centrally owned;
- feature routes call canonical server APIs and do not duplicate domain policy;
- a browser route cannot resolve a secret or private runtime address.

## 9. Migration sequencing

Use one migration coordinator.

Each feature task declares:

- proposed tables and indexes;
- tenant ownership;
- append-only or mutable state rules;
- uniqueness/idempotency constraints;
- upgrade and rollback behavior;
- expected migration order.

The coordinator creates or assigns the final migration revision. Feature agents must not independently choose competing migration heads.

## 10. Test ownership

Each feature agent owns narrow tests under its module.

The E2E owner owns shared scenarios and accepts feature contributions only after their narrow tests pass.

Required scenario families:

```text
bot_creation
bot_revision_conflict
bot_lifecycle
signal_authentication_and_replay
risk_approved_and_rejected_commands
private_dry_run_submission
ambiguous_execution_reconciliation
position_and_order_management
grid_configuration_and_runtime
cross_tenant_denial
session_revocation_and_step_up
source_unavailable_and_stale
```

No fixture-only success may be labeled real Freqtrade, Authentik, observability or Cloudflare acceptance.

## 11. Suggested task records

Use dated IDs:

```text
FTAI-YYYYMMDD-portal-bm00-bot-management-contracts
FTAI-YYYYMMDD-portal-bm01-bot-catalog-compatibility
FTAI-YYYYMMDD-portal-bm02-bot-builder-configuration
FTAI-YYYYMMDD-portal-bm03-bot-command-model
FTAI-YYYYMMDD-portal-bm04-signal-webhook-control
FTAI-YYYYMMDD-portal-bm05-grid-product-capability
FTAI-YYYYMMDD-portal-bm06-exchange-connection-product
FTAI-YYYYMMDD-portal-pi07-runtime-credential-broker
FTAI-YYYYMMDD-portal-pi08-private-dry-run-submission
FTAI-YYYYMMDD-portal-bm07-position-order-command-activation
FTAI-YYYYMMDD-portal-bm08-dashboard-read-model-completion
FTAI-YYYYMMDD-portal-bm09-bot-management-e2e-closure
```

Every task must copy its dependencies and non-goals from the architecture document.

## 12. Branch and PR discipline

Each agent:

- branches from current `develop` only after checking active ownership;
- owns one bounded package;
- opens one reviewable PR;
- does not combine adjacent packages for convenience;
- updates task checkpoint and owned status documents;
- rebases only after checking whether shared contracts changed;
- leaves exactly one concrete next action.

An architecture package being documented does not activate all implementation tasks. The owner starts each wave explicitly through dated tasks.

## 13. Stop conditions

Stop instead of improvising when:

- a required shared contract is not frozen;
- an active PR owns the same paths;
- the secret backend or provider decision is missing;
- work would expose secrets or runtime endpoints to the browser;
- PI-08 is attempted before PI-07 acceptance;
- command success would be inferred without reconciliation;
- a feature would enable live capital;
- a task would weaken risk, audit, tenant or identity controls;
- repository-only evidence would be labeled as target-environment acceptance.

## 14. Recommended immediate staffing

For the next implementation phase, use this order:

1. **one BM-00 contract lead**;
2. after BM-00 merge, **five parallel agents** for BM-01 through BM-06, combining one pair only where scope is small;
3. **one integration owner** for shared router/migration/BFF composition;
4. **one E2E owner** working continuously but merging scenario expansions after each feature;
5. PI-07 and PI-08 owners only when their entry gates are satisfied.

Therefore this is not a one-agent task. It is a coordinated multi-agent program with a serial contract gate and serial security/execution activation gates.
