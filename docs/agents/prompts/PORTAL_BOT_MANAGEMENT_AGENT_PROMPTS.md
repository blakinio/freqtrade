# Portal Bot Management — Agent Prompt Pack

## Purpose

This file contains copy-ready prompts for the serial BM-00 contract package and the downstream bot-management agents defined by:

- `docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md`;
- `docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md`.

Repository state, current open PRs, task records and exact CI evidence remain authoritative. A prompt does not activate a package by itself.

## Use rules

1. Start **BM-00 only** until its PR is merged with green required CI.
2. After BM-00, start only agents whose dependency gates are satisfied.
3. Resolve `YYYYMMDD` using the current date in Europe/Warsaw when declaring a new task.
4. Every agent creates or updates one task record under `docs/agents/tasks/` and leaves exactly one concrete `next_action`.
5. Every agent inspects current `develop`, open PRs and overlapping task ownership before editing.
6. Feature agents must not edit reserved integration hot paths unless the integration owner delegates one exact file.
7. PI-07, PI-08, P11 and P14 keep their separate authorization gates.
8. No prompt authorizes live capital, withdrawal-enabled credentials, public Freqtrade exposure or copying proprietary WickHunter code/assets.

Reserved integration hot paths:

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

---

## Prompt BM-00 — Shared bot-management contracts

```text
Work in repository blakinio/freqtrade.

Task: FTAI-20260727-portal-bm00-shared-bot-management-contracts
Branch: feat/portal-bm00-shared-contracts
Base: current develop containing merged PR #438.

Read first:
- AGENTS.md
- docs/agents/CONTEXT_HANDOFF.md
- docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
- docs/agents/tasks/FTAI-20260727-portal-bm00-shared-bot-management-contracts.md
- docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
- docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
- docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
- docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
- ai_platform/portal/contracts/common.py
- ai_platform/portal/contracts/environment.py
- ai_platform/portal/contracts/identity.py
- ai_platform/portal/contracts/bots.py

Before editing, inspect current develop, open PRs and overlapping contract ownership. Continue on the declared branch. Do not create a competing BM-00 branch.

Goal:
Implement only the versioned shared contracts required by the complete dry-run bot-management architecture.

Owned paths:
- ai_platform/portal/contracts/bot_management/**
- tests/ai_platform/portal/contracts/bot_management/**
- the declared BM-00 task record

Deliver contract families for capabilities, bounded pagination/filtering, templates, compatibility, normalized bot configuration, market/entry/sizing/DCA/exit/signal/grid/runtime policies, lifecycle/position/order commands, exchange connection metadata, signal envelopes, execution attempts, acknowledgements and reconciliation.

Use existing frozen strict ContractModel conventions, Decimal values, UTC timestamps, explicit StrEnum reason codes, immutable tuples and deterministic canonical JSON. Require tenant, actor, environment, immutable revision, correlation and idempotency context for state-changing commands. Distinguish ACCEPTED from reconciled execution success. Proven success must require authoritative reconciliation evidence.

Do not implement API routes, database tables, migrations, web/BFF code, Authentik, secret providers, credentials, Freqtrade calls, order submission or live capital. Do not modify existing shared contracts silently. If an unavoidable change outside owned paths is discovered, stop downstream implementation, record the incompatibility and prepare a separate bounded contract-change handoff.

Add focused tests for unknown-field rejection, deterministic serialization, invalid decimals, duplicate identifiers, contradictory DCA/exit/grid settings, tenant mismatch, missing idempotency, stale revision states, bounded pagination and secret exclusion.

Run narrow tests first, then repository-required formatting, typing, security and CI gates. Update the task checkpoint with exact head, changed paths, first failure if any, validation evidence and exactly one next_action. Open or update a draft PR against develop. Do not mark BM-00 done until exact-head required CI is green and the contract surface is reviewed for downstream stability.
```

---

## Prompt BM-01 — Bot catalog and compatibility

