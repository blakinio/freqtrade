# AI Trading Portal — UI Delivery Status

## Purpose

Track the difference between a route or shell being present, a surface being integrated with canonical portal data and a real target environment being accepted.

Repository product closure does not authorize production deployment, exchange credentials, withdrawals or live capital.

## Status vocabulary

- **integrated** — route reads or mutates canonical server-side portal data;
- **partially integrated** — bounded canonical behavior exists while a broader target source remains unavailable or owner-gated;
- **fixture preview** — deterministic development/E2E data exists only in explicit fixture mode;
- **blocked** — external infrastructure or separately authorized lifecycle work is required.

## Completed convergence packages

The current repository includes:

- authoritative operational positions, orders, trades, risk and audit read models;
- PI-01 private runtime read/reconciliation;
- PI-02 attributable valuation;
- PI-03 inference/drift telemetry;
- PI-04 repository observability contracts;
- PI-06 repository identity/session backend, same-origin browser integration and Authentik/Synology deployment package;
- PI-07 Vault-backed credential broker contracts;
- PI-08 private risk-approved dry-run submission and reconciliation;
- BM-00 through BM-06 domain products;
- BMW-01 through BMW-03 browser convergence;
- BM-07 private position/order command activation;
- BM-08 server-owned dashboard read model;
- BM-09 repository E2E and quality closure.

BM-07 completed in PR #672, merge `ef0550744104f4c82ef3f106181f14442f9b82af`. BM-09 completed in PR #675, merge `d7ae949cb91d44e260ca7c32e193d69238fad120`.

## Current surface matrix

| Product surface | Route | Current delivery | Data and authority boundary |
|---|---|---|---|
| Dashboard | `/` | integrated | tenant-scoped server-owned BM-08 model with independent control-plane, runtime, valuation, model and risk states |
| PNL & Performance | `/performance` | integrated for bounded evidence | persisted realized trades plus attributable valuation; stale, unavailable and incompatible evidence remains non-current |
| Open Positions | `/positions` | integrated | private collector to tenant/bot/runtime operational mirror with explicit freshness |
| Orders | `/orders` | integrated | private runtime evidence mirror with attribution and reconciliation |
| Trade History | `/trades` | integrated | canonical runtime trade evidence with source timestamps and mismatch/unavailable states |
| Liquidations | `/market/liquidations` | integrated read-only preview | bounded Liquid20 research evidence; `trading_authorized=false` |
| Trading Terminal | `/terminal` | integrated risk-intent surface, no direct runtime authority | same-origin BFF to deterministic risk intent; private PI-08 exists server-side and is not a browser-addressable Freqtrade route |
| View Bots | `/bots` | integrated | bounded server composition of bot, runtime, performance, valuation, risk and audit evidence |
| Bot Detail | `/bots/detail/[botId]` | integrated operations and lifecycle intent | same-origin immutable-revision commands; execution acknowledgement remains distinct from proof |
| Create Bot | `/bots/new` | integrated for dry-run | protected same-origin BFF to control plane |
| Signal Wizard | `/bots/signals` | integrated advisory control | protected signal persistence and authentication state; no independent execution authority |
| Strategy Catalog | `/bots/strategies` | integrated | immutable server-side strategy metadata |
| Grid Bots | `/bots/grid` | partially integrated | persisted dry-run configuration; exposure-increasing private activation must reuse PI-08 and is not a direct browser runtime call |
| Exchange Connections | `/platform/exchanges` | integrated metadata and lifecycle state | opaque credential references only; secret values and private endpoints hidden |
| AI Overview | `/ai` | integrated | canonical model, intelligence and learning reads |
| Trade Analysis | `/ai/trade-analysis` | integrated | TradeAnalysis read API |
| Insights | `/ai/insights` | integrated | TradeInsight read API |
| Model Health | `/ai/model-health` | integrated | aggregate inference and reproducible drift evidence |
| Experiments | `/ai/experiments` | integrated | learning-history evidence |
| Learning History | `/ai/learning` | integrated | aggregate learning history |
| Execution Activity | `/operations/execution-logs` | partially integrated | permission-gated repository observability and audit; real target telemetry remains deployment-owned |
| Signal Logs | `/operations/signal-logs` | integrated | tenant-scoped persisted SignalEvent evidence |
| Risk Events | `/operations/risk-events` | integrated | deterministic RiskDecision evidence |
| Runtime Health | `/operations/runtime-health` | integrated | desired/observed runtime state and source evidence |
| Audit Events | `/operations/audit` | integrated | tenant-scoped append-only evidence requiring audit permission |
| Notifications | `/platform/notifications` | partially integrated | actor preferences and in-app entries; external channels remain PI-05 |
| Product login | `/login`, `/api/identity/*` | integrated repository/BFF boundary; real target blocked | opaque same-origin sessions, CSRF and membership-derived authorization; real Authentik acceptance unproven |
| Profile & Security | `/platform/profile` | partially integrated | tenant/MFA session state and logout controls; real enrollment/recovery remain target-owned |
| Administration | `/platform/admin` | partially integrated | permission-gated RBAC overview; real membership/recovery administration remains PI-06 target work |

