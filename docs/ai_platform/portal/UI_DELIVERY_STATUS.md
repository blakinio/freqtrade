# AI Trading Portal — UI Delivery Status

## Purpose

Track the difference between a route/shell being present and a product surface being functionally integrated with an authoritative backend read model.

A stage is not complete merely because a first web shell exists. UI status must be evaluated against `UI_INFORMATION_ARCHITECTURE.md` and the stage deliverables in `DELIVERY_ROADMAP.md`.

## Status vocabulary

- **integrated** — route exists and reads canonical server-side portal data;
- **partially integrated** — a bounded authoritative read model is integrated, while a broader source such as a real target-environment backend remains intentionally unavailable;
- **shell** — intentional route and safety/authorization UX exist, but the owning mutating capability is not implemented;
- **read-model gap** — route exists and fails closed in API mode because no canonical query API exists yet;
- **fixture preview** — deterministic development/E2E data is available only when explicit fixture mode is enabled;
- **blocked** — external infrastructure or separately authorized lifecycle work is required.

## Delivery correction

Historical PR #135 delivered the **P6.1 Web Shell Foundation**, not the whole target P6 product UI. It delivered the shell, Dashboard, bot fleet, basic Create Bot and state/error/denied foundations.

The full P6 stage remained incomplete because Bot Detail, exchange metadata, runtime health/log views, profile/security/notifications surfaces and the wider navigation contract were not all delivered.

P8 PR #147 delivered the Trade Intelligence backend foundation but did not deliver the roadmap-declared Trade Analysis UI or Insights UI.

P9 PR #158 delivered the Safe Continual Learning backend foundation but did not deliver the roadmap-declared Learning History UI.

`FTAI-20260723-portal-ui-completion` closed the presentation/read-model gaps that could be backed by the then-existing control-plane, intelligence and learning APIs.

`FTAI-20260723-portal-operational-read-models` added a bounded tenant-scoped operational mirror for order/open-position evidence and exposed existing persisted trade-outcome, risk-decision and audit evidence through trusted read APIs. It did not expose private runtime endpoints.

`FTAI-20260724-portal-pi01-runtime-read-reconciliation` adds authoritative private runtime reads for open positions, orders and trades, normalizes them into the operational mirror and makes freshness, completeness and reconciliation explicit. Browser and BFF code still receive no Freqtrade endpoint or credential.

`FTAI-20260724-portal-pi03-inference-drift-telemetry` adds aggregate-only inference windows, explicit source status and reproducible PSI-v1 drift assessments attributed to the exact model, feature schema, bot configuration and runtime. It stores no raw feature values or individual predictions and cannot mutate model lifecycle or promotion state.

`FTAI-20260724-portal-pi04-central-runtime-observability` adds a permission-gated, tenant-scoped private runtime-log query boundary, explicit source availability and retention metadata, correlation/trace linkage and OpenTelemetry Collector routing contracts. Runtime telemetry remains separate from append-only audit evidence, and API mode fails closed when the private target-environment source is not configured.

`FTAI-20260724-portal-pi02-authoritative-valuation` adds exact-runtime `mark-to-entry-v1` valuation with explicit `CURRENT`, `STALE`, `SOURCE_UNAVAILABLE` and `UNPRICED` states. Realized PNL remains separate closed-trade evidence and unsupported currency conversion or leverage never produces a numeric guess. The task is complete and PR #267 merged as `0c8fdfe6fb50ff635403ae963484bf4e6883e1e1`.

`FTAI-20260723-portal-remaining-product-capabilities` closes the remaining software-addressable shell/read-model gaps with tenant-scoped signal evidence, immutable strategy metadata, dry-run grid configuration, in-app notification preferences, trusted profile/security context, permission-gated RBAC overview, truthful model-health telemetry availability and explicit runtime-log availability. It does not fabricate unavailable runtime, market-price or drift sources.

Remaining authoritative-source and external/private integration work is routed through `POST_P12_INTEGRATION_BACKLOG.md`. Current task selection and repair ordering are routed through `NEXT_WORK_AND_REPAIR_PLAN.md`. A mapped package is planning evidence only and does not activate implementation or authorize live capital.

## Current surface matrix

