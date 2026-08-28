# Quant Platform v2 Target Architecture — Candidate

Status: **selected candidate pending independent architecture qualification**  
Recorded: `2026-08-28`  
Architecture base: `develop@2a85a4ba54a55bb3312262e0a600a9a889ce31ce`  
Decision record: `ADR-026_QUANT_PLATFORM_V2_CORE_AND_FREQTRADE_RETIREMENT.md`  
Qualification command: `Quant: audyt architektury`

## 1. Authority and purpose

This document is the detailed architecture candidate for Quant Platform v2. It records the result of the `PLATFORM_ARCHITECT` design cycle and is the exact target for independent architecture qualification.

It is **not yet binding current target authority**. Until qualification passes and a bounded promotion change explicitly updates the architecture registry/decision authority, the binding current product/runtime architecture remains ADR-023, ADR-025 and `DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md`.

This document therefore distinguishes:

- selected target architecture;
- current implementation/reference assets;
- migration compatibility;
- intentionally deferred design;
- proof required before implementation closeout.

It does not authorize runtime implementation, deployment, model activation, private exchange authority or real capital.

## 2. Inherited product and operational constraints

Quant Platform v2 remains inside the current owner-approved Developer Quant product boundary:

- private, single-owner developer/quant/research platform;
- `REALTIME_PUBLIC | REPLAY` data sources;
- integrated deterministic simulation, not a capital-authority mode;
- `BASELINE | CHALLENGER | ACTIVE | ARCHIVED` model lifecycle;
- deliberate owner activation; training never silently promotes a model;
- no current private trading credentials, real orders, withdrawals or capital authority;
- persistent application runtime/durable state on Synology under ADR-025;
- GitHub-hosted runners for stateless CI/test/build/scan/disposable work where compatible;
- browser clients stay behind the same-origin Portal/BFF boundary and never receive private engine/container/exchange authority.

Future real-money execution, if ever wanted, is a separate Execution/Capital Gateway programme and is not designed into V2-S1 as dormant authority.

## 3. Migration strategy decision

Three alternatives were evaluated:

### A. Evolve the Freqtrade-centered platform

Advantages:

- lowest immediate migration cost;
- maximum reuse of existing Freqtrade runtime behavior and tooling.

Material disadvantages:

- Freqtrade remains a permanent state/semantic owner even where the product needs deterministic simulation, replay and causal state outside its natural ownership boundary;
- v2 would preserve long-term dual semantics between Freqtrade, Python simulator/replay, WickHunter evidence and Portal state;
- recovery/replay and model-runtime provenance remain coupled to a framework whose primary architecture is not this Developer Quant product.

### B. Incrementally rewrite selected Freqtrade responsibilities but keep Freqtrade first-class indefinitely

Advantages:

- allows gradual extraction;
- lowers early cutover risk.

Material disadvantages:

- indefinite optionality leaves target ownership ambiguous;
- parity surface never closes;
- execution/state adapters remain permanent architecture rather than migration tooling.

### C. Clean-sheet deterministic Quant Core with strangler migration

Advantages:

- one target owner for deterministic simulation/replay/runtime state;
- explicit cross-language contracts rather than directory-level coupling;
- Freqtrade, current Python simulator and WickHunter become testable reference oracles;
- Portal and ML/research assets can be reused without a whole-product rewrite;
- migration can stop or roll back at bounded compatibility seams.

Cost/risk:

- new Rust capability and cross-language contracts must be proven;
- deterministic parity/recovery work is real migration cost;
- premature service decomposition or collector rewrite would increase scope if not controlled.

### Selected

**C** is selected. Clean-sheet applies only to the deterministic Quant Core responsibility. The Portal UI/control facade, Python ML/research ecosystem, current collectors and useful adapters are reused through a strangler migration.

## 4. Target topology

