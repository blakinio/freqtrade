# Quant v2 Execution Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` (or the repository-approved equivalent) and `superpowers:test-driven-development`. This plan is test-first and fail-closed.

**Goal:** Deliver the accepted Quant Platform v2 execution-governance package: one machine-readable programme contract, one canonical durable programme-state source, one fail-closed implementation coordinator, deterministic allocation admission, unambiguous owner routing, and a complete legacy PAPER fence, while leaving the governance package itself in `GOVERNANCE_ACCEPTED_STANDBY` with zero V2 implementation allocations.

**Architecture:** Keep generic execution, lease, risk and closeout behaviour authoritative in `docs/agents/PROJECT_LANES.json`, `docs/agents/EXECUTION_PROTOCOL.md`, `docs/agents/RISK_BASED_EXECUTION_POLICY.json` and `docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md`. Add one narrower static programme contract at `docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json`. After a later explicit owner activation, canonical dynamic programme truth is stored only in `docs/agents/quant_v2/PROGRAMME_STATE.json`; workers do not supply their own programme state, incumbent-allocation census or predecessor truth. The coordinator serializes all state/allocation mutations before a worker may write.

**Tech stack:** JSON, Python 3 standard library, pytest, Markdown prompt/eval contracts, repository GitHub Actions/pre-commit/CodeQL/zizmor.

**Approved spec:** `docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md`

## Global constraints

- This plan implements governance/CI only. It must not add Rust Quant Core runtime, Python V2 strategy runtime, Portal causal-trace runtime, deployment, model activation, private exchange credentials, real orders, withdrawals, or real-capital authority.
- `PROJECT_LANES.json` remains the repo-wide generic execution authority. Do not place the V2 DAG or V2 lane semantics in it.
- The governance implementation merge ends in `GOVERNANCE_ACCEPTED_STANDBY`; it must not itself issue `Quant: implementacja v2`, create a V2 allocation, create an activation receipt, or create an activated `PROGRAMME_STATE.json`.
- Absence of `docs/agents/quant_v2/PROGRAMME_STATE.json` on trusted `develop` is canonical only for **standby/no allocations**. It is never sufficient worker write authority.
- Only a later explicit owner invocation `Quant: implementacja v2` may authorize the coordinator to create a durable activation receipt and transition the canonical state to `ENTRY_EVIDENCE_PENDING`; only `V2-ENTRY-EVIDENCE` is eligible then.
- `V2-ENTRY-EVIDENCE` is the producer/verifier of the exact reference/parity oracle and canonical WickHunter/WH09 fixture. Missing/UNKNOWN entry evidence is therefore allowed when admitting that lane, provided the activation/state/allocation fences pass and `repository_implementation` is exactly `false`.
- `V2-BOOTSTRAP` and all later lanes remain blocked until both `reference_parity_oracle` and `canonical_wickhunter_wh09_fixture` have exact immutable identities and independently verified `PASS` evidence in canonical programme state.
- Missing, malformed, expired, stale-governance, wrong-lane, wrong-state, dependency-unsatisfied, path-outside-lane, owned-path-overlap, shared-surface-overlap, stale/unknown predecessor evidence, incomplete state, omitted incumbent, forged activation or authority-widening allocations fail closed to read-only.
- Generic lease authority is inherited mechanically from `PROJECT_LANES.execution.lease_minutes`; the accepted value on the design base is 45 minutes and the V2 overlay must fail closed if its mirror differs from the generic source.
- `WDROŻENIE PAPER` / `PAPER_PLATFORM_EXECUTOR.md` is legacy compatibility only and must implement the full four-part fence from the approved spec: `quant_v2_authority:false`, `may_allocate_quant_v2_lanes:false`, `may_mutate_quant_v2_governance:false`, `treatment: legacy_closeout_or_reclassification_only`.
- Existing valid legacy PAPER work may be closed out, but must be reclassified under ADR-023/025/027 before any further target-driven mutation. Legacy routing may never mutate Quant-v2 governance, V2-owned paths or V2 shared surfaces.
- Oteryn is non-authoritative design precedent only.
- Governance/CI risk is true: test-first policy regression, trusted-base self-validation, exact-head CI and a fresh independent exact-head audit are mandatory before governance merge.
- Runtime/browser E2E is `NOT_APPLICABLE_WITH_REASON` for this governance-only package.

