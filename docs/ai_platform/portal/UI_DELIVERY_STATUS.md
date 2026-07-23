# AI Trading Portal — UI Delivery Status

## Purpose

Track the difference between a route/shell being present and a product surface being functionally integrated with an authoritative backend read model.

A stage is not complete merely because a first web shell exists. UI status must be evaluated against `UI_INFORMATION_ARCHITECTURE.md` and the stage deliverables in `DELIVERY_ROADMAP.md`.

## Status vocabulary

- **integrated** — route exists and reads canonical server-side portal data;
- **shell** — intentional route and safety/authorization UX exist, but the owning mutating capability is not implemented;
- **read-model gap** — route exists and fails closed in API mode because no canonical query API exists yet;
- **fixture preview** — deterministic development/E2E data is available only when explicit fixture mode is enabled;
- **blocked** — external infrastructure or separately authorized lifecycle work is required.

## Delivery correction

Historical PR #135 delivered the **P6.1 Web Shell Foundation**, not the whole target P6 product UI. It delivered the shell, Dashboard, bot fleet, basic Create Bot and state/error/denied foundations.

The full P6 stage remained incomplete because Bot Detail, exchange metadata, runtime health/log views, profile/security/notifications surfaces and the wider navigation contract were not all delivered.

P8 PR #147 delivered the Trade Intelligence backend foundation but did not deliver the roadmap-declared Trade Analysis UI or Insights UI.

P9 PR #158 delivered the Safe Continual Learning backend foundation but did not deliver the roadmap-declared Learning History UI.

`FTAI-20260723-portal-ui-completion` closes these presentation/read-model gaps without changing live-capital or research boundaries.

## Current surface matrix

| Product surface | Route | Current delivery | Data boundary |
|---|---|---|---|
| Dashboard | `/` | integrated | bot/control-plane snapshot |
| PNL & Performance | `/performance` | read-model gap + fixture preview | normalized PNL read model not yet exposed |
| Open Positions | `/positions` | read-model gap + fixture preview | private execution position query not yet exposed |
| Trading Terminal | `/terminal` | integrated, execution still fail-closed | deterministic risk intent API |
| Orders | `/orders` | read-model gap + fixture preview | private execution order query not yet exposed |
| Trade History | `/trades` | read-model gap + fixture preview | normalized trade mirror query not yet exposed |
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
| Execution Logs | `/operations/execution-logs` | read-model gap | centralized log query API pending |
| Signal Logs | `/operations/signal-logs` | read-model gap | signal event query API pending |
| Risk Events | `/operations/risk-events` | read-model gap | durable risk event query API pending |
| Runtime Health | `/operations/runtime-health` | integrated | bot desired/observed runtime state |
| Audit Events | `/operations/audit` | read-model gap | privileged audit query API pending |
| Exchange Connections | `/platform/exchanges` | integrated metadata-only | opaque refs derived from bot configs; secrets hidden |
| Notifications | `/platform/notifications` | shell | notification service pending |
| Profile & Security | `/platform/profile` | shell | end-user identity/MFA/session flows pending |
| Administration | `/platform/admin` | shell | permission-gated admin capabilities pending |

## Safety behavior

API mode never fabricates PNL, position, order, trade, log or audit records when the canonical backend read model is absent.

Explicit `PORTAL_WEB_DATA_MODE=fixture` may show deterministic preview rows for development and browser E2E. Those rows are test evidence only and cannot authorize execution or model promotion.

Browser code still has no direct Freqtrade, exchange or secret-store path.