```text
                       GitHub-hosted CI/build/test
                                 |
                                 v
                       immutable images/artifacts
                                 |
                                 v
+------------------------------------------------------------------+
|                    Synology persistent runtime                    |
|                                                                  |
|  public collectors / adapters                                    |
|             |                                                    |
|             v                                                    |
|      canonical market input                                      |
|             |                                                    |
|             v                                                    |
|   +--------------------+       private versioned contract         |
|   | Rust Quant Core    |<-----------------------------------+     |
|   |--------------------|                                    |     |
|   | ordering/idempotency|                                    |     |
|   | simulation state   |                                    |     |
|   | journal/replay     |                                    |     |
|   | snapshot/recovery  |                                    |     |
|   | causal trace       |                                    |     |
|   +---------+----------+                                    |     |
|             |                                               |     |
|             | strategy request                              |     |
|             v                                               |     |
|   +--------------------+                                    |     |
|   | Python strategy/ML |------------------------------------+     |
|   | WickHunter/FreqAI  | decision / NO_TRADE / failure            |
|   +--------------------+                                          |
|             |                                                      |
|             v                                                      |
|      PostgreSQL authoritative state                                |
|             |                                                      |
|             +----------> immutable artifact refs                   |
|             |                                                      |
|             v                                                      |
|   FastAPI Portal/control facade                                    |
|             |                                                      |
|             v                                                      |
|   Next.js / React / TypeScript Portal                              |
+------------------------------------------------------------------+
```

The target is not a microservice programme. Process boundaries exist only where ownership, language/runtime or failure isolation justifies them.

## 5. Bounded contexts and ownership

### 5.1 Quant Core — Rust

Target responsibility:

- canonical event/run identity and ordering;
- ingestion acceptance/idempotency at the Quant Core boundary;
- strategy-decision request lifecycle identity;
- deterministic simulated exchange/order/position/outcome transitions;
- authoritative decision→simulation causal relationship;
- durable journal semantics and transactional persistence coordination;
- replay from canonical durable state/evidence;
- snapshot/restart/crash recovery;
- conflict detection and fail-closed handling for ambiguous duplicate/order cases;
- deterministic trace digest generation.

Candidate implementation family:

- Rust stable toolchain;
- Tokio async runtime;
- Axum for bounded private HTTP service endpoints where needed;
- Serde for versioned JSON contracts;
- SQLx/PostgreSQL for explicit transaction/state access.

Exact dependency versions are implementation decisions and must be selected against current compatible releases when coding begins; this architecture does not freeze stale versions.

Quant Core does **not** own:

- feature research;
- model training;
- model selection/promotion policy UI;
- LLM/agent reasoning;
- browser-facing application composition;
- private exchange execution.

### 5.2 Strategy and ML plane — Python

Target responsibility:

- WickHunter strategy semantics independent of legacy process/file layout;
- feature/context construction;
- LightGBM/classical ML inference where selected;
- FreqAI/research reuse where valuable;
- dataset preparation and training workflows;
- challenger creation/evaluation;
- deterministic model/config/feature identity supplied with each decision;
- explicit typed failures when inference cannot produce a valid decision.

The Python plane is a bounded decision producer. It does not own authoritative simulation state or reinterpret Quant Core ordering/recovery rules.

### 5.3 Portal server/control facade — FastAPI/Python

The existing FastAPI control plane is reused through migration because it already owns broad Portal server APIs and the same-origin boundary.

Target responsibilities include:

- owner-facing commands/query composition within current product authority;
- authentication and server-side validation;
- read models for traces/datasets/models/runtime health;
- deliberate active-model selection workflow;
- compatibility adapters while legacy and v2 coexist.

It is not the canonical owner of deterministic simulation transitions merely because current modules are implemented in Python.

A wholesale FastAPI→Rust rewrite is explicitly **not** a v2 requirement.

### 5.4 Portal UI — TypeScript/Next.js/React

Retain the current web stack and same-origin BFF discipline.

The browser consumes truthful server-side contracts for:

- market/source health;
- decision/`NO_TRADE` trace;
- simulated positions/outcomes;
- dataset/model identities;
- baseline/challenger/active comparison;
- explicit error/unavailable states;
- restart/recovery health.

The browser never talks directly to Quant Core, Freqtrade, exchange APIs, container engine or private Python worker endpoints.

### 5.5 Persistence and artifacts

PostgreSQL is authoritative for relational/runtime state required to answer “what happened and why?” across restart.

At minimum it owns durable identity/relationship records for:

- run/session identity;
- canonical accepted market-event reference;
- strategy request and decision;
- model/config/feature identities;
- `NO_TRADE` decisions;
- engine-unavailable/failure records;
- simulated orders/positions/outcomes;
- trace lineage;
- replay/snapshot checkpoints;
- dataset/model registry metadata;
- deliberate active-model selection audit.

Large immutable blobs stay outside ordinary relational rows behind an artifact-store abstraction: datasets, model binaries, replay bundles and large evidence. ADR-010's S3-compatible direction is retained, but actual Synology backend availability is `UNKNOWN` until proven.

## 6. Current-component classification

