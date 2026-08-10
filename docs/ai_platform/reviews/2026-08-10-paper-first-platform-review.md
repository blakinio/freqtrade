# PAPER-First Quant Platform Architecture Review — 2026-08-10

Status: `architecture review and recommendation evidence`

Repository: `blakinio/freqtrade`

Reviewed integration snapshot for the delivery package: `develop@2a9bee4895981f0a2b7f7f08e0e1d2d2e2ad646a`

Owner operating-mode decision: PAPER is the default/only currently authorized operational mode; SHADOW is optional for bounded test/training/research/diagnostics/parity; LIVE is unreachable until a future explicit owner-approved programme.

This review is point-in-time evidence, not exact-head implementation authority. Current code, tests, migrations, workflow results, deployed-target evidence and the canonical exact-head implementation inventory determine current implementation state.

## 1. Executive verdict

The product idea and target architecture are strong. The platform has unusually good foundations for reproducibility, deterministic risk, immutable runtime identity, AI authority separation and self-hosted auditability. The main weakness is not the architectural direction; it is incomplete product composition.

The platform should therefore not be rewritten. It should stop expanding horizontally until it completes one trustworthy PAPER path from authored revision through isolated runtime, observed state, reconciliation, valuation, audit, restart and rollback.

Directional assessment:

| Area | Assessment |
|---|---|
| Product idea and positioning | strong |
| Target architecture and trust boundaries | strong |
| Research/reproducibility design | strong |
| Runtime isolation implementation | advanced but incomplete |
| Supervisor/Gateway/reconciliation composition | critical gap |
| PAPER execution realism contract | incomplete |
| Product/UX end-to-end coherence | incomplete |
| Governance/status consistency | material conflict |
| Operational protected-target acceptance | incomplete |

## 2. Evidence classification

### PROVEN

- `develop` is the current integration/default branch at the recorded snapshot; `main` remains accepted target release architecture pending physical migration evidence.
- ADR-019 through ADR-021 define architecture authority, exact evidence, RuntimeGeneration/Supervisor/Gateway and orthogonal branch/environment/release/mode semantics.
- Issues #1353 and #1357 are closed; merged PRs #1425 and #1388 provide their repository delivery evidence.
- Issue #1354 remains open and draft PR #1431 contains substantial runtime-isolation work but explicitly does not complete #1355 Runtime Supervisor, its final UDS/API boundary, durable command journal or full acceptance.
- Issue #1355 remains the critical Runtime Supervisor boundary.
- Issue #1356 remains the architecture-registry lifecycle-guard work item.
- Issue #1396 remains open/reopened and therefore must be reconciled with ADR-022 rather than assumed complete from older package status.

### DERIVED

- Adding more pages, bot types or AI families before the first full PAPER vertical slice would increase product-disconnected debt.
- Supervisor and Gateway should remain separate trust-boundary processes while the rest of the Control Plane stays modular-monolith-first.
- PostgreSQL durable state/outbox/inbox/command journal is sufficient as the initial recovery spine before making NATS/JetStream a required dependency.
- If Synology cannot effectively enforce required resource/network/storage isolation, execution should move to a compatible Linux host/VM rather than weaken security requirements.

### CONFLICT

- Legacy lifecycle wording implies mandatory SHADOW and/or a path toward `live-small`/`production`, conflicting with the owner PAPER-first decision and ADR-022.
- Repository status is described by older feature/programme status views and newer exact-head inventories; the authority/migration contract is not yet consistently enforced everywhere.
- Some programme documents lag exact implementation evidence, including WickHunter package statuses.
- Broad component delivery can be mistaken for a complete product where authoritative runtime consumers or reconciliation are still absent.

### UNKNOWN

- Exact protected-host enforcement and real-Docker behavior for every intended Synology/runtime configuration until accepted E2E evidence exists.
- Final measured RTO/RPO and clean restore characteristics.
- PAPER fill realism for each venue/market profile until a versioned execution profile and parity evidence are implemented.
- Scale thresholds that would justify NATS, TimescaleDB, Kubernetes or broader service decomposition.

## 3. What should be preserved