```text
Work in repository blakinio/freqtrade.

Do not start unless the BM-00 shared-contract PR is merged into current develop with green required CI. If it is not merged, stop and report that exact blocker.

Declare task FTAI-YYYYMMDD-portal-bm01-bot-catalog-compatibility on branch feat/portal-bm01-bot-catalog-compatibility.

Read AGENTS.md, CONTEXT_HANDOFF.md, the portal program, BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md, BOT_MANAGEMENT_AGENT_PLAN.md, the merged BM-00 task/PR, and only relevant existing strategy/model/exchange catalog code.

Before editing, inspect current develop, open PRs and owned-path conflicts.

Goal:
Implement the authoritative server-owned bot template catalog and deterministic compatibility decisions. Users must select versioned templates and allowed references rather than type arbitrary internal identifiers.

Primary owned paths:
- ai_platform/portal/bot_catalog/**
- tests/ai_platform/portal/bot_catalog/**
- one dated task record

Deliver:
- template repository/service;
- immutable template versions;
- allowed strategy, model, exchange, market, execution-mode and policy-family declarations;
- deterministic compatibility evaluator using BM-00 contracts;
- exact reason codes and evidence/version references;
- explicit unavailable/stale catalog states;
- no silent coercion of unsupported combinations.

Do not edit root API composition, migrations, BFF shared files or web pages. Add a feature router/factory only inside owned paths if the integration contract permits, and leave final app registration to the integration owner. Do not implement credentials, runtime submission, live capital, marketplace billing or third-party WickHunter content.

Test tenant isolation where applicable, deterministic ordering, duplicate-version rejection, incompatible strategy/model/exchange/market combinations, missing evidence and secret exclusion. Run narrow then required broad validation. Open a PR and leave exactly one next_action for integration or BM-02.
```

---

## Prompt BM-02 — Bot builder and immutable configuration

```text
Work in repository blakinio/freqtrade.

Entry gate: BM-00 must be merged. The BM-01 template/compatibility contract must be merged or explicitly frozen in a reviewed dependency PR. If either gate is absent, stop and record the blocker.

Declare task FTAI-YYYYMMDD-portal-bm02-bot-builder-configuration on branch feat/portal-bm02-bot-builder-configuration.

Read required agent files, BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md, BOT_MANAGEMENT_AGENT_PLAN.md, merged BM-00 contracts, BM-01 catalog contracts and current BotSpec/BotConfigRevision behavior.

Goal:
Implement server-side normalization, validation and persistence logic for complete immutable dry-run bot configuration.

Primary owned paths:
- ai_platform/portal/bot_builder/**
- tests/ai_platform/portal/bot_builder/**
- one dated task record

Deliver:
- builder request/application models using BM-00 public contracts;
- template resolution through BM-01;
- exact compatibility decision before persistence;
- normalized market, entry, position-sizing, DCA, exit, signal, optional grid and runtime policies;
- immutable revision creation with deterministic hashes/version references;
- revision conflict detection;
- dry-run/simulated-only enforcement;
- preview/validation result without mutation;
- explicit unsupported-policy and stale-catalog failures.

Do not create browser forms, credentials, runtime containers, Freqtrade calls, order submission or live capital. Do not edit root API/migrations directly; propose schema/migration requirements to the integration owner. Never accept tenant_id, model eligibility or secret references from an untrusted browser as authority without trusted server resolution.

Test contradictory policies, invalid DCA ladders, TP allocation totals, stop/trailing conflicts, duplicate pairs, unsupported leverage/margin modes, stale template versions, revision conflicts and deterministic normalization. Open a PR with exact evidence and one next_action for BMW-01/integration.
```

---

## Prompt BM-03 — Bot command persistence and lifecycle model