| Current component | Candidate classification | v2 treatment |
|---|---|---|
| Next.js/React/TypeScript Portal | `TARGET_COMPONENT` | retain and adapt contracts |
| FastAPI Portal control plane | `TARGET_COMPONENT` + migration facade | retain; do not rewrite solely for language uniformity |
| PostgreSQL/SQLAlchemy Portal state | `TARGET_COMPONENT` / `MIGRATION_INPUT` | PostgreSQL retained; schema ownership migrates toward explicit v2 bounded ownership |
| WickHunter semantics/models | `REFERENCE_ORACLE` + `MIGRATION_INPUT` + target Python capability | preserve semantics, remove dependence on legacy file/process layout over time |
| WH09 append-only journal/runtime evidence | `REFERENCE_ORACLE` + `MIGRATION_INPUT` | parity/provenance source, not target authoritative persistence |
| current Python deterministic simulator | `REFERENCE_ORACLE` + `MIGRATION_INPUT` | golden/parity oracle while Rust simulator assumes target ownership |
| deterministic replay implementation | `REFERENCE_ORACLE` + `MIGRATION_INPUT` | frozen fixtures/digests for v2 replay evidence |
| FreqAI/research stack | `REFERENCE_ORACLE` + `MIGRATION_INPUT` | Python remains research/ML home where useful |
| Liquid20/public collectors | `MIGRATION_INPUT` + initial producer | freeze/adapt first; Rust rewrite deferred |
| Freqtrade | `REFERENCE_ORACLE` + `MIGRATION_INPUT` + `TEMPORARY_COMPATIBILITY_LAYER` | retire from persistent Developer Quant v2 runtime after parity/intentional-difference and recovery gates |
| Synology persistent placement | `TARGET_COMPONENT` | retained under ADR-025 |
| GitHub-hosted CI/build/test | `TARGET_COMPONENT` | retained under ADR-025 |

No classification above claims implementation migration is complete.

## 7. Canonical contract model

Every cross-language/runtime contract must be explicitly versioned and reject unsupported incompatible versions.

### 7.1 Canonical market input

Conceptual minimum fields:

```text
schema_version
source
instrument
market_event_id / source sequence identity where available
event_time
received_time
run_id
payload/body or immutable payload reference
payload_hash
provenance
```

Ordering uses explicit source sequence/version where available and a canonical deterministic acceptance order inside the run. Source timestamps are evidence/freshness inputs, not a substitute for processing identity.

### 7.2 Strategy request

```text
schema_version
trace_id
run_id
canonical_input_ref
strategy_id/version
model_id/version or deterministic no-model marker
feature_schema_id/version
config_id/version
decision_deadline/budget when applicable
```

### 7.3 Successful strategy decision

```text
schema_version
trace_id
decision_id
input_ref
strategy/model/config/feature identities
decision = NO_TRADE | SIGNAL(...)
reason codes / bounded explanation
produced_at
producer identity/version
payload_hash
```

`NO_TRADE` is a successful, attributable strategy output and is valid learning evidence.

### 7.4 Decision-engine failure

A worker crash, timeout, incompatible schema, missing model or dependency failure is **not** `NO_TRADE`.

Conceptual error state:

```text
DECISION_ENGINE_UNAVAILABLE
```

with typed reason and trace identity. Quant Core records the failure truthfully and does not invent a strategy decision.

### 7.5 Simulated transition/outcome

Simulation records are deterministic functions of canonical accepted input, selected decision, immutable simulation profile and prior authoritative simulated state.

They carry exact identities for:

- simulator/version;
- fee/slippage/latency/funding assumptions;
- state revision;
- decision/source trace;
- resulting position/order/outcome state;
- transition hash/digest.

## 8. Determinism, idempotency and ordering

The target system prefers **at-least-once delivery with idempotent acceptance** over pretending transport can provide global exactly-once semantics.

Rules:

- every externally visible/cross-process operation has a stable idempotency/domain identity;
- duplicate identical payloads for the same identity are safe no-ops;
- same identity with conflicting payload/hash fails closed and becomes explicit evidence;
- authoritative state transition and outbox publication are committed atomically where both are required;
- replay operates over canonical accepted evidence/state, not arrival timing from a transient broker;
- no transport acknowledgment can outrank PostgreSQL authoritative transition state;
- trace/run/event/decision/outcome identifiers remain stable across restart and replay.

## 9. Journal, snapshot, replay and recovery

PostgreSQL authoritative state is the recovery spine.

Candidate recovery model:

1. append/commit the canonical accepted domain transition and required provenance transactionally;
2. emit asynchronous notifications through an outbox when another process/read model needs them;
3. take bounded snapshots/checkpoints for faster restoration when measured state size justifies them;
4. replay from durable canonical state/evidence after the latest valid checkpoint;
5. verify resulting digest/state revision against stored evidence where available;
6. fail closed on conflicting identity/hash or unrecoverable gap rather than silently skipping it.

The WH09 file journal remains valuable as migration evidence but is not the target runtime source of truth.

## 10. Messaging decision

A message broker is deliberately **not required for V2-S1**.

Use:

- direct private service calls for synchronous request/response boundaries;
- PostgreSQL transactions for authoritative state;
- transactional outbox for reliable asynchronous publication where needed.

Revisit NATS/JetStream when evidence shows one or more of:

- multiple independent consumers need sustained fan-out;
- process isolation/restart behavior is materially simpler with durable broker semantics;
- measured throughput/latency makes database-backed dispatch unsuitable;
- independent service scaling becomes a real requirement.

If a broker is later selected, it remains transport rather than authoritative state.

## 11. Rust↔Python boundary

Initial selected transport: **private HTTP/JSON with explicit schema versions**.

Why:

- inspectable fixtures and failure evidence;
- easy cross-language contract testing;
- minimal generation/tooling overhead for the first slice;
- adequate for the bounded decision request/response workload unless benchmark evidence proves otherwise.

Rules:

- private network/process boundary only;
- bounded payload size and strict validation;
- deadlines/timeouts are explicit;
- retry only operations that are safe through idempotency identity;
- producer health never changes a missing decision into `NO_TRADE`;
- schema compatibility is tested in Rust and Python.

gRPC/protobuf may supersede this later only with measured or maintainability evidence.

## 12. ML, AI and agent architecture

### Use now

- deterministic code for state transition, risk-free simulation mechanics, ordering, replay and recovery;
- classical/supervised ML such as LightGBM where existing WickHunter/FreqAI evidence justifies it;
- Python research/training/inference ecosystem.

### Do not use now

- LLM for synchronous trade/signal decision authority;
- autonomous agents for simulation/runtime state mutation;
- LLM-generated model activation;
- automatic challenger→active promotion;
- a feature store/experiment platform solely because it is fashionable.

### Possible later use

LLM/agents may assist asynchronously with:

- research synthesis;
- experiment diagnostics;
- operator/developer explanations;
- log/evidence triage;
- proposal generation.

Any such capability must treat external/market/text input as untrusted, isolate prompts/tools, persist provenance where outputs affect developer decisions and remain outside automatic activation/runtime authority.

## 13. Model/dataset lifecycle

Retain ADR-023 lifecycle:

```text
BASELINE | CHALLENGER | ACTIVE | ARCHIVED
```

Architectural invariants:

- dataset/feature/model/config identity is immutable/versioned;
- decision-time evidence is separated from later outcome labels;
- no-lookahead constraints apply to feature/dataset creation and evaluation;
- training creates a candidate/challenger, never ACTIVE implicitly;
- deliberate active selection is attributable and durable;
- replay/decision traces always identify the exact active/challenger/model/config used;
- model service unavailability has explicit fail-closed runtime behavior.

An independent feature store or experiment tracker is deferred until concrete scale/search/reuse needs justify another durable system.

## 14. Portal truth model

Portal is an observer/controller of the Developer Quant workflow, not an alternate state authority.

For V2-S1 it must be possible to navigate one causal trace showing:

```text
market input
-> strategy request
-> decision or explicit engine failure
-> NO_TRADE or signal
-> simulated transition/outcome where applicable
-> exact model/config/simulator identities
-> durable/replay/restart identity
```

UI labels must not collapse:

- `NO_TRADE` into missing data;
- worker unavailability into `NO_TRADE`;
- target architecture into implementation status;
- historical SHADOW/PAPER/LIVE vocabulary into current product modes.

## 15. Freqtrade retirement migration

The target end state removes Freqtrade from the persistent Developer Quant runtime while preserving it as a bounded oracle/tool where useful.

Migration principles:

1. do not modify upstream Freqtrade core merely to ease migration when an adapter/reference fixture suffices;
2. freeze representative reference behavior/fixtures before replacing a responsibility;
3. migrate one ownership boundary at a time;
4. require deterministic parity where semantics are intended to remain equivalent;
5. document and test intentional differences instead of forcing false parity;
6. retain rollback/compatibility until the replacement boundary proves restart/recovery and owner-facing behavior;
7. remove persistent-runtime dependency only when no current product workflow requires Freqtrade-owned state.