## Canonical programme-state model

The static machine contract must define exactly one dynamic state path:

`docs/agents/quant_v2/PROGRAMME_STATE.json`

Before owner activation the path must be absent and the only valid interpretation is:

```json
{
  "programme_state": "GOVERNANCE_ACCEPTED_STANDBY",
  "activation_epoch": null,
  "active_allocations": 0
}
```

A worker validator must **not** turn absence into worker authority. Only the coordinator handling the explicit owner activation command may use the absence-as-standby rule.

On a later explicit `Quant: implementacja v2`, the coordinator must first create and merge a serialized control-plane activation transaction containing:

- `docs/agents/quant_v2/activation/<activation_epoch>.json` — immutable activation receipt;
- `docs/agents/quant_v2/PROGRAMME_STATE.json` — canonical state initialized to `ENTRY_EVIDENCE_PENDING` with zero or exactly one pending ENTRY allocation transaction, depending on whether allocation issuance is combined in the same serialized control-plane PR.

The activation receipt must record at minimum:

```json
{
  "programme_id": "quant-v2",
  "governance_sha": "<exact merged governance sha>",
  "activation_epoch": "<stable unique epoch>",
  "activation_command": "Quant: implementacja v2",
  "owner_command_received": true,
  "recorded_at": "<timezone-aware timestamp>",
  "previous_programme_state": "GOVERNANCE_ACCEPTED_STANDBY"
}
```

`PROGRAMME_STATE.json` must bind to that receipt by exact path plus SHA-256 of its bytes and must contain one complete canonical snapshot:

```json
{
  "schema_version": 1,
  "programme_id": "quant-v2",
  "governance_sha": "<exact merged governance sha>",
  "state_generation": 1,
  "programme_state": "ENTRY_EVIDENCE_PENDING",
  "activation": {
    "epoch": "<same epoch>",
    "receipt_path": "docs/agents/quant_v2/activation/<epoch>.json",
    "receipt_sha256": "<64 hex>"
  },
  "allocations": [],
  "predecessors": {}
}
```

After activation, `PROGRAMME_STATE.json` is the only canonical source for:

- current programme state and generation;
- activation epoch/receipt binding;
- the **complete** active-allocation set;
- predecessor terminal state/evidence identities;
- ENTRY-EVIDENCE artifact verdicts.

Callers may not replace any of those with partial `--active-task`, `predecessor_states`, free-form programme-state flags or stale snapshots.

Every allocation issuance/revocation/rebind and every predecessor terminal-evidence update is a serialized coordinator control-plane transaction that updates canonical `PROGRAMME_STATE.json` before dependent worker writes. Each canonical allocation entry must bind to the worker task record by exact task path plus SHA-256 of the task bytes. `allocation_count` must equal the number of allocation entries; allocation IDs and task IDs must be unique. Missing entries, duplicate entries, malformed references or a task allocation not exactly represented in canonical state fail closed.

## Hard execution order

```text
Task 0: DESIGN MERGE GATE
  -> Task 1: machine programme contract + canonical-state schema
  -> Task 2: canonical-state/allocation admission validator
  -> Task 3: coordinator routing + complete legacy PAPER fence
  -> Task 4: qualify/merge/archive governance package
```

Tasks 1-3 **MUST NOT** execute on the design branch or before Task 0 is terminally successful. A plan worker that cannot prove Task 0 must stop before creating the implementation task/branch.

---

### Task 0: Mandatory design/spec/plan merge gate

**Files:** none.

