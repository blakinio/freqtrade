# FTAI Developer Quant Portal Program

## Program ID

`FTAI-PROGRAM-AI-TRADING-PORTAL`

## Status

`architecture-reset-migration`

## Governing decision

ADR-023, owner-accepted `2026-08-15`, governs the **entire current Portal**, including WickHunter integration. It supersedes conflicting current-Portal assumptions from the former PAPER-first, multi-tenant and production-like staging target while preserving historical evidence truthfully.

## Mission

Deliver a private, single-owner Developer Quant Portal that continuously turns real public market data into observable bot/model decisions, simulated outcomes, durable research datasets, local challenger training, model comparison/manual activation and restart-safe ongoing observation.

The programme is not a real-money trading programme. Exchange order submission, private trading credentials, withdrawals and capital authority are outside the current product and require a separate future owner-approved Execution/Capital Gateway programme if ever requested.

## Current product model

```text
data source:      REALTIME_PUBLIC | REPLAY
runtime location: LOCAL | SYNOLOGY
simulation:       integrated developer capability
model lifecycle:  BASELINE | CHALLENGER | ACTIVE | ARCHIVED
```

`SHADOW`, `PAPER`, `LIVE`, `PAPER_ELIGIBLE`, `production trading`, former P/PI/BM stage gates and protected-production acceptance remain historical/compatibility vocabulary only where exact current code or evidence still contains them. They are not current Portal product modes or automatic delivery blockers.

## Source of truth

In order:

1. system/owner instructions and root `AGENTS.md`;
2. current repository, PR, Issue and exact-head CI state;
3. `ARCHITECTURE_REGISTRY.yaml` and ADR-023;
4. `docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md`;
5. this programme record and active dated tasks;
6. historical architecture/audit/programme evidence for context only.

Chat history is not durable programme state.

## Required reads

For current Portal/WickHunter work read only the minimum relevant set:

- `AGENTS.md`
- `docs/agents/PROMPTING_STANDARD.md`
- `docs/agents/PROMPTING_HANDOVER.md`
- `ARCHITECTURE_REGISTRY.yaml`
- `docs/ai_platform/portal/ADR-023_DEVELOPER_QUANT_PORTAL.md`
- `docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md`
- `docs/ai_platform/portal/README.md`
- the active task and live PR/Issue/CI state.

Load older `SYSTEM_ARCHITECTURE.md`, PI/BM plans, PAPER-first documents, Runtime Supervisor/isolation contracts or audit reports only when their retained technical component is actually relevant.

## Program invariants

- The Portal is single-owner. Existing tenant fields/RBAC may remain for compatibility or defense in depth but are not product-completion prerequisites.
- Browser traffic never receives secrets and does not talk directly to internal runtime-control endpoints.
- Server-side collectors/runtimes may consume public exchange/market-data APIs required by `REALTIME_PUBLIC` workflows.
- Existing Freqtrade compatibility remains `dry_run: true`; no current Portal path may submit a real exchange order.
- Simulation may create positions/orders/trades **inside the simulator** and must label them as simulated.
- Every bot/model decision, including `NO_TRADE`, should be attributable to data/model/config identity and decision-time context sufficient for later analysis.
- Later outcomes/labels are materialized without future leakage and grow a chronological durable dataset.
- Local training may create challenger models. It may not silently replace the active model.
- Model activation is explicit, attributable and reversible.
- Existing RuntimeGeneration, Supervisor, Gateway, risk, evidence, audit and isolation components are reusable tools, not universal ceremony. Keep them only where they materially solve the current workflow or a concrete safety/reliability risk.
- Authentication, secret exclusion, durable state/backup, bounded inputs, restart recovery and proportionate process/container hardening remain required.
- Historical research evidence and protected holdouts are not rewritten or iteratively consumed merely to make the current product look better.
- Autonomous repair remains branch/PR based and may not perform destructive shared-host actions outside task scope.

## Product vertical slice — current highest priority