This is a strangler retirement, not a big-bang deletion.

## 16. Deployment and operations

ADR-025 remains the placement authority throughout the candidate:

- persistent Quant Core, required strategy/inference workers, Portal and long-lived collectors run on Synology when they require continuity/durable state;
- GitHub-hosted Actions runs stateless CI/test/build/scan/disposable jobs where compatible;
- images/artifacts use exact immutable identity;
- ordinary application containers do not gain container-engine socket access;
- retained self-hosted runner access remains disabled/deploy-only or equivalently narrow;
- durable state has explicit backup/recovery evidence.

No separate dedicated Linux host is introduced by v2.

## 17. Observability and causal provenance

Every material v2 trace should support correlation across process/language boundaries using stable identifiers.

Minimum observability architecture:

- structured logs with trace/run/event/decision IDs;
- metrics for input freshness, queue/inflight work, decision latency, engine-unavailable rate, NO_TRADE rate, simulation transition failures, replay mismatch and recovery outcome;
- health that distinguishes ready/degraded/unavailable rather than returning optimistic success;
- durable causal/provenance records in authoritative storage;
- exact code/image/model/config/schema identities available for developer inspection;
- no secrets/model private material unnecessarily rendered in logs/browser.

Distributed tracing technology is implementation-selectable; trace identity semantics are architecture requirements.

## 18. Security and trust boundaries

Required invariants:

- browser → same-origin Portal/BFF only;
- private Quant Core and Python worker APIs are not browser/public APIs;
- server-side schema/input validation at every cross-process boundary;
- model/strategy output is untrusted input to deterministic runtime validation/state transitions;
- no Docker/container-engine authority in ordinary Portal/Quant Core/ML containers merely for convenience;
- no private exchange credentials or real order endpoints in current v2 scope;
- immutable artifact/model/config identities and bounded read/write ownership;
- external LLM/agent inputs, if later used, receive explicit prompt/tool/data trust boundaries.

## 19. V2-S1 — first evidence-producing slice

### Scope

```text
Frozen canonical public market/WickHunter input bundle
-> Rust Quant Core acceptance/order
-> Python WickHunter strategy decision
-> Rust deterministic simulation
-> PostgreSQL causal persistence
-> Portal causal-trace view
```

The first slice intentionally avoids:

- live collector rewrite;
- broker introduction;
- gRPC migration;
- Freqtrade removal across every historical path;
- training/challenger workflow completion;
- full production-like Synology deployment certification.

Those concerns must not obscure proof of the new core ownership model.

### V2-S1 proof matrix

| Evidence | What it proves |
|---|---|
| Rust unit/property tests | deterministic state machine, ordering/idempotency invariants |
| Python unit/golden tests | WickHunter decision semantics and immutable identities |
| cross-language contract tests | Rust/Python schema compatibility and typed failures |
| frozen parity fixtures | required legacy/reference equivalence or explicit intentional difference |
| PostgreSQL integration | durable transaction/state ownership |
| deterministic replay x2 | identical canonical input/identities produce identical terminal digest |
| restart injection | mid-lifecycle restart creates no duplicate decision/outcome and restores truthfully |
| engine-unavailable fault | failure remains `DECISION_ENGINE_UNAVAILABLE`, never fabricated `NO_TRADE` |
| browser/system E2E | owner can inspect the real persisted causal trace through Portal |

### E2E data capability

Use the smallest deterministic immutable fixture that exercises the same contract/persistence/replay path. Real full-world/large market history is required only when the oracle genuinely depends on those bytes. V2-S1 does not.

## 20. Decision backlog