- [ ] Resolve live `develop`, PR #1679 base/head, all changed paths, reviews/threads/comments and exact-head workflow runs.
- [ ] Require PR #1679 exact head to have a fresh genuinely independent design/governance audit with zero material P0/P1 findings. The authoring context may not self-qualify its own design head.
- [ ] Require latest qualifying exact-head Freqtrade CI, Risk-aware component CI, CodeQL and zizmor to be terminal success; older same-head cancellations count as superseded only by a newer successful run of the same workflow.
- [ ] Require zero unresolved blocking review/thread, `mergeable: true`, and unchanged compatible `develop` base.
- [ ] Re-resolve the PR head immediately before merge; head movement invalidates the audit.
- [ ] Guarded squash-merge PR #1679 using `expected_head_sha`.
- [ ] Re-resolve `develop` and verify the exact approved spec and implementation plan landed.
- [ ] Only after these checks pass may Task 1 create a new post-design-merge governance implementation task/branch.

Expected terminal result: `DESIGN_MERGED_QUALIFIED`. Any other result blocks Tasks 1-4.

---

### Task 1: Machine-readable V2 programme contract

**Files:**
- Create: `docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json`
- Create: `tests/ci/test_quant_v2_execution_governance.py`

#### Step 1 — RED static-contract tests

Require at minimum:

```python
assert data["schema_version"] == 1
assert data["programme_id"] == "quant-v2"
assert data["coordinator_role"] == "quant-v2-implementation-coordinator"
assert data["initial_state"] == "GOVERNANCE_ACCEPTED_STANDBY"
assert data["owner_command_required_for_activation"] is True
assert data["activation_command"] == "Quant: implementacja v2"
assert data["programme_state_store"]["path"] == "docs/agents/quant_v2/PROGRAMME_STATE.json"
assert data["programme_state_store"]["absent_means"] == "GOVERNANCE_ACCEPTED_STANDBY"
assert data["programme_state_store"]["worker_admission_requires_present_state"] is True
assert data["programme_state_store"]["complete_allocation_index_required"] is True
assert data["programme_state_store"]["canonical_predecessor_ledger_required"] is True
```

Require the approved state machine, repository-contract inheritance, generic `PROJECT_LANES` separation and lease binding:

```python
project_lanes = json.loads(PROJECT_LANES_PATH.read_text())
assert project_lanes["schema_version"] == 2
assert "v2_lane_dag" not in project_lanes
assert project_lanes["execution"]["lease_minutes"] == 45
assert data["lease_policy"] == {
    "source": "docs/agents/PROJECT_LANES.json",
    "source_field": "execution.lease_minutes",
    "max_duration_minutes": 45,
    "must_equal_source": True,
}
```

Require the full legacy fence:

```python
assert data["legacy_paper_executor"] == {
    "quant_v2_authority": False,
    "may_allocate_quant_v2_lanes": False,
    "may_mutate_quant_v2_governance": False,
    "treatment": "legacy_closeout_or_reclassification_only",
}
```

Require `entry_evidence` to block `V2-BOOTSTRAP`, **not** to pre-block the ENTRY producer lane itself.

Run focused tests and observe RED because the machine contract does not yet exist.

#### Step 2 — minimal GREEN machine contract

Create `docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json` with:

- schema/programme/coordinator/activation fields above;
- approved state transitions;
- `inherits_repository_execution_from` pointing to current generic contracts;
- exact `programme_state_store` semantics from this plan;
- lease-policy binding above;
- authority defaults all false for deployment, protected-environment mutation, model activation, private-exchange credentials and real capital;
- `entry_evidence` requiring both `reference_parity_oracle` and `canonical_wickhunter_wh09_fixture`, verdict `PASS`, as the gate for `V2-BOOTSTRAP` and later lanes;
- allocation record format `task_markdown_json_block_v1`, heading `## Quant V2 allocation`;
- shared surfaces `cross_language_schema`, `database_migration`, `stable_identity_vocabulary`, `programme_command_routing`;
- the full four-part `legacy_paper_executor` fence;
- eight V2 lane objects with approved dependencies, merge waves, serial flags and eligibility path families.