| Product surface | Route | Current delivery | Data boundary |
|---|---|---|---|
| Dashboard | `/` | integrated | bot/control-plane snapshot |
| PNL & Performance | `/performance` | integrated for realized and bounded unrealized evidence | realized PNL from persisted closed trades plus tenant-scoped exact-runtime mark-to-entry valuation; stale, unavailable, cross-currency and leveraged positions remain explicitly non-current |
| Open Positions | `/positions` | integrated for runtime evidence | private collector -> tenant/bot/runtime-scoped operational mirror; rows and empty states distinguish `CURRENT`, `STALE`, `PARTIAL` and `SOURCE_UNAVAILABLE` |
| Trading Terminal | `/terminal` | integrated, execution still fail-closed | deterministic risk intent API |
| Orders | `/orders` | integrated for runtime evidence | private collector -> operational mirror with source identity, freshness and reconciliation; unattributed runtime orders are `MISMATCH` |
| Trade History | `/trades` | integrated for runtime evidence | canonical runtime trade mirror with source timestamps, realized fields when present and explicit mismatch/unavailable semantics; no fabricated current price |
| View Bots | `/bots` | integrated basic fleet, operations convergence planned | control-plane bot API; canonical operations/valuation/risk evidence is not yet composed into the fleet table |
| Bot Detail | `/bots/detail/[botId]` | integrated configuration read, operations convergence planned | control-plane bot API; bot-scoped operations and lifecycle mutations are not yet exposed by the web workflow |
| Create Bot | `/bots/new` | integrated for dry-run | same-origin BFF -> control plane |
| Signal Wizard | `/bots/signals` | integrated | tenant-scoped advisory SignalEvent persistence; never grants execution authority |
| Strategy Catalog | `/bots/strategies` | integrated | immutable server-side portal strategy metadata; no research promotion authority |
| Grid Bots | `/bots/grid` | partially integrated | persisted dry-run-only grid configuration; private runtime activation remains separately controlled |
| AI Overview | `/ai` | integrated | model/intelligence/learning read APIs |
| Trade Analysis | `/ai/trade-analysis` | integrated | P8 TradeAnalysis read API |
| Insights | `/ai/insights` | integrated | P8 TradeInsight read API |
| Model Health | `/ai/model-health` | integrated | tenant-scoped aggregate inference telemetry, source availability, exact model/feature-schema/bot-config/runtime attribution and reproducible PSI-v1 reference/observation evidence |
| Experiments | `/ai/experiments` | integrated | P9 learning history read API |
| Learning History | `/ai/learning` | integrated | P9 aggregate history read API |
| Execution Activity | `/operations/execution-logs` | partially integrated for private runtime observability | `AUDIT_READ`-gated tenant-scoped runtime-log source with bounded correlation/runtime/bot/time filters and retention-aware availability plus separately rendered append-only AuditEvent evidence; real target-environment Loki/Tempo/Prometheus connectivity remains deployment-owned |
| Signal Logs | `/operations/signal-logs` | integrated | same tenant-scoped persisted SignalEvent source as Signal Wizard |
| Risk Events | `/operations/risk-events` | integrated | persisted deterministic RiskDecision evidence |
| Runtime Health | `/operations/runtime-health` | integrated | bot desired/observed runtime state |
| Audit Events | `/operations/audit` | integrated | tenant-scoped AuditEvent query requiring `AUDIT_READ` |
| Exchange Connections | `/platform/exchanges` | integrated metadata-only | opaque refs derived from bot configs; secrets hidden |
| Notifications | `/platform/notifications` | partially integrated | persisted actor preferences and in-app entries derived from canonical signal/risk/own execution evidence; external delivery channels are not claimed |
| Profile & Security | `/platform/profile` | partially integrated | trusted actor/tenant/permission context; MFA credentials and session revocation remain external-IdP-owned |
| Administration | `/platform/admin` | partially integrated | `ADMIN_MANAGE`-gated built-in RBAC overview; tenant membership lifecycle remains external-IdP-owned |

## Bot Operations completion gap

The control plane already supports immutable revision and desired-state mutations, but the web client currently exposes only bot list/get/create behavior. The next bounded product task should compose existing canonical APIs rather than create a new execution authority.

Required completion scope:

- enrich `/bots` with attributable open-position, PNL availability, risk, runtime-health and last-activity summaries plus bounded filters;
- enrich `/bots/detail/[botId]` with bot-scoped positions, orders, trades, valuations, risk decisions, runtime logs and audit evidence;
- add same-origin BFF/client support for `POST /v1/bots/{bot_id}/revisions`;
- add same-origin BFF/client support for `POST /v1/bots/{bot_id}/desired-state`;
- render permission-denied, conflict, stale, partial, unavailable, mutation-pending and confirmation states;
- preserve immutable revisions, tenant attribution, auditability and private runtime boundaries.

