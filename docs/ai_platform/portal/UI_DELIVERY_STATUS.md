# AI Trading Portal — UI Delivery Status

## Purpose

Track the difference between a route/shell being present and a product surface being functionally integrated with an authoritative backend read model.

A stage is not complete merely because a first web shell exists. UI status is evaluated against `UI_INFORMATION_ARCHITECTURE.md`, canonical backend contracts and stage deliverables.

## Status vocabulary

- **integrated** — route exists and reads or mutates canonical server-side portal data;
- **partially integrated** — a bounded authoritative model is integrated, while a broader target-environment source remains intentionally unavailable;
- **shell** — intentional route and safety/authorization UX exist, but the owning capability is not implemented;
- **read-model gap** — route exists and fails closed because no canonical query API exists;
- **fixture preview** — deterministic development/E2E data is available only in explicit fixture mode;
- **blocked** — external infrastructure or separately authorized lifecycle work is required.

## Delivery correction and completed convergence

Historical PR #135 delivered the P6.1 Web Shell Foundation, not the entire target P6 product UI. Later bounded tasks closed presentation and canonical read-model gaps.

Completed integration packages include:

- `FTAI-20260723-portal-ui-completion` for wider navigation and truthful product surfaces;
- `FTAI-20260723-portal-operational-read-models` for tenant-scoped order, position, trade, risk and audit evidence;
- `FTAI-20260724-portal-pi01-runtime-read-reconciliation` for authoritative private runtime reads with freshness and reconciliation;
- `FTAI-20260724-portal-pi02-authoritative-valuation` for exact-runtime mark-to-entry valuation with explicit unavailable/unpriced states;
- `FTAI-20260724-portal-pi03-inference-drift-telemetry` for attributable aggregate inference and PSI-v1 drift evidence;
- `FTAI-20260724-portal-pi04-central-runtime-observability` for permission-gated private runtime logs and correlation evidence;
- `FTAI-20260723-portal-remaining-product-capabilities` for signals, strategy metadata, grid configuration, in-app notification preferences, profile/security and RBAC surfaces;
- `FTAI-20260726-portal-bot-operations-completion` for bounded bot fleet/detail convergence and immutable revision/lifecycle commands;
- the Liquid20 read-only packages for source-labelled liquidation research preview;
- `FTAI-20260726-portal-pi06-product-identity-lifecycle` for the authoritative repository identity/session backend;
- `FTAI-20260726-portal-pi06-bff-browser-session-integration` for same-origin login, callback, session, logout, logout-all, CSRF and protected browser behavior.

PR #361 connects the browser/BFF boundary to the merged PI-06 backend contract. It adds optimistic Proxy denial and Route Handler defense in depth, safe redirects, opaque session/CSRF cookies, visible tenant/MFA session state and deterministic security E2E. It does not provision a real Authentik instance, user, MFA device, recovery flow, Synology deployment or Cloudflare resource.

Remaining authoritative-source and external/private work is routed through `POST_P12_INTEGRATION_BACKLOG.md`. Current task ordering is in `NEXT_WORK_AND_REPAIR_PLAN.md`. A mapped package does not authorize live capital.

## Current surface matrix

| Product surface | Route | Current delivery | Data boundary |
|---|---|---|---|
| Dashboard | `/` | integrated | bot/control-plane snapshot behind protected same-origin session boundary |
| PNL & Performance | `/performance` | integrated for realized and bounded unrealized evidence | persisted closed trades plus exact-runtime mark-to-entry valuation; stale, unavailable, cross-currency and leveraged evidence remains non-current |
| Open Positions | `/positions` | integrated for runtime evidence | private collector -> tenant/bot/runtime mirror with `CURRENT`, `STALE`, `PARTIAL`, `SOURCE_UNAVAILABLE` |
| Liquidations | `/market/liquidations` | integrated read-only research preview | same-origin BFF -> bounded Liquid20 read model -> read-only evidence mount; `trading_authorized=false` |
| Trading Terminal | `/terminal` | integrated, execution fail-closed | same-origin CSRF-protected BFF -> deterministic risk intent API; submission remains `ORDER_SUBMISSION_NOT_IMPLEMENTED` |
| Orders | `/orders` | integrated for runtime evidence | private collector -> operational mirror with attribution, freshness and reconciliation |
| Trade History | `/trades` | integrated for runtime evidence | canonical runtime trade mirror with source timestamps and explicit mismatch/unavailable semantics |
| View Bots | `/bots` | integrated operational fleet | bounded server composition of bots, runtime evidence, performance, valuation, risk and audit summaries |
| Bot Detail | `/bots/detail/[botId]` | integrated operations/lifecycle workflow | tenant/bot-scoped evidence plus same-origin CSRF-protected immutable-revision and desired-state commands |
| Create Bot | `/bots/new` | integrated for dry-run | protected same-origin BFF -> control plane |
| Signal Wizard | `/bots/signals` | integrated | protected advisory SignalEvent persistence; no execution authority |
| Strategy Catalog | `/bots/strategies` | integrated | immutable server-side strategy metadata |
| Grid Bots | `/bots/grid` | partially integrated | protected persisted dry-run grid configuration; runtime activation separately controlled |
| AI Overview | `/ai` | integrated | model/intelligence/learning read APIs |
| Trade Analysis | `/ai/trade-analysis` | integrated | TradeAnalysis read API |
| Insights | `/ai/insights` | integrated | TradeInsight read API |
| Model Health | `/ai/model-health` | integrated | tenant-scoped aggregate inference telemetry and reproducible drift evidence |
| Experiments | `/ai/experiments` | integrated | learning history read API |
| Learning History | `/ai/learning` | integrated | aggregate learning history |
| Execution Activity | `/operations/execution-logs` | partially integrated | permission-gated runtime-log source plus append-only audit; real target telemetry connectivity remains deployment-owned |
| Signal Logs | `/operations/signal-logs` | integrated | same tenant-scoped persisted SignalEvent source |
| Risk Events | `/operations/risk-events` | integrated | persisted deterministic RiskDecision evidence |
| Runtime Health | `/operations/runtime-health` | integrated | bot desired/observed state |
| Audit Events | `/operations/audit` | integrated | tenant-scoped append-only AuditEvent query requiring `AUDIT_READ` |
| Exchange Connections | `/platform/exchanges` | integrated metadata-only | opaque references; secrets hidden |
| Notifications | `/platform/notifications` | partially integrated | actor preferences and in-app entries; external channels remain PI-05 |
| Product login | `/login`, `/api/identity/*` | integrated repository/BFF boundary; real IdP blocked | same-origin OIDC initiation/callback/session/logout, opaque cookies, CSRF and backend-authoritative authorization; real Authentik target not provisioned |
| Profile & Security | `/platform/profile` | partially integrated | authenticated session exposes tenant/MFA state and logout controls; real enrollment, recovery and target identity administration remain Authentik-owned |
| Administration | `/platform/admin` | partially integrated | `ADMIN_MANAGE`-gated RBAC overview; full membership administration/recovery target flows remain PI-06 deployment work |