Approved dependencies remain:

```text
V2-ENTRY-EVIDENCE -> []
V2-BOOTSTRAP -> [V2-ENTRY-EVIDENCE]
V2-CORE -> [V2-BOOTSTRAP]
V2-STRATEGY -> [V2-BOOTSTRAP]
V2-QA -> [V2-BOOTSTRAP]
V2-DURABILITY -> [V2-CORE]
V2-PORTAL-TRACE -> [V2-CORE, V2-STRATEGY, V2-DURABILITY]
V2-S1-INTEGRATION -> [V2-CORE, V2-STRATEGY, V2-DURABILITY, V2-PORTAL-TRACE, V2-QA]
```

Approved eligibility path families remain exactly those in the owner-approved spec/previous plan. They are eligibility families only; a coordinator allocation grants a smaller exact `owned_paths` set.

Run focused tests to GREEN and commit only after observed GREEN.

---

### Task 2: Canonical programme-state parser and fail-closed allocation validator

**Files:**
- Create: `tools/agents/validate_quant_v2_execution_governance.py`
- Modify: `tests/ci/test_quant_v2_execution_governance.py`

**Required interfaces:**

```python
load_governance(path: Path) -> dict[str, Any]
load_repository_policy(path: Path) -> dict[str, Any]
load_programme_state(path: Path) -> dict[str, Any] | None
extract_allocation(task_path: Path) -> dict[str, Any] | None
validate_governance(governance: dict[str, Any], repository_policy: dict[str, Any]) -> list[str]
validate_programme_state(
    state: dict[str, Any] | None,
    governance: dict[str, Any],
    *,
    expected_governance_sha: str,
    activation_receipt_loader: Callable[[str], bytes],
    allow_absent_standby: bool,
) -> list[str]
validate_allocation(
    allocation: dict[str, Any],
    governance: dict[str, Any],
    repository_policy: dict[str, Any],
    programme_state: dict[str, Any],
    *,
    expected_governance_sha: str,
    now: datetime,
    task_record_path: str,
    task_record_bytes: bytes,
) -> list[str]
```

Production CLI must accept a repository root, expected merged governance SHA, task path and injected `now` for deterministic tests. It must load these canonical paths itself from that repository root:

```text
docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json
docs/agents/PROJECT_LANES.json
docs/agents/quant_v2/PROGRAMME_STATE.json
```

The production CLI must **not** accept caller-supplied programme state, repeatable `--active-task`, ad-hoc predecessor-state maps, allocation census subsets, or free-form activation flags. Test-only helpers may inject in-memory objects directly.

#### Step 1 — RED canonical-state and allocation tests

Add RED tests for all of these failures:

1. stale allocation `governance_sha`;
2. absent programme state for worker admission;
3. programme state governance SHA mismatch;
4. missing/malformed activation epoch after standby;
5. activation receipt missing, wrong path, hash mismatch, wrong command, wrong prior state or `owner_command_received != true`;
6. `allocation_count` differs from canonical allocation entry count;
7. duplicate allocation/task IDs;
8. candidate allocation missing from canonical state;
9. canonical allocation differs from the task-record allocation;
10. task-record path or SHA-256 binding mismatch;
11. omitted incumbent allocation attempt: candidate task sees a canonical incumbent and overlap must fail even though caller supplied no active-task list;
12. forged programme state for lane;
13. wrong merge wave;
14. wrong dependency ID set;
15. dependency missing from canonical predecessor ledger;
16. predecessor not in required terminal state;
17. predecessor evidence missing/malformed/non-immutable;
18. allocation dependency evidence differs from canonical predecessor evidence identity;
19. stale predecessor generation/evidence source binding;
20. expired lease;
21. lease expiry not after acquisition;
22. lease duration greater than generic `PROJECT_LANES.execution.lease_minutes`;
23. V2 governance lease mirror differs from generic source;
24. path outside lane family;
25. owned-path overlap with canonical active incumbent;
26. shared-surface overlap with canonical active incumbent;
27. forbidden authority widening;
28. malformed/missing required allocation fields;
29. `V2-ENTRY-EVIDENCE.repository_implementation` not exactly false;
30. `V2-BOOTSTRAP` with missing/UNKNOWN/non-PASS oracle or WH09 evidence.