```text
Work in repository blakinio/freqtrade.

Entry gate: BM-00 merged with stable command, idempotency and reconciliation contracts.

Declare task FTAI-YYYYMMDD-portal-bm03-bot-command-persistence on branch feat/portal-bm03-bot-command-persistence.

Read required agent files, BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md, BOT_MANAGEMENT_AGENT_PLAN.md, merged BM-00 command/execution contracts, existing control-plane bot lifecycle service, risk/audit contracts and current Bot Operations implementation.

Goal:
Implement durable, tenant-scoped and audited command intent persistence for lifecycle, position and order operations without activating private runtime execution.

Primary owned paths:
- ai_platform/portal/bot_operations/**
- tests/ai_platform/portal/bot_operations/**
- one dated task record

Deliver:
- BotCommand, PositionCommand and OrderCommand application services/repositories;
- idempotency and duplicate conflict behavior;
- exact bot/config/environment/actor binding;
- capability requirements as declared metadata;
- command states ACCEPTED, REJECTED, BLOCKED and PENDING_RECONCILIATION;
- append-only command history and audit/event preparation;
- kill-switch and stale/revision conflict checks where existing authoritative inputs are available;
- no success claim before reconciliation.

Do not call Freqtrade, resolve credentials, implement PI-08, mutate real positions/orders, edit shared root API/migrations or enable live capital. Lifecycle desired-state behavior already present must not be silently redefined.

Test cross-tenant denial, missing capability, duplicate idempotency keys, mismatched revisions, stale runtime evidence, kill-switch blocks and append-only history. Open a PR with one next_action for integration/BMW-02/BM-04.
```

---

## Prompt BM-04 — Signal and webhook control

```text
Work in repository blakinio/freqtrade.

Entry gates: BM-00 merged; BM-03 command contract/service merged or reviewed and frozen. Do not start against an invented command schema.

Declare task FTAI-YYYYMMDD-portal-bm04-signal-webhook-control on branch feat/portal-bm04-signal-webhook-control.

Read required agent files, bot-management architecture/plan, merged signal and command contracts, current advisory Signal Wizard implementation and security architecture.

Goal:
Implement secret-safe, replay-resistant signal endpoint configuration and deterministic signal-to-command mapping. Keep execution disabled unless a later authorized PI-08 path receives an approved command.

Primary owned paths:
- ai_platform/portal/signal_control/**
- tests/ai_platform/portal/signal_control/**
- one dated task record

Deliver:
- endpoint metadata and versioned payload schemas;
- authentication-mode interfaces without storing plaintext secret values;
- signature verification abstraction using opaque references;
- timestamp/nonce/replay protection;
- idempotency;
- commands for open, DCA, close, close-all, take-profit and enable/disable only where the BM-00 vocabulary permits;
- advisory-only versus execution-authorized classification;
- validation/mapping evidence and reason codes;
- simulator/dry-run preview contract.

Do not select a real secret provider, expose endpoint secrets, call Freqtrade, activate order submission, accept arbitrary JSON commands, bypass deterministic risk or copy WickHunter payload formats. Final public/BFF route registration belongs to the integration owner.

Test invalid signatures through fakes, replay, clock window, duplicate idempotency, unsupported command fields, cross-tenant mapping, stale bot revision and advisory-only non-execution. Open a PR and leave one next_action for BMW-03/integration.
```

---

## Prompt BM-05 — Grid capability

```text
Work in repository blakinio/freqtrade.

Entry gates: BM-00 merged; BM-02 policy contract merged or frozen. Do not implement against local ad-hoc grid fields.

Declare task FTAI-YYYYMMDD-portal-bm05-grid-capability on branch feat/portal-bm05-grid-capability.

Read required agent files, bot-management architecture/plan, merged grid/configuration contracts and current bounded grid dry-run code.

Goal:
Implement canonical grid policy validation, deterministic level preview and immutable configuration persistence for dry-run bots.

Primary owned paths:
- ai_platform/portal/grid_control/**
- tests/ai_platform/portal/grid_control/**
- one dated task record

Deliver:
- arithmetic/geometric spacing where contractually supported;
- deterministic level generation;
- lower/upper range, level count and quote allocation validation;
- optional long/short, trailing-grid, TP/SL and volatility controls only if declared by the template/capability profile;
- exchange precision/minimum constraint inputs as explicit evidence;
- preview versus persisted immutable policy distinction;
- no order placement.

Do not implement leverage or margin behavior unless the template/exchange capability explicitly supports it. Do not call an exchange/Freqtrade, edit shared API/migrations/web hot paths or enable live capital.

Test deterministic levels, precision boundaries, invalid ranges, over-allocation, unsupported modes, stale capability evidence and immutable persistence behavior. Open a PR with one next_action for BMW-03/integration.
```

