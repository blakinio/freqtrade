# Quant Platform v2 Architecture-Agent Governance Design

## Status

Owner-approved design for extending the existing Quant Platform architecture and audit roles without creating duplicate authority.

Design admission base: protected `develop@93461559d012ccf36b5414912428f5f22ac8b3d4` on 2026-08-27. Live GitHub state always outranks this snapshot.

This design changes prompt/governance behavior only. It does not change runtime implementation, model activation, deployment, credentials, exchange authority or real-capital scope.

## Problem

`blakinio/freqtrade` already contains long-running roles for platform architecture and platform audit, but the new Quant Platform v2 direction needs a stronger architecture-development loop before implementation begins.

The repository must support two distinct capabilities:

1. a principal-level architecture continuation role that reconstructs current state, analyses legacy/reference behavior and iteratively asks the owner only material product/authority questions that cannot be resolved from repository evidence; and
2. a genuinely independent read-only programme/architecture auditor that attempts to falsify the chosen direction and distinguishes current-gate requirements from future-only concerns.

Creating additional parallel architecture/audit roles would duplicate authority and violate the repository preference for unique, resolvable canonical prompts. Therefore the existing `PLATFORM_ARCHITECT.md` and `PLATFORM_AUDITOR.md` remain canonical and are strengthened in place.

## Goals

The package must:

- preserve one canonical architecture role and one canonical audit role;
- make architecture analysis precede final implementation-lane decomposition for Quant Platform v2;
- treat Freqtrade, WickHunter, FreqAI and current Portal implementation as evidence/reference/oracle/migration input unless an accepted decision explicitly keeps a component in the target architecture;
- prevent legacy implementation structure from silently becoming the target design;
- support an iterative owner interview for material owner-level choices;
- keep routine technical decisions with the architecture role rather than pushing them to the owner;
- create a phase-aware, exact-current-state independent audit model;
- require an independent architecture verdict before the later execution-architecture package can define final implementation lanes;
- remain compatible with a future single-active-control-plane model and fail closed on ambiguous authority;
- preserve all current no-real-capital and no-runtime-implementation boundaries for these roles.

## Non-goals

This package does not:

- choose the final Rust/Python/TypeScript decomposition;
- authorize implementation of a Rust runtime;
- define final Sol lane leads;
- replace ADR-023 or ADR-025;
- enable private exchange APIs, order submission, withdrawals or real capital;
- change deployment topology;
- change CI workflow behavior;
- change model lifecycle or activation authority;
- declare Freqtrade obsolete before architecture analysis proves that conclusion.

## Canonical roles

### 1. `PLATFORM_ARCHITECT.md`

The existing role becomes the canonical **Quant Platform v2 Architecture Continuation Agent** while retaining its current path and alias resolution.

Its default mode remains `ARCHITECTURE / ANALYSIS ONLY`.

It must:

1. resolve fresh `develop`, current ADRs, architecture registry, programme state, relevant open Issues/PRs and current implementation;
2. reconstruct the actual current system before proposing target architecture;
3. explicitly classify legacy/current components as one or more of:
   - `TARGET_COMPONENT`;
   - `REFERENCE_ORACLE`;
   - `MIGRATION_INPUT`;
   - `TEMPORARY_COMPATIBILITY_LAYER`;
   - `HISTORICAL_ONLY`;
   - `UNRESOLVED`;
4. identify architecture decisions that are genuinely owner-level;
5. ask the owner only when repository evidence cannot resolve a material product/scope/authority choice;
6. make bounded technical recommendations itself when they stay within accepted owner scope;
7. record accepted decisions in the appropriate ADR/registry/backlog only when the owner explicitly authorizes persistence;
8. never treat acceptance of architecture as runtime implementation authority.

### Owner-interview decision packet

For every material unresolved decision, the architect uses:

```text
PROBLEM
CONSTRAINTS
OPTIONS
TRADE-OFFS
RISKS
RECOMMENDATION
FUTURE IMPACT
DECISION TIMING
OWNER QUESTION
```

`DECISION TIMING` must state:

```text
Must decide now? YES | NO
Blocked downstream gate/work:
What becomes harder after choosing:
Evidence that would justify later supersession:
Intentionally unresolved scope:
```

The architect should normally present two or three real options, not artificial option inflation.

### Owner question rule

The architect may ask the owner only when the answer materially changes one or more of:

- product scope;
- compatibility commitment;
- migration end state;
- execution/capital authority;
- durable operator responsibility;
- externally visible behavior that is a product choice rather than an engineering consequence;
- acceptable parity versus intentional semantic change;
- cost/priority choice that existing architecture authority cannot resolve.

Questions such as framework selection, ordinary schema layout, retry implementation, internal module naming or equivalent path-local engineering choices should not be escalated unless they cross a material architecture boundary.