Add the required positive regression that proves no self-deadlock:

```text
clean standby
+ explicit owner activation receipt
+ canonical state ENTRY_EVIDENCE_PENDING
+ no prior ENTRY evidence / artifacts UNKNOWN or absent
+ exact V2-ENTRY-EVIDENCE allocation
+ repository_implementation=false
=> allocation admission PASS
```

Also prove:

```text
same state + V2-BOOTSTRAP allocation + either required artifact not PASS
=> allocation admission FAIL
```

Observe RED before implementation.

#### Step 2 — minimal GREEN validator

Implement fail-closed validation in this order:

1. validate static governance and generic lease source/mirror;
2. load canonical programme state from the fixed path;
3. for worker admission, reject absent state; only coordinator activation validation may use `allow_absent_standby=True`;
4. require exact programme/governance identity, monotonic positive `state_generation`, and valid activation epoch/receipt binding for every non-standby state;
5. recompute activation receipt SHA-256 and verify normalized `Quant: implementacja v2`, `owner_command_received=true`, exact governance SHA and previous standby state;
6. validate allocation-index completeness structurally: exact count, unique IDs/task IDs and valid task-record bindings;
7. require the candidate allocation to be represented exactly once in canonical state and equal the task-record allocation;
8. derive current programme state, all active incumbents and predecessor truth only from canonical state;
9. require known lane and lane-eligible programme state;
10. require exact merge wave and exact dependency ID set;
11. for every dependency, require canonical predecessor entry, required terminal state and exact matching immutable evidence identity;
12. parse timezone-aware lease timestamps;
13. require expiry > acquisition, expiry > injected `now`, and total duration <= generic repository maximum;
14. require every owned path inside a lane eligibility prefix;
15. compare against **all** canonical active incumbents for owned-path and shared-surface overlap;
16. require all forbidden authority flags exactly false;
17. require `V2-ENTRY-EVIDENCE.repository_implementation` exactly false;
18. for `V2-ENTRY-EVIDENCE`, do **not** require its target oracle/fixture evidence to already PASS;
19. for `V2-BOOTSTRAP` and every later dependent lane, require the canonical ENTRY predecessor plus both exact artifact records with immutable identities and independent `PASS` verdicts;
20. any missing/UNKNOWN/stale/incomplete state is a validation error, never a default PASS.

Run focused tests to GREEN and commit only after observed GREEN.

#### Step 3 — coordinator state-transaction contract

Document/test that the coordinator is the only writer of canonical programme state. Before any V2 worker first write, the required control-plane state/allocation transaction must already be merged on trusted `develop` and the worker branch must start from or rebind to a develop state containing that allocation.

Allocation issuance/rebind/revocation and predecessor terminal-evidence publication are serialized control-plane mutations. Parallel workers may exist only after their non-overlapping allocations are all represented in the canonical allocation index.

---

### Task 3: Coordinator routing, prompt regression and complete legacy PAPER fence

**Files:**
- Create: `docs/agents/prompts/QUANT_V2_IMPLEMENTATION_COORDINATOR.md`
- Create: `docs/agents/evals/QUANT_V2_IMPLEMENTATION_COORDINATOR_V1.md`
- Modify: `docs/agents/prompts/AGENT_COMMANDS.md`
- Modify: `docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md`
- Modify: `tests/ci/test_quant_v2_execution_governance.py`

#### Step 1 — RED routing/fence tests

Require:

- `Quant: implementacja v2` routes exactly to `QUANT_V2_IMPLEMENTATION_COORDINATOR.md`;
- `Quant: implementacja v2` does not route to `PAPER_PLATFORM_EXECUTOR.md`;
- standby cannot issue any allocation unless the current invocation is the explicit owner activation command;
- activation first persists the durable receipt/state transition before worker authority;
- first post-activation writable V2 lane is only `V2-ENTRY-EVIDENCE`;
- the coordinator loads the canonical programme state rather than accepting partial caller state;
- the coordinator runs the validator before any V2 repository write;
- the coordinator serializes state/allocation mutations and rebinds stale interacting generations;
- the coordinator may not self-qualify a candidate it materially authored;
- no deploy/private-exchange/real-capital authority is implied;
- PAPER executor YAML and machine contract contain all four exact legacy fence fields;
- `WDROŻENIE PAPER` and `WDROŻENIE PAPER dalej` may only continue a valid legacy closeout/reclassification path, never new target-driven mutation under superseded PAPER authority;
- legacy PAPER routing rejects creating/taking over V2 lanes, editing Quant-v2 governance/state, or claiming V2-owned/shared surfaces;
- a legacy task that needs target-driven mutation must return a reclassification-required result under ADR-023/025/027 before writes.

Observe RED.

#### Step 2 — minimal GREEN coordinator/routing implementation

Create the coordinator prompt with:

```yaml
role: quant-v2-implementation-coordinator
run_scope: autonomous_program
machine_governance: docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json
programme_state: docs/agents/quant_v2/PROGRAMME_STATE.json
legacy_paper_authority: false
protected_environment_authority: false
private_trading_credential_authority: false
live_capital_authority: false
```

It must reconstruct live GitHub state on every invocation, require exact merged governance identity, use canonical programme state, persist activation before ENTRY allocation, issue exact bounded allocations through serialized control-plane transactions, validate before mutation, preserve merge waves, serialize shared surfaces, rebind stale interacting generations, and never bypass independent audit/CI/E2E gates.

Update `PAPER_PLATFORM_EXECUTOR.md` and routing to implement exactly:

```yaml
quant_v2_authority: false
may_allocate_quant_v2_lanes: false
may_mutate_quant_v2_governance: false
treatment: legacy_closeout_or_reclassification_only
```

Existing valid legacy work remains closable. New/further target-driven mutation requires reclassification first. Explicitly reject V2 governance/state, V2 lane and V2 shared-surface mutation from legacy PAPER aliases.

Create the eval document with positive, negative, stale-governance, canonical-state completeness, omitted-incumbent, forged-state, activation receipt, ENTRY-with-missing-evidence positive, BOOTSTRAP evidence-gate, expired/oversized-lease, wrong-dependency-state, evidence-mismatch, path-overlap, shared-surface-overlap, standby-activation and legacy-PAPER scenarios.

Run focused tests to GREEN and commit only after observed GREEN.

---

### Task 4: Implement, qualify, merge and archive the governance package

**Precondition:** Task 0 is terminal `DESIGN_MERGED_QUALIFIED`.

**Files:**
- Create on a new post-design-merge branch: `docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-implementation.md`
- Implement only governance/test/prompt/routing surfaces required by Tasks 1-3.

The governance implementation task itself must **not** contain a `## Quant V2 allocation` block and must state:

```yaml
runtime_access: none
programme_post_merge_state: GOVERNANCE_ACCEPTED_STANDBY
v2_s1_activation_authorized_by_this_task: false
risk:
  governance_or_ci: true
runtime_e2e: NOT_APPLICABLE_WITH_REASON
```

Execute Tasks 1-3 with TDD. Do not create `V2-ENTRY-EVIDENCE`, activation receipt, activated programme state, or any implementation allocation as part of the governance package.

Run focused governance tests plus repository-prescribed governance/CI validation. Open one truthful governance implementation PR and require exact-head CI, zero unresolved blockers and a genuinely fresh independent exact-head governance audit. The authoring context must not self-qualify its own candidate.

