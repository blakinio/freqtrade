# ADR-026 — Quant Platform v2 core ownership and Freqtrade retirement candidate

Status: `selected_pending_independent_architecture_qualification`  
Recorded: `2026-08-28`  
Architecture base: `develop@2a85a4ba54a55bb3312262e0a600a9a889ce31ce`  
Detailed candidate: `QUANT_PLATFORM_V2_TARGET_ARCHITECTURE.md`  
Qualification command: `Quant: audyt architektury`

## Authority and lifecycle

This ADR records architecture decisions selected under the delegated `PLATFORM_ARCHITECT` authority plus the owner migration-end-state decision recorded during the `Quant: architektura` cycle.

It is intentionally **not yet the binding current target architecture**. Until an independent `ARCHITECTURE_QUALIFICATION` passes and a bounded follow-up architecture-promotion change explicitly updates authority, the current binding product/runtime overlays remain:

- ADR-023 — single-owner Developer Quant Portal product semantics;
- ADR-025 — Synology persistent runtime and GitHub-hosted stateless build/test plane;
- `DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md` — current binding refinement of those decisions.

Merging this candidate records a qualified-review target. It does not by itself claim implementation, validation, deployment, E2E proof or runtime cutover.

## Decision

Select migration strategy **C: clean-sheet Quant Platform v2 core with strangler migration**, while deliberately **not** rewriting the whole product.

The candidate target separates ownership as follows:

1. **Rust Quant Core** owns deterministic runtime semantics that benefit from one strongly typed state machine: canonical event/run ordering, idempotency, deterministic simulation, simulated order/position/outcome state, durable journal semantics, replay, snapshot/recovery and causal trace identity.
2. **Python strategy/ML plane** remains the home of WickHunter semantics, feature computation, FreqAI/research code, LightGBM/classical ML, training and bounded inference workers.
3. **TypeScript/Next.js Portal** remains the owner-facing UI. The existing **FastAPI control plane** remains the server-side Portal/BFF/control facade during the strangler migration and may remain permanently where it is the simplest owner-facing boundary.
4. **PostgreSQL** is the authoritative durable database for v2 runtime metadata, decisions, simulation state, model/dataset registry metadata and causal/provenance relationships. Large immutable datasets, model binaries and replay/evidence bundles use an artifact-store abstraction compatible with ADR-010; the exact Synology-backed S3-compatible implementation remains to be proven/selected before it becomes an implementation dependency.
5. The first v2 slice uses direct bounded service/process communication plus transactional outbox/idempotency where asynchronous publication is required. **NATS/JetStream is not a first-slice prerequisite.** A broker is introduced only when measured fan-out, isolation or independent scaling demonstrates the need.
6. The initial Rust↔Python boundary uses a versioned private HTTP/JSON contract because it is easy to inspect, replay and test across languages. gRPC/protobuf is deferred unless latency/throughput benchmarks or schema-generation benefits justify the added operational/tooling surface.
7. LLM/agentic AI is excluded from synchronous market-decision, simulation and state-transition authority. It may be used later for asynchronous research/operator assistance behind explicit trust and activation boundaries.

## Owner migration-end-state decision — Freqtrade

The selected owner end state is:

**Freqtrade is retired from the persistent Developer Quant v2 runtime.**

Freqtrade is retained as one or more of:

- `REFERENCE_ORACLE` for behavior/parity comparison;
- `MIGRATION_INPUT` while v2 assumes responsibilities currently exercised through Freqtrade-backed paths;
- bounded offline/backtest/reference tooling where it remains useful;
- `TEMPORARY_COMPATIBILITY_LAYER` during the strangler migration.

It is **not** a permanent first-class state owner in the target persistent Developer Quant runtime.

This decision does not require deleting Freqtrade code, breaking upstream synchronization or removing useful adapters immediately. Retirement is complete only after the v2 replacement behavior required by the current product has deterministic parity or an explicitly accepted intentional semantic difference, restart/recovery evidence and owner-facing Portal proof.

## Why this direction

The existing repository already contains useful but split ownership across Freqtrade-backed runtime paths, a Python deterministic simulator/replay path, WickHunter file/evidence runtimes, FastAPI Portal state and multiple historical production-control abstractions. Continuing to make Freqtrade the permanent center would preserve dual semantics and state ownership exactly where v2 needs deterministic replay/recovery and one causal record.

A complete rewrite of Portal and ML code would add migration risk without creating equivalent ownership benefit. The selected boundary therefore concentrates the clean-sheet work only in the deterministic runtime/state responsibility and reuses existing Python and TypeScript assets behind explicit contracts.

