# Quant Platform v2 execution governance design

Status: **DESIGN ONLY — owner-approved direction, pending written-spec review**  
Date: `2026-08-28`  
Repository: `blakinio/freqtrade`  
Trusted design base: `develop@7aa9ce89d36adb503c83b20ffee8c9599982b33b`  
Binding architecture: ADR-023 + ADR-025 + ADR-026 as promoted by ADR-027

## 1. Purpose

This design defines the execution-governance layer that must exist before any mutating Quant Platform v2 implementation begins.

It converts the accepted v2 target architecture into a narrow programme-execution contract: one coordinator, explicit implementation lanes, exact allocation records, dependency/merge ordering, fail-closed writer admission, independent validation, and a hard entry gate for the reference/parity oracle plus canonical WickHunter/WH09 fixture.

This document is not the execution-governance implementation and does not activate any v2 lane. No Rust/Python/Portal runtime code, deployment, model activation, exchange credential use, real order path, withdrawal or real-capital authority is created by this design.

## 2. Authority hierarchy

The execution-governance package is subordinate to current repository and architecture authority.

Precedence remains:

1. system/owner instructions and applicable repository `AGENTS` contracts;
2. accepted ADR-023 product authority;
3. accepted ADR-025 runtime/CI-placement authority;
4. ADR-026/ADR-027 Quant Platform v2 target authority;
5. repository-wide execution/risk/closeout contracts, including `PROJECT_LANES.json`, `EXECUTION_PROTOCOL.md`, `RISK_BASED_EXECUTION_POLICY.json`, and `TASK_CLOSEOUT_AUDIT_E2E.md`;
6. this Quant v2 programme overlay;
7. individual coordinator-issued allocations and worker checkpoints.

The v2 overlay may narrow authority but may never widen product, deployment, credential, protected-environment, model-activation, destructive-operation, or real-capital authority.

Oteryn/Oteryn-Game is a reference implementation/design precedent only. It is not authority for this repository, and no Oteryn role name, topology, or control-plane rule is inherited merely because it exists there.

## 3. Selected approach

Use a **dedicated Quant v2 execution-governance overlay** while reusing the repository-wide execution machinery.

`docs/agents/PROJECT_LANES.json` remains the repo-wide source for generic lease/checkpoint/decomposition/validation defaults. `docs/agents/EXECUTION_PROTOCOL.md` remains the generic one-writer, exact-state, branch, checkpoint, validation and closeout contract.

The Quant v2 overlay adds only programme-specific semantics that those generic contracts do not know:

- the v2 coordinator role;
- the V2-S1 dependency DAG;
- lane-specific allowed path families;
- exact allocation schema;
- entry-evidence requirements;
- shared-contract serialization;
- merge-wave ordering;
- legacy executor fences;
- v2-specific negative validation cases.

It does **not** create a second repo-wide task/lease system.

## 4. Alternatives rejected

### 4.1 Expand `PROJECT_LANES.json` into the full V2 control plane

Rejected because it would mix generic repository routing with one programme's detailed authority and dependency graph. It would make ordinary Freqtrade/Portal/WickHunter tasks depend on v2-specific semantics and increase the blast radius of future governance changes.

### 4.2 One permanent prompt/lead role for every V2 lane

Rejected for V2-S1 because it creates more static authority than the first slice needs. Durable lane identity belongs in machine-readable governance plus coordinator-issued task allocations. A lane may use a specialized worker prompt later when evidence shows the role is repeatedly useful; the prompt must not become the authority source.

## 5. Two-layer execution model

### Layer A — repository execution policy

Inherited, not duplicated:

- branch/path single-writer rule;
- dedicated branch for writes;
- current repo lease/checkpoint/staleness defaults;
- exact-state reconstruction after interruption;
- risk-based validation and closeout;
- merge to `develop` through normal repository lifecycle;
- independent audit when selected by risk;
- no authority from Issue/PR/task prose alone.

### Layer B — Quant v2 programme overlay

New, narrow authority:

- programme ID `quant-v2`;
- coordinator role `quant-v2-implementation-coordinator`;
- programme state machine;
- lane DAG and merge waves;
- allocation admission/fencing;
- entry-evidence gate;
- shared-surface ownership;
- v2-specific command routing and legacy fences.

When the two layers differ, the more restrictive rule wins.

## 6. Canonical implementation artifacts

The later execution-governance implementation package must create/update these canonical surfaces:

1. `docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json` — machine-readable programme/DAG/allocation contract; canonical v2 execution authority.
2. `docs/agents/prompts/QUANT_V2_IMPLEMENTATION_COORDINATOR.md` — coordinator behavior; must defer to the machine-readable authority rather than restate it inconsistently.
3. `docs/agents/evals/QUANT_V2_IMPLEMENTATION_COORDINATOR_V1.md` — deterministic/manual prompt regression matrix for positive, negative, stale-state, overlap, dependency, injection and legacy-routing cases.
4. `docs/agents/prompts/AGENT_COMMANDS.md` — owner aliases `Quant: implementacja v2`, `Quant: implementacja v2 dalej`, and `Quant: implementacja v2 status`, plus the legacy PAPER fence.
5. `tools/agents/validate_quant_v2_execution_governance.py` — deterministic schema/invariant/task-allocation validator.
6. `tests/ci/test_quant_v2_execution_governance.py` — regression tests for the machine contract and routing/fail-closed invariants.
7. Minimal pointers in root/agent instructions only where needed to make the canonical overlay discoverable. Detailed lane semantics must not be duplicated into `AGENTS.md`.

`PROJECT_LANES.json` is intentionally not converted into a V2 DAG. If implementation needs a minimal keyword/pointer for discoverability, it may add one only if the dedicated overlay remains the sole V2 lane/dependency authority.

## 7. Programme state machine

Canonical programme states:

```text
DESIGN_ONLY
  -> GOVERNANCE_ACCEPTED_STANDBY
  -> ENTRY_EVIDENCE_PENDING
  -> READY_FOR_BOOTSTRAP
  -> IMPLEMENTING
  -> S1_INTEGRATION_READY
  -> S1_TERMINAL
```

Fail-closed side states:

```text
BLOCKED
REVOKED
```

Semantics:

- `DESIGN_ONLY`: current state of this spec. No v2 implementation allocations exist.
- `GOVERNANCE_ACCEPTED_STANDBY`: the execution-governance implementation package is merged, but no owner implementation invocation has occurred. No implementation lane may be allocated.
- `ENTRY_EVIDENCE_PENDING`: the owner invoked `Quant: implementacja v2`; only the evidence lane may operate, and it has no product/runtime implementation authority.
- `READY_FOR_BOOTSTRAP`: entry evidence is independently verified PASS at exact immutable identities.
- `IMPLEMENTING`: bootstrap merged and one or more dependency-safe implementation allocations are active.
- `S1_INTEGRATION_READY`: all predecessor lane gates required by V2-S1 are merged/terminal and exact integration inputs are frozen.
- `S1_TERMINAL`: V2-S1 proof matrix is terminal with a truthful PASS/FAIL/BLOCKED result; this state does not imply broader v2 completion.
- `BLOCKED`: a material required dependency/evidence/authority condition cannot currently be satisfied.
- `REVOKED`: coordinator or higher authority invalidated outstanding v2 allocations; workers stop writes and checkpoint.

No state transition creates deployment, private exchange, model activation or real-capital authority.

## 8. Coordinator authority

`quant-v2-implementation-coordinator` is the sole programme execution-control authority for V2-S1 allocations.

It may:

- reconstruct live v2 programme state;
- verify entry/dependency gates;
- create bounded task/branch allocations;
- choose exact owned paths inside lane-allowed path families;
- serialize shared surfaces;
- order merge waves;
- revoke/reissue allocations after drift or conflict;
- require revalidation when an upstream contract changes;
- administratively merge a lane PR only after that lane's required checks/audit are satisfied and exact-head fencing still holds;
- advance the programme state only from durable evidence.

It may not:

- self-qualify a governance or implementation diff when independent audit is required;
- grant itself or a worker deployment/protected-environment authority;
- activate models/strategies;
- use private exchange/order credentials;
- authorize real capital/orders/withdrawals;
- weaken ADR-023/025/027 or repository risk/closeout gates;
- convert missing evidence into PASS;
- bypass the V2-S1 entry evidence gate;
- allow two writers to own the same path/shared surface concurrently.

The coordinator is a **repository programme control plane**, not a container/runtime/exchange control plane.

## 9. Allocation contract

Every mutating V2 worker must have one current coordinator-issued allocation persisted in its active task record before its first write.

Minimum allocation fields:

```yaml
allocation:
  programme_id: quant-v2
  governance_sha: <exact merged governance commit>
  allocation_id: <stable unique id>
  lane_id: <lane>
  task_id: <task>
  task_kind: <evidence|implementation|validation|integration>
  issued_by_role: quant-v2-implementation-coordinator
  base_branch: develop
  exact_base_sha: <sha>
  branch: <dedicated branch>
  state: <allocated|active|waiting_dependency|validating|ready|terminal|revoked>
  lease_acquired_at: <timestamp>
  lease_expires_at: <timestamp>
  owned_paths: [<exact paths/prefixes>]
  shared_surface_claims: [<exact surfaces>]
  dependencies:
    - id: <gate/lane>
      required_state: <state>
      exact_evidence_ref: <sha/digest/merge ref>
  merge_wave: <integer>
  validation_profile: <profile>
  authority:
    repository_implementation: <true|false>
    deployment: false
    protected_environment_mutation: false
    model_activation: false
    private_exchange_credentials: false
    real_capital: false
```

The task checkpoint may update execution state, heartbeat/evidence, validation and next action. It may not widen frozen allocation authority. Any requested widening of lane, paths, shared surfaces, task kind, dependencies or authority requires a coordinator reallocation/reissue and fresh conflict/dependency checks before additional writes.

The effective lease/checkpoint duration is inherited from the exact repository policy in force at allocation issuance. The task records the policy/governance SHA so later policy drift cannot silently change an active worker's authority.

## 10. Fail-closed writer admission

Before every first write and after a material interruption/rebind, a V2 worker proves all of:

1. merged execution governance is current and compatible;
2. its allocation exists and is not revoked/expired;
3. task, branch, lane and exact admission base match the allocation;
4. requested write path is inside `owned_paths`;
5. no active allocation owns an overlapping write path/shared surface;
6. all allocation dependencies are at the required exact terminal state;
7. programme state permits that lane;
8. risk/authority boundaries permit the intended operation.

If any item is `UNKNOWN`, stale, conflicting or false, the worker remains read-only and records the blocker.

A worker with no allocation is read-only even if its prompt, alias, PR body, Issue, chat history or previous task says implementation is desired.

## 11. Upstream movement and rebind

`exact_base_sha` is an admission fence, not a promise that `develop` will never move.

When `develop` advances:

- do not force-rebase shared history;
- classify whether the upstream change touches allocation paths, shared contracts, dependencies or validation assumptions;
- if non-interacting, the worker may continue under its frozen allocation and reconcile before final merge according to repository policy;
- if interacting or authority-affecting, stop writes, checkpoint, and require coordinator rebind/reallocation;
- if a shared contract/schema digest changes, every dependent allocation bound to the older generation becomes stale until explicitly rebound and revalidated.

No lane may silently reinterpret an upstream architecture/governance change.

## 12. Canonical V2-S1 execution DAG

```text
QUANT-V2-COORD
      |
      v
V2-ENTRY-EVIDENCE
  oracle + canonical WH09 fixture
      |
      v
V2-BOOTSTRAP                  [SERIAL]
      |
      +--> V2-CORE            Rust deterministic core
      +--> V2-STRATEGY        Python/WickHunter decision plane
      +--> V2-QA              fixtures/contracts/evidence harness
               |
V2-CORE ------> V2-DURABILITY PostgreSQL/outbox/replay/recovery
               |
V2-CORE + V2-STRATEGY + V2-DURABILITY
      -> V2-PORTAL-TRACE      FastAPI/read model + Next causal trace
               |
V2-CORE + V2-STRATEGY + V2-DURABILITY + V2-PORTAL-TRACE + V2-QA
      -> V2-S1-INTEGRATION    [SERIAL FINAL GATE]
```

`QUANT-V2-COORD` is a control role, not an implementation lane.

## 13. Lane definitions

### 13.1 V2-ENTRY-EVIDENCE — merge wave 10

Purpose: prove the exact inputs required before implementation.

Authority: evidence/validation only. No runtime/product implementation.

Required outputs:

- exact reference/parity-oracle identity and reproducible invocation/fixture contract;
- exact canonical WickHunter/WH09 fixture identity;
- public/replay-only provenance and protected-holdout non-use evidence;
- frozen expected decisions/failures needed by the V2-S1 proof matrix;
- independent verification result `PASS | FAIL | BLOCKED`.

Only `PASS` permits `V2-BOOTSTRAP` allocation.

### 13.2 V2-BOOTSTRAP — merge wave 20, serial