Squash-merge only with `expected_head_sha`. After merge verify on `develop`:

- static machine governance is present and valid;
- dynamic `docs/agents/quant_v2/PROGRAMME_STATE.json` is absent;
- therefore canonical programme state is `GOVERNANCE_ACCEPTED_STANDBY` and active allocation count is zero;
- no activation receipt exists;
- no Rust/Python/Portal runtime implementation landed;
- no runtime/deployment/model/private-exchange/real-capital authority widened;
- `WDROŻENIE PAPER` has the complete four-part legacy fence and reclassification requirement.

Archive/release the governance implementation task through repository closeout rules. Closeout must not activate the programme.

---

## Required validation matrix

| Gate | Required result |
| --- | --- |
| Task 0 design exact-head CI | PASS |
| Task 0 independent design audit | PASS_ZERO_MATERIAL_FINDINGS |
| Static machine-contract tests | RED then GREEN |
| Canonical programme-state/activation matrix | RED then GREEN |
| Complete allocation-index / omitted-incumbent matrix | RED then GREEN |
| Dependency canonical-state/evidence matrix | RED then GREEN |
| ENTRY-EVIDENCE initial-UNKNOWN positive admission | PASS |
| BOOTSTRAP exact oracle+WH09 evidence gate | RED then GREEN |
| Generic 45-minute lease inheritance matrix | RED then GREEN |
| Routing/complete PAPER fence tests | RED then GREEN |
| Governance trusted-base self-validation | PASS |
| Governance exact-head repository CI | PASS |
| Governance independent exact-head audit | PASS_ZERO_MATERIAL_FINDINGS |
| Runtime/browser E2E | NOT_APPLICABLE_WITH_REASON |
| Post-governance dynamic state file | ABSENT |
| Post-governance canonical state | GOVERNANCE_ACCEPTED_STANDBY |
| Post-governance V2 allocations | 0 |

## Stop conditions

Stop before mutation if Task 0 is not proven. During governance implementation stop only for a real authority/safety/capability blocker, conflicting path ownership, material architecture change, or failed independent audit that requires remediation. Do not stop merely because a commit or PR exists.

## Self-review against independent audit findings

- `QV2-1679-001` — **REMEDIATED:** design qualification/merge is Task 0 and a hard predecessor of Tasks 1-3.
- `QV2-1679-002` — **REMEDIATED IN PLAN:** dependency truth is no longer caller-supplied. The validator loads canonical predecessor state/evidence from `PROGRAMME_STATE.json`, verifies terminal state plus exact immutable evidence identity, and fails closed on missing/stale/mismatched records.
- `QV2-1679-003` — **REMEDIATED:** V2 governance mirrors the generic lease source and validator enforces source/mirror equality and total duration `<= PROJECT_LANES.execution.lease_minutes` plus expiry-at-`now`.
- `QV2-1679-004` — **REMEDIATED IN PLAN:** programme state, activation epoch, complete incumbent-allocation set and predecessor ledger are canonical durable state. Production validator does not accept partial active-task/predecessor/programme-state caller inputs; omitted-incumbent and forged-state negative regressions are mandatory.
- `QV2-1679-005` — **REMEDIATED IN PLAN:** ENTRY-EVIDENCE may be admitted after explicit durable activation with its target artifacts initially absent/UNKNOWN; exact artifact PASS is a BOOTSTRAP/later-lane gate, eliminating self-deadlock.
- `QV2-1679-006` — **REMEDIATED IN PLAN:** machine contract, PAPER executor and routing must enforce all four legacy-fence fields plus legacy-closeout/reclassification-only behaviour and explicit rejection of V2 governance/lane/shared-surface mutation.

The owner-approved spec remains unchanged. This remediation changes only the implementation plan and design-task checkpoint and therefore requires fresh exact-head CI plus a fresh genuinely independent audit before PR #1679 may merge.