## PI-06 browser identity semantics

The same-origin browser boundary now follows these rules:

- protected pages redirect anonymous/expired/revoked sessions to a neutral login surface;
- protected APIs return fail-closed 401/403 responses rather than rendering authorization as page visibility;
- unsafe browser methods require a readable CSRF cookie and matching `x-csrf-token` header;
- the opaque session cookie remains HttpOnly and browser code never reads it;
- login accepts only an HTTPS IdP authorization redirect from the private backend;
- callback accepts only safe relative application returns and copies backend session/CSRF cookies without exposing IdP tokens;
- Proxy checks are optimistic; Route Handlers and the identity-enabled control plane remain authoritative;
- fixture identity exists only when fixture data mode, test environment and explicit fixture identity mode are all enabled;
- fixture states prove anonymous, expired, revoked, MFA-required, step-up-required and cross-tenant browser behavior, but are not real Authentik evidence.

Exact final head `ec1970a9272bec241a1bab3c447ebd36f53afa58` passed Portal Web CI #287, Portal Universal E2E #292, AI Platform CI #1521, Freqtrade CI #1837 and security #1702. Portal Web CI passed typecheck, lint, production build and 37 Chromium tests.

## Operational evidence semantics

### Bot Operations

The fleet and Bot Detail compose canonical APIs instead of creating a second source or execution authority. Permission-denied, stale, conflict, partial, unavailable, unpriced, empty and mutation-pending states remain explicit. Lifecycle controls do not submit orders.

### Liquidations

The page presents public market-data research evidence only. Source semantics remain labelled, cross-exchange events are not deduplicated, truncated results are not complete aggregates, and a report is accepted only with explicit `passed: true`. Browser code receives no Synology path, Docker socket, exchange credential, signal or execution authority.

### PI-01 runtime evidence

Open Positions, Orders and Trade History distinguish current/synced, stale, partial, unavailable and mismatch states. API mode never falls back to fixture rows.

### PI-02 valuation

Numeric unrealized PNL requires a current reconciled position, exact source match, timestamped mark, unit leverage and compatible quote currency. Missing or conflicting evidence produces degraded state, never a fallback number.

### PI-03 drift

Model Health derives status only from persisted aggregate windows and explicit source state. No drift status triggers retraining, promotion or lifecycle mutation; raw feature values, individual predictions and protected-holdout observations are excluded.

### PI-04 observability

Runtime logs are operational, retention-bound and permission-gated; AuditEvent evidence remains independent and append-only. Missing target telemetry is `UNAVAILABLE`, not healthy or empty success.

## Remaining hard boundaries

| Boundary | Canonical package/stage |
|---|---|
| real Authentik/Synology deployment, MFA enrollment, recovery, backup/restore and identity acceptance | remaining `PI-06` deployment subpackage |
| real target Loki/Tempo/Prometheus connectivity and dashboards | PI-04 deployment configuration |
| external email/webhook/push delivery | `PI-05` |
| runtime exchange credential injection/rotation | `PI-07` |
| private risk-approved dry-run Freqtrade submission | `PI-08` |
| real protected Cloudflare staging acceptance | P11 |

P13 remains deferred until measured need. P14 remains blocked and separately owner-approved.

## Safety behavior

API mode never fabricates PNL, valuation, position, order, trade, signal, log, drift, security, identity or audit records. It returns canonical data where a trusted source exists and truthful empty/unavailable/denied state otherwise.

The operational mirror remains the portal-facing runtime evidence boundary. Bot Operations composes those reads server-side and forwards only same-origin commands. Signals remain advisory, grid configuration remains `dry_run`, and browsers have no direct Freqtrade, exchange, secret-store or observability path.

Explicit fixture mode may show deterministic preview rows and identity states for development/E2E. They cannot authorize execution, model promotion, real identity acceptance or live capital.