## First evidence-producing vertical slice

The first candidate slice is **V2-S1**:

```text
Public Market Event
  -> WickHunter Decision
  -> Deterministic Simulation
  -> Durable Causal Trace
  -> Portal
```

V2-S1 starts from a frozen canonical market/WickHunter input bundle through an adapter; it does not require rewriting the live collectors first.

Required semantics:

- Rust Quant Core assigns/validates canonical run and event ordering;
- Python WickHunter worker emits an immutable versioned strategy decision;
- `NO_TRADE` is a first-class successful strategy decision, not an error or missing output;
- strategy/ML worker unavailability is a separate fail-closed `DECISION_ENGINE_UNAVAILABLE` condition and must never be converted to `NO_TRADE`;
- Rust Quant Core owns deterministic simulated state transition and outcome production;
- PostgreSQL durably relates input, decision, simulation transition/outcome, code/model/config identities and trace identity;
- Portal reads the causal trace through the existing same-origin server-side boundary;
- restart/replay cannot duplicate an accepted decision/outcome or change the replay digest for the same canonical input and identities.

## Verification gate for V2-S1

Before V2-S1 can be claimed complete, its implementation plan must require at least:

- Rust/Python/TypeScript contract/schema tests;
- canonical/golden WickHunter fixtures;
- property tests for ordering, idempotency and duplicate/conflict handling;
- deterministic replay twice with the same result/digest;
- parity tests against the frozen Python/WickHunter/Freqtrade reference behavior where parity is required, with explicit fixtures for intentional differences;
- restart during the decision-to-outcome lifecycle with no duplicate state transition;
- PostgreSQL integration/recovery evidence;
- explicit worker-unavailable fail-closed evidence distinct from `NO_TRADE`;
- one browser/system E2E proving the complete causal trace is readable through the actual Portal boundary.

Synology target proof is required before deployment completion, but it is not a prerequisite for architecture qualification and must not turn every inner-loop implementation change into a full target-host E2E.

## Migration and anticipated supersession impact

This candidate does **not** supersede any accepted ADR while qualification is pending.

If it passes independent qualification and is promoted by a bounded follow-up architecture change, that promotion is expected to:

- refine/supersede ADR-001 only to the extent it makes Freqtrade a permanent internal execution engine for the current Developer Quant runtime;
- refine ADR-002 so the Portal may remain a FastAPI modular control/BFF surface while deterministic Quant Core state becomes a separate Rust process/bounded context;
- retain ADR-009 versioned-event, outbox and durable-state principles while removing NATS JetStream as an unconditional first-slice dependency;
- retain ADR-010 PostgreSQL-first and large immutable artifact separation;
- retain ADR-023 product scope and absence of real-money execution;
- retain ADR-025 Synology/GitHub workload-placement authority unless independently superseded later;
- refine the Freqtrade language in `DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md` from persistent target runtime to migration/reference compatibility.

The promotion change must preserve exact supersession history rather than rewriting old evidence.

## Deliberately deferred decisions

The following are not blockers for architecture qualification or V2-S1 design:

- NATS/JetStream introduction — revisit when measured fan-out/independent scaling warrants a broker;
- gRPC/protobuf — revisit when benchmark or generated-contract value justifies it;
- rewriting Liquid20/public collectors in Rust — revisit after V2-S1 proves canonical ingestion contracts;
- exact Synology S3-compatible artifact backend — must be resolved before an implementation slice depends on it;
- deep-learning/LLM/agent runtime roles — require a concrete research problem and evidence; no synchronous authority is granted;
- future real-money Execution/Capital Gateway — completely outside current scope and requires a separate owner-approved programme.

## Safety invariants

This candidate grants no authority for:

- private exchange trading credentials;
- real order submission or withdrawal;
- real-capital allocation;
- automatic model promotion/activation;
- protected-environment mutation;
- broad container-engine access;
- browser access to private engine/runtime endpoints;
- runtime/product implementation through the architecture command itself.

ADR-023 and ADR-025 safety/runtime boundaries remain binding during qualification and migration.

## Qualification and promotion gate

Candidate promotion requires all of the following:

```text
owner-approved target direction exists
AND V2-S1 is explicitly defined
AND V2-S1-required decisions are selected or deliberately deferred with a gate
AND independent exact-head ARCHITECTURE_QUALIFICATION has no unresolved current-gate P0/P1 blocker
AND the promotion change explicitly updates canonical authority/supersession surfaces
```

Only after that gate may a separate implementation-governance package freeze implementation lanes/control-plane/DAG. This ADR does not define or activate such mutating implementation authority.