## Execution and evidence semantics

### PI-07 and PI-08

Credentials resolve only through the approved tenant/runtime-scoped broker and never enter browser-visible state. PI-08 binds exact approved intent, tenant, bot, configuration and runtime revisions before private dry-run submission. Health, kill-switch, credential or binding failures fail closed. An HTTP acknowledgement is never authoritative execution proof.

### BM-07

Private close, partial-close, close-all, forced take-profit, cancel and cancel-all mappings reserve durable pending-reconciliation evidence before I/O. Exact replay cannot repeat mutation. DCA, grid and exposure-increasing replacement reuse PI-08. Unsupported price-changing replacement remains rejected.

The browser still communicates only with the portal/BFF. It cannot select a private runtime endpoint, read credentials or call Freqtrade directly.

### BM-08

The dashboard consumes `/v1/bot-management/dashboard/search`. Missing evidence is `UNAVAILABLE`, incomplete evidence is `PARTIAL`, absent valuation for a bot without open positions is `NOT_APPLICABLE`, and independent sources retain their own observation times.

### BM-09

The repository closure provides:

- one versioned matrix covering every required bot-management scenario family exactly once;
- deterministic validation that all evidence references exist;
- a critical Chromium journey across dashboard, fleet, bot detail, exchanges, signals and grid;
- request evidence excluding private Freqtrade mutations and credential references;
- lifecycle replay evidence that persisted acceptance is not execution proof.

Exact implementation head `e0a90ccdcfb3dc0e1ac03acede92f0f8c9da70e3` passed AI Platform CI `30437195010`, Portal Web CI `30437194948`, Portal Universal E2E `30437195047`, Freqtrade CI `30437194987` and workflow security `30437194958`.

## Identity semantics

Protected pages and APIs fail closed for anonymous, expired, revoked, MFA-missing, stale-step-up and cross-tenant states. Unsafe browser requests require same-origin CSRF evidence. Opaque session cookies remain HttpOnly and browser code receives no IdP access, ID or refresh token.

Fixture identity proves deterministic browser behavior only. It is not real Authentik, MFA, recovery, Synology or Cloudflare evidence.

## Remaining hard boundaries

| Boundary | Canonical package or stage |
|---|---|
| real Authentik/Synology provisioning, MFA, recovery, backup/restore and identity acceptance | remaining PI-06 target acceptance |
| real Loki/Tempo/Prometheus connectivity and dashboards | PI-04 deployment configuration |
| external email/webhook/push delivery | PI-05 after provider/privacy decision |
| real Vault initialization, credential enrollment and restore acceptance | PI-07 target evidence |
| real private Freqtrade target and TLS acceptance | PI-08/BM-07 target evidence |
| real protected Cloudflare staging acceptance | P11 |
| live-small readiness | P14, blocked and separately owner-approved |

P13 remains deferred until measured need.

## Safety behavior

API mode never fabricates PNL, valuation, position, order, trade, signal, log, drift, identity, execution or audit records. It returns canonical evidence where a trusted source exists and truthful empty, unavailable, stale, partial, denied or unreconciled state otherwise.

Explicit fixture mode may show deterministic preview rows for development and E2E. Fixture and repository evidence cannot authorize model promotion, real target acceptance, withdrawals or live capital.