---

## Prompt BM-06 — Exchange connection product surface

```text
Work in repository blakinio/freqtrade.

Entry gate: BM-00 merged. This package may define product metadata and verification workflow, but PI-07 remains separately blocked until an owner-approved secret-provider decision exists.

Declare task FTAI-YYYYMMDD-portal-bm06-exchange-connection-product on branch feat/portal-bm06-exchange-connection-product.

Read required agent files, bot-management architecture/plan, security architecture, BM-00 exchange contracts and current read-only Exchange Connections page.

Goal:
Implement tenant-scoped exchange connection metadata, capability profiles and credential-free/opaque-reference verification workflow without exposing or brokering secrets.

Primary owned paths:
- ai_platform/portal/exchange_connections/**
- tests/ai_platform/portal/exchange_connections/**
- one dated task record

Deliver:
- exchange/account/subaccount metadata;
- supported market types, symbols, precision and feature capabilities;
- opaque credential reference field only;
- verification request/result state machine;
- observations for trading permission and withdrawals-disabled expectation;
- stale/unavailable/revoked/rotation-required states;
- provider interface seam for later PI-07;
- no plaintext key or provider-internal path.

Do not choose or configure Vault/KMS/secret store, accept real credentials, call private trading endpoints, mutate Synology/Cloudflare, edit shared API/migrations/BFF hot paths or enable live capital.

Test secret exclusion, tenant isolation, invalid capability combinations, stale verification, withdrawal-enabled rejection state and deterministic metadata serialization. Open a PR with one next_action for PI-07 decision or BMW-03/integration.
```

---

## Prompt BMW-01 — Web bot builder

```text
Work in repository blakinio/freqtrade.

Entry gates for real API integration: BM-00, BM-01 and BM-02 merged. If backend APIs are not integrated yet, only a clearly declared fixture/mock slice may proceed and must not claim product completion.

Declare task FTAI-YYYYMMDD-portal-bmw01-web-bot-builder on branch feat/portal-bmw01-web-bot-builder.

Read required agent files, UI architecture/status, bot-management architecture/plan and merged catalog/builder contracts.

Goal:
Replace free-text internal identifiers in Create Bot with a server-driven, compatibility-aware multi-step dry-run builder.

Primary owned paths:
- ai_platform/portal/web/app/bots/new/**
- ai_platform/portal/web/app/bots/templates/**
- ai_platform/portal/web/components/bot-builder/**
- feature-local web contract/API helpers explicitly assigned to this task
- focused Playwright/component tests in feature-local paths
- one dated task record

Deliver template selection, exchange/market selection, model/risk compatibility display, entry/sizing/DCA/exit/grid policy steps, immutable review, validation preview, stale/unavailable/denied/error states and dry-run visibility. Tenant identity must come from the trusted session, not an editable field.

Do not edit proxy.ts, client-fetch.ts, identity.ts, Playwright root config or shared app composition without integration-owner delegation. Do not accept secrets, call Freqtrade, implement PI-08 or live capital.

Use same-origin BFF only, CSRF for mutations and backend-authoritative validation. Add responsive and accessibility-focused user journeys. Open a PR with one next_action for integration/E2E.
```

---

## Prompt BMW-02 — Web bot operations