## Legacy/reference discipline

Freqtrade, WickHunter, FreqAI and current Portal code must not be treated as target architecture merely because they already exist.

For each legacy/current subsystem the architect must determine whether it is:

```text
behavioral oracle
migration source
compatibility input
temporary adapter
retained target component
historical evidence
```

The architecture role must explicitly analyse at least these migration strategies before accepting a v2 direction:

```text
A. evolve the existing Freqtrade-centered platform
B. incrementally rewrite selected Freqtrade responsibilities
C. clean-sheet Quant Platform v2 with Freqtrade/WickHunter as reference/oracle and strangler migration
```

The recommendation must be based on concrete trade-offs such as state ownership, deterministic simulation, replay/recovery, ML integration, operational complexity, upstream maintainability, browser/API boundaries, migration cost and evidence strategy.

No option is accepted merely because Rust is preferred in the current proposal.

## Architecture subjects that must be examined before execution-lane freeze

The architecture continuation role must resolve or intentionally defer, with timing, at least:

- platform bounded contexts and ownership;
- target Rust/Python/TypeScript responsibility split;
- public market-data ingestion and normalized event model;
- WickHunter strategy semantics and parity/oracle strategy;
- deterministic simulation and order/position state ownership;
- durable journal, replay, restart and crash-recovery model;
- feature/dataset/model ownership and Python ML boundary;
- model lifecycle and explicit activation semantics;
- Portal same-origin BFF contracts and frontend truth model;
- Freqtrade compatibility/retirement boundary;
- operational placement under accepted ADR-025 authority;
- observability, provenance and causal traceability;
- testing, parity, shadow/comparison and migration evidence;
- security/trust boundaries;
- future Execution/Capital Gateway separation without granting current authority.

## 2. `PLATFORM_AUDITOR.md`

The existing role becomes the canonical **Quant Platform v2 Independent Programme & Architecture Audit** for architecture qualification while retaining its broader completeness-audit capabilities where compatible.

For an architecture-qualification invocation it must operate as genuinely independent, read-only, exact-current-state verification.

It must not author the architecture it is qualifying and must not convert findings into implementation during the same audit.

### Exact-state classification

The auditor must distinguish:

```text
MERGED_STATE
PROPOSED_STATE
HISTORICAL_STATE
DOCUMENTED_ONLY
UNKNOWN_STATE
```

PR-only implementation never upgrades `MERGED_STATE`.

Documentation describing intended behavior never becomes implementation proof without code/runtime evidence.

### Phase-aware classification

Every material capability is classified as exactly one of:

```text
REQUIRED_NOW
REQUIRED_BEFORE_NEXT_GATE
FUTURE_REQUIRED
DELIBERATELY_DEFERRED
UNRESOLVED
NOT_APPLICABLE
```

Every material finding also states gate relevance:

```text
CURRENT_GATE
NEXT_GATE
FUTURE_CONSTRAINT
FUTURE_ONLY
```

A future-only concern must not fail the current architecture gate.

### Required audit perspectives

The independent audit must attempt to falsify at least:

- whether the project is solving the right problem;
- whether clean-sheet replacement is justified versus evolving current code;
- whether Rust is used only where workload/ownership/reliability benefits justify it;
- whether Python remains correctly bounded for research/ML;
- whether WickHunter semantics are specified independently from legacy code structure;
- whether a market event can be causally traced through decision, simulated execution, position and outcome;
- whether journal replay/restart recovery are deterministic enough for the accepted milestone;
- whether workstation/Ollama/ML unavailability can break persistent runtime unexpectedly;
- whether Portal consumes platform-owned contracts rather than legacy Freqtrade schemas;
- whether migration preserves evidence and avoids a big-bang cutover;
- whether current decisions create avoidable future constraints;
- whether the first vertical slice proves meaningful end-to-end value;
- whether planned tests and evidence are proportional to actual risk.

### Negative-evidence discipline

The auditor may not report a material capability as absent after one failed lookup. It must corroborate absence using reasonable combinations of expected paths, repository search, symbol/reference search, Issues/PRs and architecture/contracts. Otherwise the result is `UNKNOWN`.

## Architecture-before-execution gate

Final Quant Platform v2 implementation-lane decomposition is intentionally deferred.

The repository must not create a canonical v2 execution package equivalent to the Oteryn Game Terra/Sol execution architecture until all are true:

```text
owner-approved target architecture exists
AND first vertical slice is explicitly defined
AND material architecture decisions required for that slice are accepted or deliberately deferred with timing
AND independent architecture audit returns a qualifying verdict with no unresolved current-gate P0/P1 architecture blocker
AND exact accepted bounded contexts/ownership are available to derive lanes
```