The programme is not allowed to call the current Portal usefully delivered until this owner-facing journey works end to end:

1. Liquid20/market collectors provide current public Binance/Bybit/OKX evidence with truthful freshness/health.
2. WickHunter consumes canonical public market evidence continuously on the selected `SYNOLOGY` runtime.
3. Every eligible decision, including `NO_TRADE`, is durable with score/confidence/reason/model/data context.
4. Simulated signal/position lifecycle and later outcomes are visible with PnL, fees/slippage assumptions and drawdown.
5. Decision-time evidence plus delayed outcomes grow a versioned chronological dataset.
6. A `LOCAL` training worker can train at least one challenger from the accumulated dataset without touching protected holdout or silently promoting it.
7. The Portal compares `ACTIVE`/`BASELINE` versus `CHALLENGER` on attributable evidence and lets the owner deliberately activate/archive the selected model.
8. Portal/API/browser views expose data health, bot decisions, simulated positions/outcomes, dataset/model identities and training/comparison state.
9. Restart of the persistent Synology services preserves/reconciles the durable workflow and continued observation.
10. Real exchange orders, private trading credentials and live capital remain absent.

## Product surfaces

Current product navigation should prioritize:

- Dashboard / system health;
- WickHunter / bot decisions;
- Market Data / Liquidations;
- Simulation / positions / outcomes;
- Datasets;
- Models / active vs challenger;
- Training / experiments / replay;
- System / logs / storage / restart state.

Administration, notifications, enterprise tenant switching, production credential management and similar surfaces are not blockers unless reclassified `KEEP_NOW` for a concrete current need.

## Backlog migration rule

Before continuing any pre-ADR-023 Portal/WickHunter task, classify it from exact live state:

- `KEEP_NOW` — directly required by the current vertical slice;
- `SIMPLIFY` — capability is useful but former mode/enterprise/protected ceremony is removed;
- `DEFER` — useful later but not needed to make the current owner workflow operational;
- `OBSOLETE` — exists only because of superseded SHADOW/PAPER/LIVE, multi-tenant, private-trading, Vault/credential or production-certification assumptions.

An `OBSOLETE` task/PR should become intentionally terminal with an accurate superseded/not-planned reason. Preserve historical commits, evidence and branches long enough to support provenance; do not delete useful history merely because the plan changed.

A `SIMPLIFY` task must be rewritten around the smallest current user outcome rather than continuing old acceptance by inertia.

## Quality policy

Validation is proportional to actual risk and workflow impact:

- focused unit/contract tests for changed logic;
- component/integration tests across real producer/consumer seams being delivered;
- real browser/API E2E for owner-facing Portal workflows;
- real `REALTIME_PUBLIC` data evidence where market-data behavior is the feature;
- restart/persistence validation for persistent Synology components;
- security validation for authentication, secrets, input bounds and privileged boundaries actually used;
- exact-head CI before merge.

Do not require enterprise production certification, a protected-target ritual, a complete audit matrix or exact-current proof of unrelated monorepo components merely because an older plan did. A material current risk still requires a proportionate gate.

## Historical programme state

P0-P14, PI-01..PI-08, BM-00..BM-09, ADR-020/021/022, PAPER Platform gates and prior protected staging work remain immutable history/evidence. Their completed code may be reused. Their former completion semantics do not override ADR-023.

In particular:

- historical Vault/private-execution work does not require current private trading credentials to exist;
- historical multi-tenant/RBAC work may remain in code but is not a current product blocker;
- historical Runtime Supervisor/Gateway/isolation work may be reused for safe lifecycle control but is not mandatory for every simulated/research path;
- historical PAPER/SHADOW evidence remains valid as evidence of what ran at that time, but future work uses current Developer Portal vocabulary.

## Immediate next action

Reclassify the full live Portal/WickHunter backlog and open related PR inventory under `KEEP_NOW | SIMPLIFY | DEFER | OBSOLETE`, make obsolete work terminal, then execute the smallest complete current vertical slice rather than opening another isolated producer programme.