This package must not implement `submit_approved_intent`, exchange credential injection, external notification delivery, P11 infrastructure or live capital. Detailed entry gates and acceptance are in `NEXT_WORK_AND_REPAIR_PLAN.md`.

## PI-01 freshness and reconciliation semantics

The Open Positions, Orders and Trade History pages read one canonical `/v1/runtime-evidence` snapshot in API mode.

- `CURRENT` + `SYNCED` means the private source returned a complete authoritative batch inside the freshness bound.
- `STALE` means preserved evidence exists but is not represented as current.
- `PARTIAL` means pagination or record validation was incomplete; the UI does not convert it to a confirmed empty result.
- `SOURCE_UNAVAILABLE` means no authoritative source batch was available.
- `MISMATCH` means source identities or expected attribution/outcome fields conflict with mirror evidence.

Explicit fixture mode remains available only for development/E2E. API mode never falls back to fixture rows.

## PI-03 inference and drift semantics

Model Health derives `HEALTHY`, `ATTENTION`, `DEGRADED`, `INSUFFICIENT_EVIDENCE` or `UNAVAILABLE` only from persisted aggregate windows and explicit source status. Rows expose exact attribution, window identities, sample counts and PSI/feature-quality evidence. No status triggers retraining, promotion or lifecycle mutation, and raw feature values, individual predictions and protected final-holdout observations are excluded.

## PI-04 runtime observability semantics

Execution Activity presents two independent evidence classes. Runtime logs are operational, retention-bound and queryable only through the private tenant-scoped source using `audit.read`; AuditEvent rows remain append-only business/security evidence. A missing or failed log backend produces explicit `UNAVAILABLE`, never a healthy claim or a fabricated empty success. Browser contracts contain source identity, retention and runbook metadata but no private backend endpoint or credential.

## PI-02 valuation semantics

The PNL & Performance page keeps closed-trade realized evidence separate from open-position valuation. Numeric unrealized PNL requires a current reconciled position, an exact source-position match, the pinned runtime's timestamped mark identity, unit leverage and quote currency equal to the bot capital currency. Missing, stale, cross-currency, leveraged or conflicting evidence produces `STALE`, `SOURCE_UNAVAILABLE` or `UNPRICED`, never a fallback number.

## Remaining hard boundaries

The remaining partial states depend on authoritative sources or separately reviewed private integrations that do not currently exist in this repository or target environment:

| Boundary | Canonical package/stage |
|---|---|
| bot-scoped operational convergence and lifecycle/revision UI | `NEXT_WORK_AND_REPAIR_PLAN.md` Bot Operations completion package |
| real target-environment Loki/Tempo/Prometheus connectivity and dashboards | PI-04 deployment configuration |
| external email/webhook/push delivery | `PI-05` External Notification Delivery |
| product authentication, MFA, session revocation and tenant membership lifecycle | `PI-06` Product Identity and Session Lifecycle |
| runtime exchange credential injection/rotation | `PI-07` Runtime Credential Broker and Rotation |
| private risk-approved dry-run Freqtrade submission | `PI-08` Private Dry-Run Approved Execution Submission |
| real protected Cloudflare staging acceptance | P11 external infrastructure gate |

P13 remains deferred until measured need. P14 remains blocked and separately owner-approved; neither is an ordinary UI completion package.

## Safety behavior

API mode never fabricates PNL, valuation, position, order, trade, signal, log, drift, security or audit records. It returns canonical data where a trusted source exists and a truthful empty/unavailable result otherwise. PI-03 drift evidence is derived only from persisted aggregate telemetry and explicit source status. PI-04 runtime-log absence never changes audit records or runtime-health claims.

The normalized operational mirror is the only portal-facing runtime trade evidence boundary. `FreqtradeExecutionAdapter.get_open_positions`, `get_orders` and `get_trades` use the private collector but return records only for complete, current and synced reads; stale, partial, unavailable and mismatched evidence fails closed or remains explicitly degraded in the mirror.

Signal evidence is advisory and cannot create execution authority. Grid configuration is constrained to `dry_run`. Browser code still has no direct Freqtrade, exchange, secret-store or observability-backend path.

Explicit `PORTAL_WEB_DATA_MODE=fixture` may show deterministic preview rows for development and browser E2E. Those rows are test evidence only and cannot authorize execution or model promotion.