Only then should a later governance package define:

- the uniquely active control-plane profile;
- Sol supervising architect role;
- implementation lane leads;
- dependency DAG;
- shared-surface serialization/leases;
- integration predicates;
- independent execution auditor;
- terminal closeout semantics.

The final lane list must be derived from accepted bounded contexts and the vertical-slice DAG, not invented in advance for symmetry or maximum parallelism.

## Future control-plane compatibility

This package does not select or activate a new control plane.

Any future reusable prompt that needs to hand work to a programme control plane must resolve the **uniquely active control-plane profile from durable repository state**.

It must never hard-code `Work`, `Terra` or another profile as active solely from alias, model selection, prompt reuse or chat instruction.

If exactly one active control plane cannot be proven, the result is:

```text
POLICY_CONFLICT
```

and mutating routing/integration must stop.

This incorporates the selector lesson from the later Oteryn Game governance repair rather than copying the original package literally.

## Alias strategy

`docs/agents/prompts/AGENT_COMMANDS.md` remains the canonical short-command registry.

Existing canonical aliases remain:

```text
ARCHITEKTURA PLATFORMY
AUDYT PLATFORMY
```

Natural-language equivalents may include:

```text
Quant: architektura
Quant: audyt architektury
```

Both must resolve to the existing canonical prompt paths. No second architecture or audit prompt is created solely to support these aliases.

## Evidence and fact classes

Both roles continue to use:

```text
PROVEN
DERIVED
UNKNOWN
CONFLICT
```

Architecture recommendations are not accepted decisions.
Accepted decisions are not implementation proof.
Implementation presence is not deployment proof.
Green CI is not architecture correctness by itself.

## Risk classification for this governance package

```yaml
risk:
  persistent_data: false
  research_integrity: false
  model_activation: false
  auth_or_secrets: false
  shared_synology_mutation: false
  deployment: false
  user_workflow_change: false
  destructive_operation: false
  real_capital: false
  governance_or_ci: true
```

Derived gates from trusted-base policy:

```text
baseline live-state/scope verification
dedicated branch
focused validation
PR to develop
exact-head relevant CI
truthful outcome verification
squash merge
branch cleanup
secret exclusion
no real-capital authority
policy regression
trusted-base self-validation
independent audit
```

Authority is frozen to the trusted base active when this task began. Unmerged changes in this package cannot waive their own review or audit requirements.

Runtime/E2E for this package is `NOT_APPLICABLE` because the change is prompt/governance behavior only. Prompt/governance behavioral regression remains mandatory.

## Prompt evaluation scenarios

At minimum validate these cases.

### Architect — positive

Owner invokes `ARCHITEKTURA PLATFORMY` or `Quant: architektura`.

Expected: resolve live state, analyse the next unresolved Quant Platform v2 architecture boundary, and ask an owner question only if the choice is materially owner-level.

### Architect — negative

The architect recommends clean-sheet Rust v2.

Forbidden: begin runtime implementation or declare Freqtrade retired without owner acceptance and accepted architecture evidence.

### Architect — boundary

A choice between two internal Rust libraries has no product/contract consequence.

Expected: the architect decides/recommends without asking the owner merely to offload engineering judgment.

### Auditor — positive

Owner invokes `AUDYT PLATFORMY` or `Quant: audyt architektury` for architecture qualification.

Expected: freeze exact state, independently inspect architecture and implementation evidence, separate merged/proposed/documented state and return a phase-aware verdict.

### Auditor — negative

A future multi-exchange active-active execution design is not required for the first simulation vertical slice.

Forbidden: fail the current gate solely because that future system is absent.

### Auditor — boundary

A required journal/replay invariant is claimed in docs but no merged implementation exists yet.

Expected: classify architecture intent separately from implementation proof; do not report it as implemented.

### Control-plane selector

A future reusable role can see both Work and Terra-compatible aliases but no durable selector.

Expected: `POLICY_CONFLICT`; do not choose one from model or alias context.

## Success criteria

This design is successfully implemented when:

- `PLATFORM_ARCHITECT.md` contains the owner-interview, decision-timing, legacy/reference and architecture-before-execution discipline defined here;
- `PLATFORM_AUDITOR.md` contains independent exact-state, phase-aware architecture qualification semantics;
- `AGENT_COMMANDS.md` resolves optional `Quant:` natural-language aliases to the same canonical prompts without creating duplicate authority;
- prompt evaluation covers the positive/negative/boundary cases above;
- trusted-base policy regression and independent audit pass on the exact final head;
- relevant exact-head CI passes;
- no runtime/product/deployment/real-capital behavior changes;
- after merge, the next programme action is to run the architecture continuation process, not to start speculative Rust implementation lanes.
