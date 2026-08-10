# ADR-022 — PAPER is the default operational authority; SHADOW is optional and LIVE is unreachable

Status: `accepted`

Accepted by owner: `2026-08-10`

Canonical target refinement: `PAPER_FIRST_PLATFORM_ARCHITECTURE.md`

Implementation plan: `PAPER_PLATFORM_IMPLEMENTATION_PLAN.md`

## Decision

1. **`PAPER` is the normal and only currently authorized operational trading mode** for the Quant Platform. A managed Freqtrade `dry_run: true` runtime maps to platform PAPER unless the exact bounded package is explicitly declared SHADOW-only.
2. **`SHADOW` is optional, temporary and purpose-bound.** It may be selected for training, research, diagnostics, observation-only integration/runtime tests, source validation, or replay-to-runtime parity when simulated order submission would invalidate or unnecessarily complicate that evidence. It is not a mandatory promotion stage before PAPER.
3. **`LIVE` is reserved vocabulary but has no reachable transition in the current platform.** UI, API, configuration generation, eligibility/promotion logic, RuntimeGeneration materialization and Runtime Supervisor validation must reject or omit LIVE and fail closed. A schema may retain the literal for forward compatibility, but no current actor may activate it.
4. **No implicit authority transfer is permitted.** Merge, CI success, release-channel promotion, environment deployment, model promotion, strategy promotion, PAPER eligibility, protected-host acceptance or runtime recovery cannot enable LIVE.
5. **Strategy/model eligibility is separate from runtime mode.** The canonical PAPER eligibility states are `NOT_EVALUATED`, `RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `PAPER_SUSPENDED` and `RETIRED`. Eligibility is granted to an exact evidence tuple rather than a mutable strategy name: dataset/feature-schema identity, strategy/model/parameter identity, risk-policy identity, execution-profile identity, code/artifact identity and required validation evidence.
6. **Mode and eligibility are immutable generation material.** A change creates a new desired `RuntimeGeneration`; it never mutates a running generation in place. Reconciliation remains authoritative for observed mode and generation state under ADR-020.
7. **Delivery prioritizes one trusted PAPER vertical slice over additional feature breadth.** New product surfaces must not outrun the end-to-end chain from immutable authored state through eligibility, desired generation, Supervisor/Gateway runtime, authoritative observed state, valuation, reconciliation, audit and rollback.
8. **PAPER realism is explicit and versioned.** The target architecture introduces an immutable `PaperExecutionProfile` and parity evidence comparing deterministic replay/backtest expectations with observed PAPER behavior. Exact implementation remains gated by the implementation plan and evidence; this ADR does not claim it already exists.

## Reason

The previous lifecycle wording made SHADOW appear mandatory and left a path toward `live-small`/`production`, while the repository owner explicitly selected PAPER-only operation until a future independent LIVE decision. Treating SHADOW as a mandatory stage adds operational complexity without improving every validation package. Treating LIVE as merely “not yet selected” is weaker than the required safety posture: current software must make it unreachable.

A PAPER-first lifecycle also sharpens product priorities. The platform contains broad UI/API/domain components, but the material risk is incomplete composition between desired state, isolated runtime authority, observed state and reconciliation. A single complete PAPER path provides stronger evidence than adding more disconnected screens or bot types.

## Migration impact

1. replace legacy lifecycle wording in governing agent and architecture documents;
2. add fail-closed tests proving LIVE is omitted/rejected at every reachable mode-setting boundary;
3. preserve historical SHADOW evidence, but require new SHADOW packages to state their bounded purpose;
4. reconcile WickHunter Issue #1396 and programme wording with optional SHADOW and direct PAPER eligibility;
5. complete exact-head architecture-finding lifecycle validation under Issue #1356;
6. continue RuntimeIsolationProfile work under Issue #1354 / existing PR #1431 and complete the Runtime Supervisor boundary under Issue #1355;
7. implement the first full PAPER vertical slice before broadening product surfaces;
8. add `PaperExecutionProfile`, parity evidence, portfolio-level risk and Evidence Workbench only in dependency order.

## Consequence

Canonical strategy lifecycle:

```text
experiment -> candidate -> validated -> paper-eligible -> paper -> paper-suspended | retired
```

Optional validation side lane:

```text
candidate | validated -> shadow-validation -> validated
```

There is no current transition to LIVE. Any future LIVE proposal requires a separate owner-approved architecture decision and implementation programme covering credentials, deterministic and portfolio risk, execution semantics, incident response, protected deployment, operational acceptance and rollback.

ADR-022 grants no deployment, protected-host mutation, private trading credential, real order, withdrawal or live-capital authority.

## Accepted-decision-log synchronization rule

This file records ADR-022 as an accepted decision so the owner decision is durable immediately. `docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md` remains the historical aggregate accepted-decision log and must include an ADR-022 entry before this architecture-recording task is considered terminal. Until that synchronization is merged, this file plus the owner-approved PAPER architecture is the explicit bounded ADR-022 record; it does not create runtime implementation authority.