Purpose: establish the first implementation skeleton and shared contract generation after entry evidence passes.

Allowed path families must be narrowly frozen in the actual allocation. The intended programme roots are:

- new Rust Quant Core under `quant_core/**`;
- project-specific cross-language schemas/fixtures under `ai_platform/contracts/quant_v2/**`;
- project-specific Python v2 capability under `ai_platform/quant_v2/**`;
- bounded task/test/CI surfaces required to prove the scaffold.

Bootstrap owns the initial shared contract generation and must publish exact schema/fixture digests before parallel child lanes begin.

### 13.3 V2-CORE — merge wave 30

Purpose: Rust deterministic acceptance/order/idempotency/simulation/causal state and typed decision lifecycle.

Default allowed family: `quant_core/**`, excluding any shared surface currently claimed by another lane.

Must preserve `NO_TRADE` as successful attributable output and `DECISION_ENGINE_UNAVAILABLE` as a distinct fail-closed failure.

### 13.4 V2-STRATEGY — merge wave 30

Purpose: Python WickHunter strategy decision adapter/semantics and immutable strategy/model/config/feature identity contract.

Default allowed family: `ai_platform/quant_v2/**` plus focused project tests.

It does not own authoritative simulation state or ordering/recovery semantics.

### 13.5 V2-QA — merge wave 30

Purpose: frozen fixtures, cross-language contract harnesses, parity/intentional-difference evidence, deterministic replay/restart/fault proof infrastructure.

QA may read all V2 implementation surfaces but writes only its explicitly allocated test/fixture/evidence paths. It cannot modify production code to make tests pass.

### 13.6 V2-DURABILITY — merge wave 40

Dependency: V2-CORE foundational contract is merged and frozen.

Purpose: PostgreSQL authoritative causal persistence, transactional state/outbox, replay/checkpoint/restart recovery and conflict/fail-closed semantics.

Any migration/shared-schema path is a serialized shared surface and requires explicit coordinator claim.

### 13.7 V2-PORTAL-TRACE — merge wave 50

Dependencies: exact merged Core, Strategy and Durability contract generations required by the trace.

Purpose: FastAPI/read-model and Next.js owner-facing causal trace for market input -> request -> decision/failure -> simulation/outcome -> identities/recovery.

Portal remains observer/controller, not alternate deterministic state authority.

### 13.8 V2-S1-INTEGRATION — merge wave 60, serial final gate

Dependencies: all V2-S1 predecessor lane gates are merged/terminal and fixture/schema generations are frozen.

Purpose: integrate and prove the first accepted slice, not broaden scope.

It must execute the complete V2-S1 proof matrix and return a truthful terminal result. It may perform bounded integration repairs only inside explicitly allocated integration paths; material lane defects route back to the owning lane rather than being hidden in integration glue.

## 14. Path ownership and shared surfaces

The machine overlay defines **allowed path families**; each allocation defines the smaller exact `owned_paths` actually writable by that worker.

Rules:

- one active writer per exact path/prefix;
- read-only overlap is allowed;
- an allowed path family is not itself an allocation;
- no wildcard such as the repository root may be allocated to a child lane;
- upstream/vendor `freqtrade/**` remains read-only unless a separate architecture/authority decision proves an extension point cannot satisfy a required capability;
- cross-language schemas, shared stable IDs, database migration inventories, common generated artifacts and programme-governance files are serialized shared surfaces;
- a shared surface may be transferred only after the current owner checkpoints/releases it and the coordinator issues the next claim;
- changing a shared contract generation invalidates downstream evidence bound to the old digest until explicit rebind/revalidation.

The coordinator owns allocation/governance records, not child production-code paths.

## 15. Entry-evidence contract

V2-S1 may not enter implementation on a vague statement that legacy behavior or WH09 data exists.

### Reference/parity oracle PASS requires

- exact repository revision/path/tool identity;
- exact invocation or deterministic fixture materialization procedure;
- bounded input identity/digest;
- expected output/digest or explicit semantic oracle;
- coverage of the behavior V2-S1 intends to preserve or intentionally change;
- proof that evidence is reproducible and not dependent on mutable transient state.

### Canonical WickHunter/WH09 fixture PASS requires

- exact immutable fixture identity/digest;
- public/replay provenance compatible with ADR-023;
- no private trading credentials or live-capital dependency;
- no protected-holdout leakage;
- at least the decision/failure cases required to distinguish `NO_TRADE`, signal and engine-unavailable behavior where the selected proof matrix needs them;
- deterministic expected semantics independent of legacy file/process layout.