```yaml
- id: A-001
  decision: migration strategy
  class: ARCHITECT_DECISION
  selected_choice: C - clean-sheet deterministic Quant Core plus strangler reuse
  status: SELECTED

- id: A-002
  decision: Rust/Python/TypeScript responsibility split
  class: ARCHITECT_DECISION
  selected_choice: Rust deterministic core; Python ML/strategy; TypeScript Portal; FastAPI facade retained
  status: SELECTED

- id: A-003
  decision: simulator ownership
  class: ARCHITECT_DECISION
  selected_choice: Rust Quant Core authoritative deterministic simulation
  status: SELECTED

- id: A-004
  decision: journal/replay/recovery
  class: ARCHITECT_DECISION
  selected_choice: PostgreSQL-backed Rust domain state + outbox + replay/checkpoint semantics + immutable artifact refs
  status: SELECTED

- id: A-005
  decision: ML/LLM boundary
  class: ARCHITECT_DECISION
  selected_choice: Python ML; LLM/agents outside synchronous runtime authority
  status: SELECTED

- id: A-006
  decision: first-slice broker
  class: DEFERRED
  selected_choice: no broker for V2-S1; revisit on measured fan-out/scaling need
  status: DEFERRED
  deadline_or_gate: before a slice that requires durable multi-consumer event fan-out

- id: A-007
  decision: rewrite live market ingestion in Rust
  class: DEFERRED
  selected_choice: adapt existing collectors first
  status: DEFERRED
  deadline_or_gate: after V2-S1 canonical ingestion contract is proven

- id: A-008
  decision: Freqtrade persistent-runtime end state
  class: OWNER_DECISION_REQUIRED
  selected_choice: retire from persistent Developer Quant v2 runtime; keep reference/migration/offline roles
  status: ACCEPTED
```

## 21. Proven / derived / unknown / conflict ledger

### PROVEN at architecture base

Repository evidence at `develop@2a85a4ba54a55bb3312262e0a600a9a889ce31ce` proves at least:

- ADR-023 current Developer Quant product semantics;
- ADR-025 Synology persistent runtime/GitHub-hosted stateless plane;
- FastAPI Portal control plane and Next.js/TypeScript web application exist;
- PostgreSQL/SQLAlchemy-capable Portal persistence exists;
- public Liquid20/market-data collectors and WickHunter runtimes/evidence exist;
- deterministic Python simulator/replay implementations exist;
- a Freqtrade execution adapter/seam exists;
- no current v2 Rust Quant Core is claimed implemented by this document.

### DERIVED

- concentrating clean-sheet work in deterministic state/simulation/replay creates a clearer target owner than either a whole-product rewrite or permanent Freqtrade-centered dual ownership;
- retaining FastAPI and TypeScript avoids migration cost that does not solve the v2 deterministic ownership problem;
- no broker is necessary to prove the first causal slice.

### UNKNOWN

- exact Synology-backed S3-compatible artifact-store implementation/operational proof;
- benchmark threshold at which private HTTP/JSON should be replaced by gRPC/protobuf;
- whether later measured collector load justifies moving ingestion into Rust.

### CONFLICT

- live Issue/programme prose that still requires `DEDICATED_LINUX` is stale against later accepted ADR-025; ADR-025 wins current placement authority.

## 22. Deliberate deferrals and gates

| Decision | Deferred until |
|---|---|
| NATS/JetStream | measured multi-consumer fan-out/independent scaling need |
| gRPC/protobuf | benchmark or maintainability evidence |
| Rust live collector rewrite | after canonical ingestion contract/V2-S1 proof |
| exact object-store backend | before first implementation slice that requires object artifacts as a hard dependency |
| feature store/experiment tracker | concrete reuse/scale/search need |
| deep learning | research evidence shows classical/deterministic approach is insufficient |
| LLM/agent runtime role | concrete bounded problem with explicit trust/failure model |
| Execution/Capital Gateway | separate future owner product/authority decision |
| final implementation lanes/control-plane/DAG | independent architecture qualification passes |

## 23. Architecture qualification gate

Independent `ARCHITECTURE_QUALIFICATION` must review the exact candidate PR head and attempt to falsify:

- migration rationale and ownership boundaries;
- Rust/Python/TypeScript technology split;
- deterministic simulator/journal/replay model;
- persistence and messaging decisions;
- NO_TRADE versus engine-unavailable semantics;
- Freqtrade retirement/parity/rollback strategy;
- ML/AI/agent boundaries;
- Portal truth/same-origin boundary;
- Synology/GitHub placement compatibility;
- security and trust boundaries;
- V2-S1 evidence sufficiency;
- whether any required-now decision is accidentally deferred.

Qualification failure does not silently mutate this architecture. Findings must be resolved through a bounded architecture update and a fresh exact-head qualification.

## 24. Promotion and implementation boundary

After qualification has no unresolved current-gate P0/P1 architecture blocker, a **separate bounded architecture-promotion change** may make ADR-026/the v2 target binding and update explicit supersession/refinement relationships.

Only after the architecture-before-execution gate passes may a separate execution-governance package freeze implementation lanes, ownership leases, dependency DAG or a mutating control-plane profile.

This candidate itself is not runtime implementation authority and is not evidence that any v2 component has been coded, deployed or E2E proven.
