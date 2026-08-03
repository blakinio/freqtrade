# AI Trading Portal left-navigation completeness audit

## Scope

This audit verifies every item rendered by the canonical left navigation in `ai_platform/portal/web/components/app-shell.tsx`.

Each item is checked against:

- the documented capability in `docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md`;
- the Next.js page and client component;
- same-origin BFF or server-side control-plane client;
- FastAPI route and backend service;
- persistence, provider and runtime composition;
- focused tests and whether they are fixture, component, API-mode or real protected-target evidence.

The audited product base is `626087ca45d67eb908d6c1f1f419f13cbd49f596`. The canonical audit PR is #1082.

## Terminal conclusion

**None of the 28 left-navigation items is fully end-to-end complete on the audited production-labelled deployment.**

Repository-side code is substantial, but the deployment remains fixture-backed (#1089) and there is no complete real API-mode browser-to-backend journey (#1098). Fifteen items are disconnected from required runtime/provider/producers, one expected producer is missing, nine are partial, and three require owner-managed external acceptance.

## New findings from the 1:1 navigation review

- #1102 — trusted AI intelligence, learning and model lifecycle producers/actions are not composed.
- #1103 — Administration is a safe but read-only RBAC overview, not the documented administration workflow.
- #1104 — Notifications implements an in-app subset but not the documented channels, rule families or delivery lifecycle.

These findings are implementation tasks for separate remediation agents. This audit PR remains audit-only.

## Exact 1:1 matrix

- Audited product base: `626087ca45d67eb908d6c1f1f419f13cbd49f596`
- Canonical navigation items: **28**
- Global deployment gate: `FIXTURE_ONLY` (#1089).
- Global real browser-to-backend gate: incomplete API-mode E2E (#1098).

## Overall totals

- `COMPLETE`: 0
- `PARTIAL`: 9
- `MISSING`: 1
- `DISCONNECTED`: 15
- `FIXTURE_ONLY`: 0
- `EXTERNAL_ACCEPTANCE_REQUIRED`: 3
- `BLOCKED`: 0
- `NOT_APPLICABLE`: 0

## Every left-navigation item

| Group | Item | Route | Frontend | API/BFF | Backend | Persistence/provider | Tests | Overall | Issue/boundary | Reason |
|---|---|---|---|---|---|---|---|---|---|---|
| Overview | Dashboard | `/` | COMPLETE | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **PARTIAL** | #1089, #1092, #1093, #1094, #1098 | Dashboard read model exists, but authoritative runtime, valuation and observability sources are not composed and production-labelled deployment is fixture-backed. |
| Overview | PNL & Performance | `/performance` | COMPLETE | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1092, #1093, #1098 | Rendered portfolio/bot performance cannot be authoritative without runtime collection and valuation composition. |
| Overview | Open Positions | `/positions` | PARTIAL | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1091, #1092, #1098 | Position read model exists, but no authoritative collector is composed and documented manual exit actions are not complete. |
| Market Data | Likwidacje | `/market/liquidations` | COMPLETE | COMPLETE | COMPLETE | EXTERNAL_ACCEPTANCE_REQUIRED | COMPLETE | **EXTERNAL_ACCEPTANCE_REQUIRED** | owner-managed source acceptance | Repository reader, health and browser states are implemented; current real-source freshness and protected deployment acceptance remain external. |
| Market Data | WickHunter Evidence | `/market/evidence` | COMPLETE | COMPLETE | COMPLETE | EXTERNAL_ACCEPTANCE_REQUIRED | COMPLETE | **EXTERNAL_ACCEPTANCE_REQUIRED** | owner-managed source acceptance | Bounded same-origin evidence reader is implemented; real package/source publication and protected-target acceptance remain external. |
| Trading | Trading Terminal | `/terminal` | PARTIAL | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1086, #1089, #1091, #1095, #1098 | Manual risk intent UI exists, but trusted approved submission is not composed and other documented terminal modes remain incomplete. |
| Trading | Orders | `/orders` | PARTIAL | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1091, #1092, #1098 | Order read API exists, but no authoritative collection loop is composed and full order actions are not available. |
| Trading | Trade History | `/trades` | COMPLETE | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1092, #1098 | Trade history reader exists, but production evidence is not refreshed by an authoritative private-runtime collector. |
| Bots | View Bots | `/bots` | PARTIAL | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **PARTIAL** | #1089, #1092, #1093, #1099, #1098 | Durable bot CRUD/read paths exist, but observed runtime, valuation and desired-state execution/reconciliation are incomplete. |
| Bots | Create Bot | `/bots/new` | COMPLETE | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1090, #1098 | Wizard and catalog validation exist, but finalization remains in memory and does not create the durable canonical bot. |
| Bots | Signal Wizard | `/bots/signals` | PARTIAL | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1095, #1100, #1098 | Readiness view exists, but signed endpoint persistence, verifier/provider and operable UI are not composed. |
| Bots | Strategy Catalog | `/bots/strategies` | COMPLETE | COMPLETE | MISSING | MISSING | FIXTURE_ONLY | **MISSING** | #1085, #1089, #1098 | Rich frontend and BFF expect /v1/strategy-catalog producers that do not exist. |
| Bots | Grid Bots | `/bots/grid` | PARTIAL | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1096, #1098 | Readiness view exists, but capability provider, durable policy and canonical configuration actions are unavailable. |
| AI Intelligence | AI Overview | `/ai` | COMPLETE | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1098, #1102 | Read APIs exist, but trusted intelligence/learning producers and model lifecycle workflows are not composed. |
| AI Intelligence | Trade Analysis | `/ai/trade-analysis` | PARTIAL | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1098, #1102 | List view exists, while production analyses are created only through simulator/test call paths. |
| AI Intelligence | Insights | `/ai/insights` | PARTIAL | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1098, #1102 | Insight list exists, but canonical producer plus acknowledge/dismiss/create-experiment actions are incomplete. |
| AI Intelligence | Model Health | `/ai/model-health` | COMPLETE | COMPLETE | PARTIAL | PARTIAL | FIXTURE_ONLY | **PARTIAL** | #1089, #1098, #1102 | Telemetry ingestion and health reads exist, but a complete registered model lifecycle and trusted producer path are missing. |
| AI Intelligence | Experiments | `/ai/experiments` | COMPLETE | COMPLETE | COMPLETE | COMPLETE | FIXTURE_ONLY | **PARTIAL** | #1089, #1098, #1102 | Strategy Lab create/read/compare persistence is implemented, but real API-mode browser proof and authorized promotion handoff are incomplete. |
| AI Intelligence | Learning History | `/ai/learning` | PARTIAL | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1098, #1102 | History reader exists, while learning evidence is produced only by simulator/test workflows. |
| Operations | Execution Logs | `/operations/execution-logs` | COMPLETE | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1094, #1098 | UI and query API exist, but the canonical app injects an unavailable runtime observability source. |
| Operations | Signal Logs | `/operations/signal-logs` | COMPLETE | COMPLETE | COMPLETE | PARTIAL | FIXTURE_ONLY | **PARTIAL** | #1089, #1095, #1098 | Durable advisory signal evidence is readable, but the signed signal-control producer remains disconnected. |
| Operations | Risk Events | `/operations/risk-events` | COMPLETE | COMPLETE | COMPLETE | PARTIAL | FIXTURE_ONLY | **PARTIAL** | #1086, #1089, #1098 | Deterministic risk decisions persist, but the full intent-to-private-execution product path and real API-mode proof are incomplete. |
| Operations | Runtime Health | `/operations/runtime-health` | COMPLETE | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1092, #1099, #1098 | Desired/observed view exists, but no product collector and desired-state worker reconcile authoritative runtime state. |
| Operations | Audit Events | `/operations/audit` | COMPLETE | COMPLETE | COMPLETE | COMPLETE | FIXTURE_ONLY | **PARTIAL** | #1089, #1098 | Tenant-scoped audit reads are durable and permission-gated, but real API-mode browser and deployment evidence are absent. |
| Platform | Exchange Connections | `/platform/exchanges` | PARTIAL | COMPLETE | PARTIAL | DISCONNECTED | FIXTURE_ONLY | **DISCONNECTED** | #1089, #1097, #1100, #1098 | Public metadata is read-only; durable create/verify/rotate/revoke and Vault-backed credential composition are absent. |
| Platform | Notifications | `/platform/notifications` | PARTIAL | COMPLETE | PARTIAL | PARTIAL | FIXTURE_ONLY | **PARTIAL** | #1089, #1098, #1104 | In-app preferences and entries work, but channel delivery, full rule families, retries and receipts are incomplete. |
| Platform | Profile & Security | `/platform/profile` | PARTIAL | COMPLETE | PARTIAL | EXTERNAL_ACCEPTANCE_REQUIRED | FIXTURE_ONLY | **EXTERNAL_ACCEPTANCE_REQUIRED** | owner-managed identity acceptance | Trusted identity summary exists; MFA enrollment, recovery, credential changes and real session acceptance remain external IdP responsibilities. |
| Platform | Administration | `/platform/admin` | PARTIAL | COMPLETE | PARTIAL | PARTIAL | FIXTURE_ONLY | **PARTIAL** | #1089, #1098, #1102, #1103 | Permission-gated RBAC overview is safe but read-only; documented administration workflows are not connected. |

## Interpretation

- `COMPLETE` requires a usable frontend, reviewed API boundary, composed backend, durable or explicitly bounded provider path, and non-fixture acceptance evidence.
- `PARTIAL` means a useful subset exists but documented actions, data sources or acceptance evidence remain incomplete.
- `MISSING` means the expected producer or capability is absent.
- `DISCONNECTED` means classes/routes may exist but the canonical product does not compose the required durable/provider/runtime path.
- `EXTERNAL_ACCEPTANCE_REQUIRED` means repository-side behavior is bounded, but owner-managed identity, source or protected-target acceptance is still required.

No navigation item is fully end-to-end `COMPLETE` on the audited production-labelled deployment because #1089 and #1098 remain open.

## Safety and evidence boundary

- No product behavior, credential, deployment, trading state or live-capital authority was changed.
- Browser fixture evidence is not treated as product API-mode acceptance.
- Simulator evidence is not treated as private runtime evidence.
- Authentik, Vault, Cloudflare, Synology, market-data publication and private Freqtrade acceptance remain owner-managed or protected-target gates where stated.
- P14 live-small/live capital remains unauthorized and blocked.

```text
secret_values_recorded=false
live_capital_authorized=false
product_code_changed=false
```