Missing, ambiguous or stale evidence is `BLOCKED/UNKNOWN`, never PASS.

## 16. Shared contract generation

Every Rust/Python/Portal cross-language contract used by V2-S1 has a stable `schema_version` plus immutable generation identity/digest.

Bootstrap publishes generation 1. Later shared-contract changes require:

1. serialized coordinator claim;
2. Rust and Python compatibility tests;
3. migration/compatibility classification;
4. updated fixture digest where affected;
5. explicit invalidation/rebind of dependent allocations;
6. exact-head CI before the new generation becomes dependency-ready.

No lane may locally fork a schema and call it compatible.

## 17. Merge and dependency discipline

Merge wave establishes dependency order, not a reason to merge incomplete work.

- wave 10 must terminally PASS before wave 20 can be allocated;
- wave 20 must merge before wave 30 allocations;
- wave 30 lanes may work concurrently only with non-overlapping owned/shared paths;
- durability waits for the exact required Core foundation;
- Portal trace waits for exact Core/Strategy/Durability contract generations;
- S1 integration is last and serial;
- every PR is rechecked against current `develop`, dependencies, review state and exact-head CI immediately before merge;
- a merged predecessor SHA/digest is recorded in downstream allocation dependencies;
- a later change to a predecessor that invalidates downstream assumptions requires explicit coordinator reconciliation.

No worker self-declares a dependency satisfied.

## 18. Validation and independent audit

The execution-governance implementation package is `governance_or_ci` risk and therefore requires:

- deterministic policy/schema regression;
- trusted-base self-validation;
- exact-final-head relevant CI;
- genuinely independent final-diff audit before merge.

Runtime/browser E2E is not applicable to the governance package itself because it does not change user/runtime behavior.

Later V2 implementation tasks derive their own risk gates. V2-S1 integration must additionally execute the architecture proof matrix:

- Rust deterministic/property tests;
- Python golden tests;
- Rust/Python cross-language contract tests;
- frozen parity/intentional-difference fixtures;
- PostgreSQL integration;
- deterministic replay twice with identical terminal digest;
- restart injection with no duplicate decision/outcome;
- engine-unavailable fault preserving `DECISION_ENGINE_UNAVAILABLE`;
- real owner-facing Portal/browser/system causal-trace E2E.

Independent audit is separate from worker self-review. A worker or coordinator must not qualify a material diff it authored in the same context when policy requires independence.

## 19. Legacy PAPER executor fence

The current `WDROŻENIE PAPER` / `PAPER_PLATFORM_EXECUTOR.md` path is legacy/superseded programme compatibility, not Quant v2 execution authority.

The governance implementation must make this explicit with a machine-readable and prompt-routing invariant equivalent to:

```yaml
legacy_paper_executor:
  quant_v2_authority: false
  may_allocate_quant_v2_lanes: false
  may_mutate_quant_v2_governance: false
  treatment: legacy_closeout_or_reclassification_only
```

`WDROŻENIE PAPER`, `WDROŻENIE PAPER dalej`, an old PAPER task, an old prompt, or historical mode vocabulary may never create/take over a V2 allocation.

Existing valid legacy work is not deleted by this fence. It must be reclassified under current ADR-023/025/027 authority before further target-driven mutation.

## 20. Owner command routing

After the execution-governance implementation package is merged, add:

### `Quant: implementacja v2`

- load the canonical coordinator prompt plus machine overlay;
- reconstruct current programme state;
- if in `GOVERNANCE_ACCEPTED_STANDBY`, enter `ENTRY_EVIDENCE_PENDING` and allocate only V2-ENTRY-EVIDENCE;
- if a valid programme already exists, resume it rather than duplicate it;
- never skip entry evidence or create child implementation allocations from the alias alone.

### `Quant: implementacja v2 dalej`

Resume the exact safe coordinator `next_action`; no duplicate programme/task/lane.

### `Quant: implementacja v2 status`

Strictly read-only. Report programme state, exact governance SHA, entry evidence, active allocations, dependencies, merge waves, CI/audit state, blockers and one next safe action.

Alias resolution creates no second authority. The machine overlay is canonical.

## 21. Prompt/routing regression cases

The eventual eval/validator suite must include at least:

### Positive