- private Freqtrade behind an adapter and generation-bound Gateway;
- RuntimeGeneration as immutable execution identity;
- authored/desired/observed separation;
- Runtime Supervisor as the only container-engine authority;
- deterministic Risk Engine as final veto;
- AI/model output as advisory evidence, never unrestricted execution authority;
- availability-time/no-lookahead data contracts;
- explicit possibility of selecting no model;
- modular monolith as the default Control Plane structure;
- PostgreSQL and immutable artifact/evidence storage as recovery/audit spine;
- exact-head CI, provenance, digest pinning and build-once/promote-same-digest direction.

## 4. What should change first

1. Make ADR-022 PAPER policy technically fail closed, including tests for all reachable mode-setting boundaries.
2. Establish one implementation-status authority and generate/validate derived programme views.
3. Finish existing runtime-isolation work rather than create a competing implementation.
4. Implement the narrow Supervisor and Gateway boundaries, durable command semantics, idempotency, fencing and reconciliation.
5. Complete one real PAPER vertical slice before exposing more product surfaces.
6. Introduce immutable `PaperExecutionProfile` and replay/backtest/PAPER parity evidence.
7. Add portfolio-level risk, virtual-capital allocation and Decision Black Box composition after authoritative runtime evidence exists.
8. Close operational gaps: SLOs, independent deadman, backup/restore and exact protected-target acceptance.

## 5. Competitor/reference patterns worth adopting

The goal is selective pattern adoption, not feature copying. These references are design inputs, not independent security/performance audits and not implementation authority. Re-check official documentation before making time-sensitive public comparison claims.

| Reference | Pattern used as design input | Quant Platform adaptation |
|---|---|---|
| QuantConnect | coherent research/backtest/paper workflow and reconciliation comparisons | one Evidence Workbench and automatic backtest/replay/PAPER parity report |
| NautilusTrader | event-driven state semantics and reconciliation discipline | deterministic clocks, explicit order/position state machines and reconciliation as truth |
| Hummingbot | bounded Controller/Executor concepts and separate Gateway patterns | versioned `ExecutionPlan` state machines for entry/exit/DCA/grid/TWAP behind stronger per-runtime isolation |
| OctoBot | simulator history, experiment comparison and guided configuration | immutable resettable PAPER portfolio generations and run comparison |
| retail bot UX such as 3Commas/Bitsgap | fast onboarding, templates and demo workflows | guided PAPER bot creation only after the underlying vertical slice is authoritative |
| Coinrule-style demo disclosure | explicit separation of demo/simulated assumptions from real execution | visible PAPER assumptions/limitations instead of implying perfect execution realism |

Patterns not to copy:

- opaque “AI autopilot” authority;
- direct browser/exchange/runtime control paths;
- mandatory LIVE-oriented promotion funnel;
- proliferation of bot types without common execution/risk semantics;
- premature microservices/Kubernetes;
- UI breadth that hides unavailable, disconnected or fixture-backed functionality.

Reference documentation used for the architecture comparison:

- QuantConnect Research Pipeline: <https://www.quantconnect.com/docs/v2/cloud-platform/research-pipeline>
- QuantConnect reconciliation: <https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/reconciliation>
- NautilusTrader concepts: <https://nautilustrader.io/docs/latest/concepts/overview/>
- Hummingbot Strategy V2: <https://hummingbot.org/strategies/v2-strategies/>
- OctoBot simulator: <https://www.octobot.cloud/en/guides/octobot-usage/simulator>
- 3Commas feature overview: <https://help.3commas.io/en/articles/4430555-all-about-3commas-features-tools-history-and-benefits>
- Coinrule demo/live comparison: <https://help.coinrule.com/articles/946340-comparing-live-trading-demo-exchange>
- Bitsgap demo trading: <https://bitsgap.com/demo-trading>

## 6. Recommended product position

The credible differentiator is:

> Every PAPER decision is reproducible, explainable, deterministically risk-bounded and bound to exact data, model, configuration, code, execution-profile and runtime-generation identity.

This is more defensible than claiming that AI automatically finds profitable trades.

## 7. Delivery conclusion

Do not rewrite the platform and do not expand breadth first. The dependency order is:

```text
truth/PAPER guardrails
-> runtime-state conformance
-> effective isolation
-> Supervisor/Gateway
-> authoritative reconciliation/valuation
-> first complete PAPER vertical slice
-> PAPER realism/parity
-> portfolio risk/Evidence Workbench
-> operational recovery/acceptance
```

`main` release migration remains orthogonal and no release/deployment step can unlock LIVE.