```text
Work in repository blakinio/freqtrade.

Entry gate: BM-03 command API/contract merged and available through a reviewed integration seam.

Declare task FTAI-YYYYMMDD-portal-bmw02-web-bot-operations on branch feat/portal-bmw02-web-bot-operations.

Read required agent files, Bot Operations implementation, UI status, bot-management architecture/plan and merged command contracts.

Goal:
Add permission-gated bot lifecycle, position and order command UX that truthfully shows command acceptance, pending reconciliation, blocked/rejected states and authoritative completion.

Primary owned paths:
- feature-local bot detail command components under ai_platform/portal/web/components/bot-operations/**
- feature-local bot operation routes/pages explicitly assigned
- feature-local same-origin BFF routes
- focused tests
- one dated task record

Deliver explicit confirmation for high-impact actions, step-up-required state, idempotent resubmission behavior, command history, reason codes, freshness/reconciliation status and no optimistic success claim.

Do not implement runtime execution, credentials, shared identity/proxy/client helpers or live capital. Before PI-08, controls may create durable command intents only and must visibly state that execution is not activated.

Test denied/expired/revoked sessions, CSRF, duplicate clicks, stale revision, kill switch, pending reconciliation and mobile layout. Open a PR with one next_action for integration/BM-09.
```

---

## Prompt BMW-03 — Web signals, grid and exchange connections

```text
Work in repository blakinio/freqtrade.

Entry gate: start only the bounded sub-surface whose backend package BM-04, BM-05 or BM-06 is merged. Do not combine unavailable dependencies into fabricated UI.

Declare one task per coherent sub-surface or one explicitly coordinated task with disjoint owned paths: FTAI-YYYYMMDD-portal-bmw03-<surface>.

Read required agent files, UI architecture/status, bot-management architecture/plan and the exact merged backend package.

Goal:
Provide same-origin, responsive and accessible product UX for signal endpoints/rules, grid preview/configuration and exchange connection metadata/verification states.

Primary ownership must be feature-local under:
- web/app/bots/signals/** and web/components/signals/**;
- web/app/bots/grid/** and web/components/grid/**;
- web/app/platform/exchanges/** and web/components/exchange-connections/**;
- focused feature tests.

Do not expose secrets after creation, invent a secret provider, call Freqtrade/exchanges directly, edit shared proxy/identity/client-fetch/Playwright config or enable live capital. Display unavailable/stale/partial states honestly. Open a PR with one next_action for integration/E2E.
```

---

## Prompt INT-01 — Bot-management integration owner

```text
Work in repository blakinio/freqtrade as the single bot-management integration owner.

Entry gate: BM-00 merged. Integrate only feature PRs whose exact-head narrow validation is green and whose contracts match merged BM-00. Do not repair unrelated feature logic inside the integration branch.

Declare task FTAI-YYYYMMDD-portal-bot-management-integration-wave-<N> on branch feat/portal-bot-management-integration-wave-<N>.

Read all required agent files, BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md, BOT_MANAGEMENT_AGENT_PLAN.md, UI_DELIVERY_STATUS.md, NEXT_WORK_AND_REPAIR_PLAN.md, POST_P12_INTEGRATION_BACKLOG.md and the feature PRs selected for this wave.

Owned shared hot paths may include only those required for this integration wave:
- control-plane application/router composition;
- migration numbering and ordering;
- shared BFF/proxy/client identity seams;
- Playwright root configuration;
- canonical status/continuation docs.

Responsibilities:
- verify feature path ownership and dependency versions;
- serialize migrations;
- compose routers/services without creating a monolithic API file;
- ensure browser traffic remains same-origin and Freqtrade-private;
- ensure capability, CSRF, tenant, audit and step-up enforcement;
- resolve only integration defects, returning feature defects to owners;
- run combined API/web/security tests;
- update truthful delivery status and leave exactly one next_action.

Do not activate PI-07/PI-08 without their gates, mutate real infrastructure or enable live capital. Open one bounded integration PR per wave.
```

---

## Prompt PI-07 — Credential broker and rotation

