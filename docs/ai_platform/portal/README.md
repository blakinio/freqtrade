<!-- portal-status-authority: FEATURE_COMPLETENESS_LEDGER.json -->
# Developer Quant Portal

## Status authority

Current implementation completeness is defined by the living exact-head inventory at `tools/portal_audit/ledger/index.json`, subject to its deterministic exact-head validation and `tools/portal_audit/ledger/status_authority.json`.

That authority answers **what is currently implemented**. ADR-023 and `DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md` answer **what the current product is and what owner-facing workflow counts as product completion**. ADR-026, as promoted by ADR-027, answers **what the accepted Quant Platform v2 deterministic-core and Freqtrade-retirement target is**. The implementation ledger must not turn historical production/PAPER findings into current product prerequisites, and accepted architecture must not fabricate implementation that exact code/tests/runtime evidence do not prove.

The historical `FEATURE_COMPLETENESS_LEDGER.json` and its Markdown projection remain dated **compatibility metadata** and evidence only. Historical pre-ledger evidence is preserved exactly at:

```yaml
snapshot_sha: 4473dfc166d83fe5e0ffba4045c0dcd967626d68
blob_sha: dfd5c7ffe252f6666c3bf3a53d3ee55c58b7bf3d
```

## Purpose

The Portal gives the owner one coherent place to:

- observe realtime public exchange/market data and replay historical data;
- run WickHunter and other developer bots/models locally or persistently on Synology;
- inspect every decision including `NO_TRADE`, confidence and reason codes;
- simulate positions, fees/slippage, outcomes, PnL and drawdown;
- grow versioned chronological datasets from decision-time evidence and later outcomes;
- launch bounded local challenger training;
- compare `BASELINE`, `CHALLENGER` and `ACTIVE` models on attributable evidence;
- deliberately activate or archive a model;
- inspect health, logs, data freshness and restart recovery.

## Current vocabulary

```text
data source:      REALTIME_PUBLIC | REPLAY
runtime location: LOCAL | SYNOLOGY
model lifecycle:  BASELINE | CHALLENGER | ACTIVE | ARCHIVED
execution:        SIMULATION only inside the current Portal
```

`SHADOW`, `PAPER`, `LIVE`, `production trading`, `PAPER_ELIGIBLE` and similar terms may remain in historical evidence or compatibility code during migration, but they are not current Portal product modes.

Real-money exchange execution, private order credentials, withdrawals and capital authority are outside the current Portal. If ever requested, they require a separate owner-approved Execution/Capital Gateway programme.

`quant.molehill.cloud` is the persistent Developer Quant Portal endpoint; its public/persistent deployment does not imply real-money production trading.

## Quant Platform v2 target overlay

ADR-026 as promoted by ADR-027 is the binding v2 core/migration target. Rust Quant Core is the target owner of deterministic ordering, simulation, journal/replay/recovery and causal state; Python remains the strategy/ML plane; TypeScript/Next.js and the FastAPI facade remain the owner-facing Portal boundary; PostgreSQL is the recovery spine.

Current Freqtrade-backed paths are migration/reference compatibility, not permanent v2 state ownership. Freqtrade may remain a `REFERENCE_ORACLE`, `MIGRATION_INPUT`, bounded offline/reference tool and `TEMPORARY_COMPATIBILITY_LAYER` until each replacement boundary proves parity or an accepted intentional difference, deterministic replay, restart/recovery and owner-facing Portal behavior. Promotion of the architecture does not itself remove or mutate current runtime paths.

V2 implementation is separately gated. A dedicated execution-governance package must freeze implementation lanes/control-plane/DAG before mutating v2 work begins, and V2-S1 entry must verify its required reference oracle and canonical WickHunter/WH09 fixture.

## Non-negotiable boundaries

- Browser traffic terminates at the Portal/Next.js same-origin boundary.
- Secrets, databases and internal runtime-control endpoints remain server-side.
- Public exchange/market-data APIs may be consumed by server-side collectors and developer runtimes.
- Existing Freqtrade compatibility use remains `dry_run: true`; simulation cannot submit a real exchange order.
- Training may create challengers but may not silently replace the active model.
- Version datasets, model/config identities and decision-time evidence sufficiently to reproduce comparisons and avoid hindsight leakage.
- Keep authentication, secret exclusion, bounded input handling, durable state/backup, restart recovery and proportionate container/process hardening.
- Do not make multi-tenancy, enterprise RBAC, Vault trading credentials, protected-target certification or host attestation universal completion gates unless a concrete current workflow/risk requires them.

## Product completion model

Current Portal product completion is proved by a real owner-facing vertical workflow, not by the number of isolated producer packages or evidence artifacts:

```text
REALTIME_PUBLIC data
-> bot/model decisions including NO_TRADE
-> simulated positions/outcomes
-> durable dataset growth
-> LOCAL challenger training
-> active/challenger comparison
-> deliberate owner activation
-> restart-safe continued observation through the Portal
```

A component can still have focused tests and exact-head CI, but an isolated backend/contract producer is not a complete user-facing feature by itself.

Open work created under the former PAPER-first/production-like target must be classified before further execution:

- `KEEP_NOW` — directly required by the workflow above;
- `SIMPLIFY` — useful capability, but old enterprise/mode ceremony is removed;
- `DEFER` — valuable later but not a blocker for the current owner workflow;
- `OBSOLETE` — exists only because of a superseded mode, multi-tenant, private-trading or production-certification assumption.

## Canonical current documents

1. `ADR-023_DEVELOPER_QUANT_PORTAL.md` — product authority.
2. `ADR-025_SYNOLOGY_PERSISTENT_RUNTIME_GITHUB_BUILD_PLANE.md` — runtime/CI placement authority.
3. `ADR-027_QUANT_PLATFORM_V2_ARCHITECTURE_PROMOTION.md` — v2 promotion/supersession authority.
4. `ADR-026_QUANT_PLATFORM_V2_CORE_AND_FREQTRADE_RETIREMENT.md` — exact promoted v2 design record.
5. `QUANT_PLATFORM_V2_TARGET_ARCHITECTURE.md` — detailed promoted v2 target.
6. `DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md` — current product/runtime baseline, refined by ADR-027 for v2 core/Freqtrade end state.
7. `ARCHITECTURE_DECISIONS.md` — prior accepted decision log and historical supersession context.
8. repository-root `ARCHITECTURE_REGISTRY.yaml` — canonical authority index.
9. `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md` — current programme boundary where not superseded by later accepted architecture.

`SYSTEM_ARCHITECTURE.md`, `RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md`, `PAPER_FIRST_PLATFORM_ARCHITECTURE.md`, older PI/BM plans and audit reports remain useful historical/specialized references only to the extent later accepted ADRs do not supersede their current-Portal assumptions.

## Current validation

Use validation proportional to the changed workflow. Repository status tooling remains available:

```bash
python tools/agents/check_portal_completeness_ledger.py
pytest -q tests/tools/test_check_portal_completeness_ledger.py
pytest -q tests/ci/test_portal_status_authority.py
```

Those checks validate implementation inventory consistency; they do not redefine accepted product or architecture scope.
