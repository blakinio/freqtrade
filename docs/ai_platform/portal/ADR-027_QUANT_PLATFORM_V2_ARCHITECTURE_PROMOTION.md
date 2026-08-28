# ADR-027 — Promote the qualified Quant Platform v2 target

Status: `accepted`
Accepted: `2026-08-28`
Trusted promotion base: `develop@c9bbd17c716162edffd5b695eac4fb197c7bbf38`
Promoted candidate: `ADR-026_QUANT_PLATFORM_V2_CORE_AND_FREQTRADE_RETIREMENT.md`
Promoted detailed target: `QUANT_PLATFORM_V2_TARGET_ARCHITECTURE.md`
Qualified candidate PR: `#1676@5efda8fc9297f9387fffcfc7c81e604baee4e8bf`
Qualification evidence: `docs/ai_platform/reviews/2026-08-28-quant-platform-v2-architecture-qualification.md`

## Decision

Promote the exact Quant Platform v2 architecture recorded by ADR-026 and `QUANT_PLATFORM_V2_TARGET_ARCHITECTURE.md` in PR #1676 to binding target architecture.

ADR-026 remains the immutable candidate/design record that was qualified. Its historical lifecycle wording (`selected_pending_independent_architecture_qualification`, `candidate`, and equivalent labels) describes the state at which the reviewed artifact was recorded. This ADR supersedes those lifecycle labels for current authority without rewriting the qualified evidence.

Current authority is intentionally layered:

1. **ADR-023** remains binding product authority: private single-owner Developer Quant research/simulation platform, `REALTIME_PUBLIC | REPLAY`, deliberate model activation, no private trading credentials/orders/withdrawals/real capital.
2. **ADR-025** remains binding runtime/CI placement authority: persistent stateful application runtime on Synology; GitHub-hosted Actions for stateless/disposable CI/test/build/scan/jobs where compatible.
3. **ADR-026 as promoted by ADR-027** is binding Quant Platform v2 core/migration authority: Rust Quant Core owns target deterministic ordering, simulation, journal/replay/recovery and causal state; Python owns strategy/ML; TypeScript/Next.js plus the FastAPI facade remain the owner-facing Portal boundary; PostgreSQL is the authoritative recovery spine.

Where older current-target documents describe Freqtrade as a persistent target engine, ADR-027 refines that wording: those paths are current implementation/migration compatibility, not the v2 end-state owner. Freqtrade remains `REFERENCE_ORACLE`, `MIGRATION_INPUT`, bounded offline/reference tooling and `TEMPORARY_COMPATIBILITY_LAYER` until replacement responsibilities prove their gates. It is retired from the persistent Developer Quant v2 runtime only after parity or explicitly accepted intentional difference, restart/recovery evidence, owner-facing Portal proof and a viable rollback/compatibility path.

## Explicit refinement / supersession relationships

ADR-027 applies the promotion relationships anticipated by ADR-026:

- **ADR-001** is refined only where it implied Freqtrade is the permanent internal execution/state engine. Freqtrade remains private/replaceable during migration and as bounded reference tooling.
- **ADR-002** is refined so the FastAPI Portal/control facade may remain modular-monolith-first while deterministic Quant Core state is a separate Rust process/bounded context. This is not a microservice programme.
- **ADR-009** keeps versioned events, transactional outbox and durable-state principles; NATS/JetStream is no longer an unconditional V2-S1 dependency and remains evidence-gated.
- **ADR-010** remains binding for PostgreSQL-first relational/runtime state and large immutable artifact separation.
- **ADR-023** is retained for product scope, model lifecycle, simulation semantics and no-real-capital authority.
- **ADR-025** is retained for Synology persistent placement and GitHub-hosted stateless/disposable execution.
- `DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md` remains the current product/runtime baseline, but its Freqtrade-persistent-target wording is refined by ADR-027 into migration/reference compatibility for the v2 end state.

Historical ADRs, PRs, Issues, runs and evidence are not rewritten.

## Architecture-before-execution gate

Promotion does **not** activate implementation lanes, runtime mutation or deployment.

A separate execution-governance package must be created before mutating v2 implementation work begins. That package must freeze unique durable lane ownership, control-plane authority, dependency DAG, task/lease semantics, validation responsibilities and stop conditions under the promoted target.

V2-S1 implementation entry remains gated on verified availability of the reference/parity oracle and canonical WickHunter/WH09 fixture needed by the selected proof matrix. The first slice remains:

```text
Frozen canonical public market/WickHunter input
-> Rust Quant Core acceptance/order
-> Python WickHunter decision
-> Rust deterministic simulation
-> PostgreSQL causal persistence
-> Portal causal-trace view
```

`NO_TRADE` is a valid successful decision. `DECISION_ENGINE_UNAVAILABLE` is a distinct fail-closed failure and may never be fabricated as `NO_TRADE`.

Only one runtime may own a given migrated live/persistent simulation responsibility at a time. Shadow/reference comparison may observe both implementations, but authority for the same state transition must not be dual-owned. Cutover of each ownership boundary requires its parity/intentional-difference, deterministic replay, restart/recovery and rollback evidence.

## Safety / non-authority

This architecture promotion grants no authority for:

- runtime or product implementation by itself;
- deployment or protected-environment mutation;
- private exchange/account/order endpoints or credentials;
- real order submission, withdrawal or capital allocation;
- automatic model or strategy activation;
- destructive/shared-state operations;
- broad container-engine authority.

Any future real-money Execution/Capital Gateway remains a separate owner-approved architecture and programme.

## Implementation truth

Acceptance of ADR-027 is target authority, not implementation evidence. Exact current code, migrations, tests, workflows, runtime state and E2E remain authoritative for what is actually implemented. The Rust Quant Core must not be reported as present, deployed or production-ready until exact evidence proves it.