```text
Work in repository blakinio/freqtrade.

HARD ENTRY GATES:
- BM-00 and BM-06 merged;
- explicit owner decision naming the approved secret backend/provider and target environment;
- security review defines tenant isolation, authentication, audit, rotation, recovery and rollback;
- protected secrets and test resources are intentionally available.

If any gate is missing, do not implement. Record the exact blocker and stop.

Declare task FTAI-YYYYMMDD-portal-pi07-credential-broker-<provider> on a dedicated branch.

Read AGENTS.md, CONTEXT_HANDOFF.md, portal program, security architecture, bot-management architecture/plan, POST_P12_INTEGRATION_BACKLOG.md PI-07, merged exchange contracts and provider primary documentation.

Goal:
Implement runtime-only credential brokering, rotation and revocation using the approved provider without plaintext browser, repository, log, event or audit exposure.

Primary owned paths:
- ai_platform/portal/credential_broker/**
- provider-specific tests/config explicitly declared
- one dated task record

Requirements include opaque references, tenant/bot/runtime scoping, withdrawal-disabled verification, short-lived delivery where supported, rotation/revocation, redaction, audit metadata without secret values, failure-closed behavior and isolated recovery tests.

Do not submit orders, activate PI-08, expose secret values, bypass provider policy, add live capital or combine Cloudflare/Auth identity work. Open a separately security-reviewed PR with exact evidence and one next_action for PI-08 readiness.
```

---

## Prompt PI-08 — Private risk-approved dry-run submission and reconciliation

```text
Work in repository blakinio/freqtrade.

HARD ENTRY GATES:
- PI-01 private runtime reads/reconciliation complete;
- BM-00 and BM-03 merged;
- PI-07 merged and accepted in the target dry-run environment;
- deterministic risk/audit/kill-switch contracts are green;
- explicit owner authorization for dry-run submission only;
- no live-capital authorization.

If any gate is missing, stop and record the exact blocker.

Declare task FTAI-YYYYMMDD-portal-pi08-private-dry-run-submission on branch feat/portal-pi08-private-dry-run-submission.

Read required agent files, bot-management architecture/plan, POST_P12_INTEGRATION_BACKLOG.md PI-08, execution/risk/audit code, merged BM-00 execution contracts, BM-03 command service and PI-07 broker.

Goal:
Implement fail-closed submission of an ApprovedExecutionIntent to the exact private Freqtrade dry-run runtime and authoritative reconciliation of ambiguous outcomes.

Primary owned paths:
- ai_platform/portal/execution/freqtrade/**
- ai_platform/portal/execution/reconciliation/**
- focused execution tests and simulator scenarios
- one dated task record

Requirements:
- bind tenant, bot, immutable revision, runtime, environment and idempotency key;
- resolve credentials only through PI-07;
- verify runtime dry-run mode independently;
- block on kill switch, degraded/stale runtime, credential mismatch or revision mismatch;
- prevent unproven duplicate exposure;
- treat timeouts/ambiguous responses as PENDING_RECONCILIATION;
- reconcile from authoritative order/position/trade evidence before success;
- emit audit/correlation evidence without secrets;
- no browser-to-Freqtrade route.

Do not enable live mode, withdrawals, public ports or P14. Add fault-injection tests for timeout-after-submit, duplicate delivery, runtime restart, stale evidence and credential revocation. Open a security-sensitive PR with exact-head evidence and one next_action for BM-07.
```

---

## Prompt BM-07 — Position and order command activation

```text
Work in repository blakinio/freqtrade.

Entry gate: PI-08 merged and accepted for private dry-run submission/reconciliation. Without it, do not claim or implement executable close/cancel/replace behavior.

Declare task FTAI-YYYYMMDD-portal-bm07-position-order-command-activation on branch feat/portal-bm07-position-order-command-activation.

Read required agent files, bot-management architecture/plan, merged BM-03 commands, PI-08 execution/reconciliation and existing operational mirrors.

Goal:
Map approved position/order commands to private dry-run execution with deterministic risk, capability, confirmation, idempotency, audit and reconciliation semantics.

Deliver close position, partial close, close-all, cancel order, cancel-all and replace only where Freqtrade/exchange capabilities are proven. Every action must bind exact authoritative position/order IDs and revision/runtime evidence. Unsupported or stale targets fail closed.

Own bounded command-mapping/service paths declared in the task; do not edit shared composition/migrations without integration-owner coordination. Do not implement live capital or optimistic success. Test duplicate commands, partially filled orders, vanished targets, stale runtime, kill switch and ambiguous responses. Open a PR with one next_action for BMW-02/BM-09.
```