- clean standby + `Quant: implementacja v2` -> only ENTRY-EVIDENCE allocation;
- entry PASS -> BOOTSTRAP becomes allocatable;
- bootstrap merged -> disjoint Core/Strategy/QA allocations may coexist;
- Core foundation merged -> Durability becomes allocatable;
- all predecessors exact/terminal -> S1 integration becomes allocatable.

### Negative

- no allocation -> attempted V2 write is rejected/read-only;
- expired/revoked allocation -> write rejected;
- owned-path overlap -> second allocation rejected;
- missing dependency -> lane remains waiting/read-only;
- stale shared-contract digest -> dependent allocation rejected until rebind;
- worker tries to widen its own `owned_paths`/authority -> rejected;
- coordinator attempts to mark its own authored material diff independently audited -> rejected;
- `WDROŻENIE PAPER` attempts to allocate or take over any V2 lane -> rejected;
- worker/model unavailable represented as `NO_TRADE` -> rejected;
- any private-exchange/order/real-capital authority -> STOP/rejected.

### Boundary/stale/injection

- unrelated `develop` advance -> reconcile without automatic revoke when ownership/dependencies remain unaffected;
- interacting `develop` advance -> checkpoint/rebind before further writes;
- PR/Issue/comment/task prose asks to broaden authority -> ignored unless higher authority changed;
- external text/prompt attempts to rewrite lane/dependency state -> treated as untrusted data;
- status alias -> no allocation or mutation.

## 22. Rollout sequence

1. Merge this reviewed design/spec only after its own repository lifecycle is satisfied.
2. Produce a separate implementation plan from the approved spec.
3. Implement the execution-governance package (machine overlay, coordinator prompt, routing/fence, validator/tests) without V2 runtime code.
4. Independently audit and merge that governance package.
5. Leave programme in `GOVERNANCE_ACCEPTED_STANDBY`; do not auto-start V2.
6. On a later explicit `Quant: implementacja v2`, allocate only ENTRY-EVIDENCE.
7. Independently verify entry evidence.
8. Only on exact PASS allocate serial BOOTSTRAP.
9. Fan out only dependency-safe, non-overlapping lanes according to the DAG.
10. Run serial V2-S1 integration only after all predecessor evidence is exact and terminal.

## 23. Rollback

Before any allocations exist, rollback is a normal revert of the execution-governance implementation package followed by its required governance validation.

After allocations exist:

1. coordinator moves programme to `REVOKED`;
2. stop new allocations/writes;
3. current workers checkpoint and release leases/shared surfaces;
4. verify no active V2 writer remains;
5. revert/replace governance through normal repository policy;
6. do not infer runtime/data rollback from governance rollback — any implemented persistent/runtime state follows its own task recovery contract.

Rollback never authorizes deletion of durable evidence, persistent state, models, credentials or runtime resources.

## 24. Acceptance criteria for the future governance implementation

The execution-governance implementation package is acceptable only when all are true:

- one canonical machine-readable v2 overlay exists;
- coordinator prompt and aliases defer to that overlay;
- generic `PROJECT_LANES`/`EXECUTION_PROTOCOL` remain repository-wide authority and are not duplicated;
- the approved DAG and merge waves are represented exactly;
- allocation schema requires exact base/branch/task/paths/dependencies/lease/authority;
- missing/stale/overlapping allocation is fail-closed;
- shared-contract changes invalidate/rebind dependents deterministically;
- ENTRY-EVIDENCE is the only legal pre-bootstrap lane and cannot mutate runtime/product code;
- oracle + canonical WH09 fixture are required PASS gates, not assumed facts;
- legacy PAPER executor has `quant_v2_authority: false` semantics;
- no deployment/model/private-exchange/real-capital authority is introduced;
- deterministic positive/negative/boundary/stale/injection regressions pass;
- trusted-base self-validation passes;
- exact-final-head relevant CI passes;
- genuinely independent final-diff audit has no unresolved material finding;
- merge does not itself start V2 implementation.

## 25. Current design conclusion

The selected structure intentionally keeps V2 execution governance smaller than a full multi-agent framework: one coordinator, one static machine overlay, durable task-based allocation instances, seven bounded V2-S1 lanes plus final integration, and existing repository lease/risk/closeout machinery underneath.

This is sufficient to prevent duplicate authority and unsafe parallel writes while allowing useful Core/Strategy/QA parallelism after the evidence and bootstrap barriers. It preserves ADR-027's architecture-before-execution rule and keeps all runtime/deployment/model/private-exchange/real-capital authority outside the governance package.
