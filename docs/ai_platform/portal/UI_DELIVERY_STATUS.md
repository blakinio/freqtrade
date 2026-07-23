# AI Trading Portal — UI Delivery Status

## Purpose

Track the difference between a route/shell being present and a product surface being functionally integrated with an authoritative backend read model.

A stage is not complete merely because a first web shell exists. UI status must be evaluated against `UI_INFORMATION_ARCHITECTURE.md` and the stage deliverables in `DELIVERY_ROADMAP.md`.

## Status vocabulary

- **integrated** — route exists and reads canonical server-side portal data;
- **partially integrated** — a bounded authoritative read model is integrated, while a broader source such as raw runtime telemetry remains intentionally unavailable;
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

`FTAI-20260723-portal-operational-read-models` adds a bounded tenant-scoped operational mirror for order/open-position evidence and exposes existing persisted trade-outcome, risk-decision and audit evidence through trusted read APIs. It does not implement the deliberately fail-closed `FreqtradeExecutionAdapter` order/position/trade query methods and does not expose private runtime endpoints.

## Current surface matrix

| Product surface | Route | Current delivery | Data boundary |
|---|---|---|---|
| Dashboard | `/` | integrated | bot/control-plane snapshot |
| PNL & Performance | `/performance` | integrated for realized performance | aggregate of persisted attributable TradeOutcome evidence; unrealized PNL remains outside current read model |
| Open Positions | `/positions` | partially integrated | normalized portal operational mirror; direct Freqtrade position query remains fail-closed |
| Trading Terminal | `/terminal` | integrated, execution still fail-closed | deterministic risk intent API |
| Orders | `/orders` | partially integrated | normalized portal operational mirror; direct Freqtrade order query remains fail-closed |
| Trade History | `/trades` | integrated | persisted TradeOutcome + DecisionSnapshot/TradeAnalysis attribution |
| View Bots | `/bots` | integrated | control-plane bot API |
| Bot Detail | `/bots/detail/[botId]` | integrated | control-plane bot API |
| Create Bot | `/bots/new` | integrated for dry-run | same-origin BFF -> control plane |
| Signal Wizard | `/bots/signals` | shell | signal ingestion contract pending |
| Strategy Catalog | `/bots/strategies` | shell / fixture preview | catalog query contract pending |
| Grid Bots | `/bots/grid` | shell | strategy implementation pending |
| AI Overview | `/ai` | integrated | model/intelligence/learning read APIs |
| Trade Analysis | `/ai/trade-analysis` | integrated | P8 TradeAnalysis read API |
| Insights | `/ai/insights` | integrated | P8 TradeInsight read API |
| Model Health | `/ai/model-health` | partially integrated | immutable model metadata; drift telemetry pending |
| Experiments | `/ai/experiments` | integrated | P9 learning history read API |
| Learning History | `/ai/learning` | integrated | P9 aggregate history read API |
| Execution Activity | `/operations/execution-logs` | partially integrated | permission-gated execution-related AuditEvent evidence; raw centralized runtime stdout/stderr remains unavailable |
| Signal Logs | `/operations/signal-logs` | read-model gap | signal event query API pending |
| Risk Events | `/operations/risk-events` | integrated | persisted deterministic RiskDecision evidence |
| Runtime Health | `/operations/runtime-health` | integrated | bot desired/observed runtime state |
| Audit Events | `/operations/audit` | integrated | tenant-scoped AuditEvent query requiring `AUDIT_READ` |
| Exchange Connections | `/platform/exchanges` | integrated metadata-only | opaque refs derived from bot configs; secrets hidden |
| Notifications | `/platform/notifications` | shell | notification service pending |
| Profile & Security | `/platform/profile` | shell | end-user identity/MFA/session flows pending |
| Administration | `/platform/admin` | shell | permission-gated admin capabilities pending |

## Safety behavior

API mode never fabricates PNL, position, order, trade, log or audit records. It returns canonical data where a trusted read model exists and a truthful empty result otherwise.

The normalized operational mirror is an ingestion/read boundary, not a shortcut around the execution adapter. `FreqtradeExecutionAdapter.get_open_positions`, `get_orders` and `get_trades` remain fail-closed until a separately reviewed private runtime integration is implemented.

Execution Activity is deliberately not described as raw Execution Logs: it contains durable correlation-aware audit evidence only. Raw runtime stdout/stderr and Signal Logs remain explicit read-model gaps.

Explicit `PORTAL_WEB_DATA_MODE=fixture` may show deterministic preview rows for development and browser E2E. Those rows are test evidence only and cannot authorize execution or model promotion.

Browser code still has no direct Freqtrade, exchange or secret-store path.