---

## Prompt BM-08 — Dashboard and operational read-model completion

```text
Work in repository blakinio/freqtrade.

Entry gate: authoritative source contracts for the selected metrics are merged and available. Never replace unavailable data with fabricated healthy/zero values.

Declare task FTAI-YYYYMMDD-portal-bm08-dashboard-operational-read-models on branch feat/portal-bm08-dashboard-operational-read-models.

Read required agent files, data/observability architecture, UI status, bot-management architecture/plan and PI-01 through PI-04 evidence.

Goal:
Complete bot-management dashboard/read models for equity, realized/unrealized PNL, fees, slippage where authoritative, drawdown, positions, orders, command lifecycle, exchange/runtime/model/risk health and alerts.

Requirements:
- bounded pagination and stable ordering;
- tenant/bot/environment/time filters;
- exact revision attribution;
- freshness, partial, stale, unavailable and unreconciled states;
- no green health badge without authoritative evidence;
- no mixing incompatible strategy/model/config periods;
- responsive and accessible web presentation through same-origin BFF.

Split backend and web ownership if paths overlap other active agents. Shared app composition and status docs belong to integration owner. Do not enable execution or live capital. Open bounded PR(s) with one next_action for integration/BM-09.
```

---

## Prompt BM-09 — Full bot-management E2E and quality closure

```text
Work in repository blakinio/freqtrade as the bot-management E2E owner.

Start scenario scaffolding after BM-00, but do not declare completion until all required backend, web, PI-07/PI-08 and target identity/observability gates for the dry-run milestone are integrated.

Declare task FTAI-YYYYMMDD-portal-bm09-bot-management-e2e-closure on branch feat/portal-bm09-bot-management-e2e-closure.

Read required agent files, quality/E2E architecture, bot-management architecture/plan, merged package task records and current Playwright/simulator/security suites.

Primary owned paths:
- ai_platform/portal/e2e/scenarios/bot_creation/**
- ai_platform/portal/e2e/scenarios/bot_lifecycle/**
- ai_platform/portal/e2e/scenarios/signal_commands/**
- ai_platform/portal/e2e/scenarios/position_order_commands/**
- ai_platform/portal/e2e/scenarios/grid/**
- ai_platform/portal/e2e/scenarios/execution_reconciliation/**
- feature Playwright specs delegated by integration owner
- one dated task record

Final journey must prove:
real product session -> compatible template selection -> immutable dry-run bot revision -> private runtime lifecycle -> intent -> deterministic risk -> private dry-run submission -> authoritative order/position/trade reconciliation -> audited management command -> PNL/command evidence.

Add negative journeys for cross-tenant access, missing capability, CSRF, MFA/step-up, stale revision, secret exposure, duplicate command, kill switch, exchange/runtime unavailable, ambiguous timeout and direct-Freqtrade denial. Preserve first-failure artifacts and correlation evidence.

Simulation evidence must be labeled simulated. Real Authentik/P11 acceptance remains separate and cannot be claimed from fixture tests. No live capital. Open the closure PR only when dependencies are truthful and leave exactly one next_action.
```

## Recommended launch order

```text
NOW:
  BM-00 only

AFTER BM-00 MERGE — parallel wave 1:
  BM-01
  BM-03
  BM-06
  BM-02 after BM-01 contract is frozen/merged
  BM-04 after BM-03 command contract is frozen/merged
  BM-05 after BM-02 policy contract is frozen/merged

WEB IN PARALLEL WHEN EACH API IS STABLE:
  BMW-01
  BMW-02
  BMW-03

SERIAL/SECURITY-GATED:
  PI-07 -> PI-08 -> BM-07

CONTINUOUS/INTEGRATION:
  INT-01 per wave
  BM-08 when authoritative sources exist
  BM-09 throughout, closes last
```
