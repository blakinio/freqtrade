# Quant v2 Execution Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` (or the repository-approved equivalent) and `superpowers:test-driven-development`. This plan is test-first and fail-closed.

**Goal:** Deliver the accepted Quant Platform v2 execution-governance package: one machine-readable programme contract, one canonical durable programme-state source, one fail-closed implementation coordinator, deterministic allocation admission, unambiguous owner routing, and a complete legacy PAPER fence, while leaving the governance package itself in `GOVERNANCE_ACCEPTED_STANDBY` with zero V2 implementation allocations.

**Architecture:** Keep generic execution, lease, risk and closeout behaviour authoritative in `docs/agents/PROJECT_LANES.json`, `docs/agents/EXECUTION_PROTOCOL.md`, `docs/agents/RISK_BASED_EXECUTION_POLICY.json` and `docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md`. Add one narrower static programme contract at `docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json`. After a later explicit owner activation, canonical dynamic programme truth is stored only in `docs/agents/quant_v2/PROGRAMME_STATE.json`. Production worker admission resolves the exact current trusted `origin/develop`, reads governance/policy/programme state from that immutable tree, derives current governance identity from that tree/history, and uses validator-owned timezone-aware UTC. Caller-selected worker snapshots, expected governance SHAs, programme-state maps, incumbent subsets, predecessor maps and production-time overrides are never authority.

**Tech stack:** JSON, Python 3 standard library, pytest, Markdown prompt/eval contracts, Git CLI for trusted current-tree resolution, repository GitHub Actions/pre-commit/CodeQL/zizmor.

**Approved spec:** `docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md`

## Global constraints

- This plan implements governance/CI only. It must not add Rust Quant Core runtime, Python V2 strategy runtime, Portal causal-trace runtime, deployment, model activation, private exchange credentials, real orders, withdrawals, or real-capital authority.
- `PROJECT_LANES.json` remains the repo-wide generic execution authority. Do not place the V2 DAG or V2 lane semantics in it.
- The governance implementation merge ends in `GOVERNANCE_ACCEPTED_STANDBY`; it must not itself issue `Quant: implementacja v2`, create a V2 allocation, create an activation receipt, or create an activated `PROGRAMME_STATE.json`.
- Absence of `docs/agents/quant_v2/PROGRAMME_STATE.json` on **current trusted `develop`** is canonical only for standby/no allocations. It is never sufficient worker write authority.
- Only a later explicit owner invocation `Quant: implementacja v2` may authorize the coordinator to create a durable activation receipt and transition canonical state to `ENTRY_EVIDENCE_PENDING`; only `V2-ENTRY-EVIDENCE` is eligible then.
- `V2-ENTRY-EVIDENCE` is the producer/verifier of the exact reference/parity oracle and canonical WickHunter/WH09 fixture. Missing/UNKNOWN entry evidence is allowed when admitting that lane, provided activation/state/allocation fences pass and `repository_implementation` is exactly `false`.
- `V2-BOOTSTRAP` and all later lanes remain blocked until both `reference_parity_oracle` and `canonical_wickhunter_wh09_fixture` have exact immutable identities and independently verified `PASS` evidence in canonical programme state.
- Missing, malformed, expired, stale-governance, stale-current-tree, wrong-lane, wrong-state, dependency-unsatisfied, path-outside-lane, owned-path-overlap, shared-surface-overlap, stale/unknown predecessor evidence, incomplete state, omitted incumbent, forged activation or authority-widening allocations fail closed to read-only.
- Generic lease authority is inherited mechanically from `PROJECT_LANES.execution.lease_minutes`; the accepted value on the design base is 45 minutes and the V2 overlay must fail closed if its mirror differs from the current trusted generic source.
- Production expiry-at-now uses `datetime.now(timezone.utc)` inside the validator. Ordinary production CLI has no `--now` or equivalent time override. Deterministic time injection exists only in pure test helpers/tests.
- Production admission may accept a repository location only as a Git transport/worktree locator. It must verify expected repository identity, fetch/resolve current trusted `origin/develop`, and read authoritative files from that exact tree. A caller-selected worker root is never the authoritative state snapshot.
- Expected current governance identity is derived from trusted current history (the last commit on current `develop` that changes `docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json`), never accepted as a caller authority parameter.
- If current trusted `develop` cannot be fetched/resolved, repository identity is wrong, canonical files cannot be read from the current tree, or allocation/state generation is stale relative to current canonical state, admission fails closed.
- `WDROŻENIE PAPER` / `PAPER_PLATFORM_EXECUTOR.md` is legacy compatibility only and must implement the full four-part fence from the approved spec: `quant_v2_authority:false`, `may_allocate_quant_v2_lanes:false`, `may_mutate_quant_v2_governance:false`, `treatment: legacy_closeout_or_reclassification_only`.
- Existing valid legacy PAPER work may be closed out, but must be reclassified under ADR-023/025/027 before any further target-driven mutation. Legacy routing may never mutate Quant-v2 governance, V2-owned paths or V2 shared surfaces.
- Oteryn is non-authoritative design precedent only.
- Governance/CI risk is true: test-first policy regression, trusted-base self-validation, exact-head CI and a fresh independent exact-head audit are mandatory before governance merge.
- Runtime/browser E2E is `NOT_APPLICABLE_WITH_REASON` for this governance-only package.

## Canonical trusted-current model

### Trusted current `develop`

Production validation must resolve current authority before evaluating a worker:

1. accept `--repo-root` only as a Git repository locator and `--task-path` as the candidate task record;
2. verify the repository remote identity resolves to `blakinio/freqtrade` (normal GitHub HTTPS/SSH forms are allowed; unknown/ambiguous identity fails closed);
3. fetch `origin develop` without modifying the worker branch;
4. resolve `refs/remotes/origin/develop` to an exact 40-hex `current_develop_sha`;
5. read authoritative static governance, generic policy and canonical programme state with `git show <current_develop_sha>:<path>` rather than from worker working-tree files;
6. derive `current_governance_sha` with trusted history, equivalent to `git log -1 --format=%H <current_develop_sha> -- docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json`;
7. derive current canonical programme-state generation/history from the same trusted `develop` history;
8. only then compare the worker task/allocation against current canonical truth.

No caller may supply `current_develop_sha`, `expected_governance_sha`, programme state, incumbent census, predecessor ledger, activation status or production `now` as authority. Test helpers may inject immutable in-memory fixtures to unit-test pure validation functions, but the production CLI path must prove the trusted-current resolution itself.

### Canonical programme state

The static machine contract defines exactly one dynamic state path:

`docs/agents/quant_v2/PROGRAMME_STATE.json`

Before owner activation this path is absent on current trusted `develop`; the only coordinator interpretation is:

```json
{
  "programme_state": "GOVERNANCE_ACCEPTED_STANDBY",
  "activation_epoch": null,
  "active_allocations": 0
}
```

A worker validator must reject absent state. Only the coordinator handling the explicit owner activation command may use absence-as-standby.

On a later explicit `Quant: implementacja v2`, the coordinator must first create and merge a serialized control-plane activation transaction containing:

- `docs/agents/quant_v2/activation/<activation_epoch>.json` — immutable activation receipt;
- `docs/agents/quant_v2/PROGRAMME_STATE.json` — canonical state initialized to `ENTRY_EVIDENCE_PENDING` with generation `1` and zero or exactly one ENTRY allocation transaction.

The activation receipt records at minimum:

```json
{
  "programme_id": "quant-v2",
  "governance_sha": "<derived exact current governance commit>",
  "activation_epoch": "<stable unique epoch>",
  "activation_command": "Quant: implementacja v2",
  "owner_command_received": true,
  "recorded_at": "<timezone-aware timestamp>",
  "previous_programme_state": "GOVERNANCE_ACCEPTED_STANDBY"
}
```

`PROGRAMME_STATE.json` binds to that receipt by exact path plus SHA-256 of its bytes and contains one complete canonical snapshot:

```json
{
  "schema_version": 1,
  "programme_id": "quant-v2",
  "governance_sha": "<derived exact current governance commit>",
  "state_generation": 1,
  "programme_state": "ENTRY_EVIDENCE_PENDING",
  "activation": {
    "epoch": "<same epoch>",
    "receipt_path": "docs/agents/quant_v2/activation/<epoch>.json",
    "receipt_sha256": "<64 hex>"
  },
  "allocation_count": 0,
  "allocations": [],
  "predecessors": {},
  "entry_evidence": {}
}
```

After activation, current `PROGRAMME_STATE.json` is the only source for current programme state/generation, activation binding, complete active-allocation set, predecessor terminal/evidence identities and ENTRY artifact verdicts.

Every allocation issuance/revocation/rebind and predecessor/evidence publication is a serialized coordinator control-plane transaction merged to `develop` before dependent worker writes. Each allocation entry binds to exact worker task path + SHA-256 of task bytes and to the state generation that grants it. `allocation_count` equals allocation entries; allocation IDs and task IDs are unique.

`state_generation` is mechanically historical, not merely asserted:

- initial activated state is generation `1` when the path did not exist in prior trusted history;
- each later commit that mutates `PROGRAMME_STATE.json` must set generation to exactly previous canonical generation + 1;
- validator resolves the previous trusted version of that path from `develop` history and verifies this relation;
- every active allocation is rebound atomically to the new generation in canonical state; a worker task still bound to an older generation fails closed.

If previous/current history cannot be resolved or generation regresses/skips unexpectedly, admission fails closed.

## Hard execution order

```text
Task 0: DESIGN MERGE GATE
  -> Task 1: machine programme contract + trusted-current/canonical-state schema
  -> Task 2: trusted-current allocation admission validator
  -> Task 3: coordinator routing + complete legacy PAPER fence
  -> Task 4: qualify/merge/archive governance package
```

Tasks 1-3 **MUST NOT** execute on the design branch or before Task 0 is terminally successful.

---

### Task 0: Mandatory design/spec/plan merge gate

**Files:** none.

- [ ] Resolve live `develop`, PR #1679 base/head, all changed paths, reviews/threads/comments and exact-head workflow runs.
- [ ] Require PR #1679 exact head to have a fresh genuinely independent design/governance audit with zero material P0/P1 findings. The authoring context may not self-qualify its own design head.
- [ ] Require latest qualifying exact-head Freqtrade CI, Risk-aware component CI, CodeQL and zizmor terminal success.
- [ ] Require zero unresolved blocking review/thread, `mergeable: true`, and compatible current `develop`.
- [ ] Re-resolve PR head immediately before merge; head movement invalidates the audit.
- [ ] Guarded squash-merge PR #1679 using `expected_head_sha`.
- [ ] Re-resolve `develop` and verify exact approved spec and implementation plan landed.
- [ ] Only then may Task 1 create a new governance implementation task/branch.

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
assert data["programme_state_store"]["worker_admission_requires_present_state"] is True
assert data["programme_state_store"]["complete_allocation_index_required"] is True
assert data["programme_state_store"]["canonical_predecessor_ledger_required"] is True
assert data["trusted_current"]["branch"] == "develop"
assert data["trusted_current"]["remote"] == "origin"
assert data["trusted_current"]["production_now_source"] == "validator_utc"
assert data["trusted_current"]["caller_expected_governance_sha_allowed"] is False
assert data["trusted_current"]["caller_now_override_allowed"] is False
```

Require generic `PROJECT_LANES` separation and lease binding:

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

Require `entry_evidence` to gate `V2-BOOTSTRAP`, not pre-block `V2-ENTRY-EVIDENCE`.

Run focused tests and observe RED because the machine contract does not yet exist.

#### Step 2 — minimal GREEN machine contract

Create `docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json` with:

- schema/programme/coordinator/activation fields;
- approved state transitions;
- `inherits_repository_execution_from` pointing to current generic contracts;
- exact trusted-current and programme-state semantics from this plan;
- lease-policy binding above;
- authority defaults all false for deployment, protected-environment mutation, model activation, private-exchange credentials and real capital;
- `entry_evidence` requiring `reference_parity_oracle` and `canonical_wickhunter_wh09_fixture` independent exact `PASS` as the gate for `V2-BOOTSTRAP` and later lanes;
- allocation record format `task_markdown_json_block_v1`, heading `## Quant V2 allocation`;
- shared surfaces `cross_language_schema`, `database_migration`, `stable_identity_vocabulary`, `programme_command_routing`;
- the full four-part legacy fence;
- eight V2 lane objects with approved dependencies, merge waves, serial flags and eligibility path families.

Approved dependencies:

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

Merge waves remain 10/20/30/30/30/40/50/60 with BOOTSTRAP and S1-INTEGRATION serial. Eligibility path families remain those in the approved spec; individual allocations must narrow exact owned paths.

Run focused tests to GREEN before commit.

---

### Task 2: Trusted-current programme-state parser and fail-closed allocation validator

**Files:**
- Create: `tools/agents/validate_quant_v2_execution_governance.py`
- Modify: `tests/ci/test_quant_v2_execution_governance.py`

#### Production interface boundary

Pure testable helpers may accept parsed objects and injected `now`, but ordinary production admission must go through a wrapper equivalent to:

```python
@dataclass(frozen=True)
class TrustedCurrentSnapshot:
    develop_sha: str
    governance_sha: str
    governance_bytes: bytes
    project_lanes_bytes: bytes
    programme_state_bytes: bytes | None
    previous_programme_state_bytes: bytes | None

resolve_trusted_current(repo_root: Path) -> TrustedCurrentSnapshot
validate_worker_admission(repo_root: Path, task_path: Path) -> list[str]
```

Production CLI is exactly bounded to repository/task location, e.g.:

```text
python tools/agents/validate_quant_v2_execution_governance.py \
  --repo-root <git checkout> \
  --task-path <worker task markdown>
```

Production CLI MUST NOT offer `--expected-governance-sha`, `--now`, `--programme-state`, `--active-task`, predecessor maps, allocation census subsets, activation flags, `--develop-sha`, or any equivalent caller authority override.

`resolve_trusted_current()` must verify repository identity, fetch current `origin/develop`, resolve exact SHA, read authoritative paths from that exact tree, derive governance SHA from trusted history, and resolve prior/current programme-state history. Unknown/unavailable/ambiguous state fails closed.

Pure functions may include:

```python
load_governance_bytes(raw: bytes) -> dict[str, Any]
load_repository_policy_bytes(raw: bytes) -> dict[str, Any]
load_programme_state_bytes(raw: bytes | None) -> dict[str, Any] | None
extract_allocation(task_bytes: bytes) -> dict[str, Any] | None
validate_governance(governance: dict[str, Any], repository_policy: dict[str, Any]) -> list[str]
validate_programme_state(
    state: dict[str, Any] | None,
    governance: dict[str, Any],
    *,
    derived_governance_sha: str,
    activation_receipt_loader: Callable[[str], bytes],
    previous_state: dict[str, Any] | None,
    allow_absent_standby: bool,
) -> list[str]
validate_allocation(
    allocation: dict[str, Any],
    governance: dict[str, Any],
    repository_policy: dict[str, Any],
    programme_state: dict[str, Any],
    *,
    derived_governance_sha: str,
    now: datetime,
    task_record_path: str,
    task_record_bytes: bytes,
) -> list[str]
```

The injected `now` above is a pure-helper seam only. `validate_worker_admission()` always supplies `datetime.now(timezone.utc)` internally.

#### Step 1 — RED trusted-current/allocation tests

Add RED regressions for at least:

1. production parser exposes `--expected-governance-sha` -> FAIL;
2. production parser exposes `--now` or equivalent -> FAIL;
3. wrong/ambiguous repository remote identity;
4. `origin/develop` fetch/resolve unavailable;
5. authoritative governance/policy/state read attempted from worker working tree rather than exact trusted tree;
6. stale worker branch whose allocation was revoked/rebound on newer `develop`;
7. stale governance snapshot whose supplied worker files are self-consistent but trusted current governance differs;
8. regressed/skipped/non-current `state_generation` against trusted history;
9. active allocation bound to older state generation;
10. stale allocation `governance_sha` versus derived governance SHA;
11. absent programme state for worker admission;
12. programme-state governance SHA mismatch;
13. malformed/missing activation epoch/receipt;
14. activation receipt wrong path/hash/command/prior state/owner flag;
15. `allocation_count` differs from canonical entry count;
16. duplicate allocation/task IDs;
17. candidate allocation absent or differs from canonical state;
18. task-record path/SHA-256 mismatch;
19. omitted-incumbent overlap attempt;
20. forged programme state for lane;
21. wrong merge wave or dependency ID set;
22. missing predecessor, wrong terminal state, malformed/non-immutable evidence or evidence identity mismatch;
23. stale predecessor generation/source binding;
24. expired lease at validator-owned UTC;
25. expiry <= acquisition;
26. lease duration > current trusted `PROJECT_LANES.execution.lease_minutes`;
27. V2 lease mirror/source mismatch;
28. path outside lane family;
29. owned-path overlap with any canonical incumbent;
30. shared-surface overlap with any canonical incumbent;
31. forbidden authority widening;
32. malformed/missing required allocation fields;
33. `V2-ENTRY-EVIDENCE.repository_implementation` not exactly false;
34. `V2-BOOTSTRAP` with missing/UNKNOWN/non-PASS oracle or WH09 evidence.

Positive no-self-deadlock regression:

```text
valid explicit activation receipt on current trusted develop
+ current canonical state ENTRY_EVIDENCE_PENDING
+ generation/history valid
+ no prior ENTRY target evidence or artifacts UNKNOWN/absent
+ exact current V2-ENTRY-EVIDENCE allocation
+ repository_implementation=false
=> allocation admission PASS
```

And:

```text
same trusted state + V2-BOOTSTRAP + either artifact not exact independent PASS
=> allocation admission FAIL
```

Observe RED before validator implementation.

#### Step 2 — minimal GREEN validator

Implement in this order:

1. verify Git repository/remote identity;
2. fetch and resolve exact current `origin/develop` without changing worker branch;
3. read static governance, `PROJECT_LANES.json` and canonical state from that exact tree;
4. derive governance SHA from trusted current history; never consume caller expected SHA;
5. resolve previous/current programme-state history and mechanically validate generation 1 or exact previous+1;
6. reject absent state for worker admission; only coordinator activation helper may allow absent standby;
7. require programme/governance identity and valid activation receipt binding;
8. validate allocation-index completeness, unique IDs/task IDs and task-record bindings;
9. require candidate allocation exactly once in canonical state and bound to current state generation;
10. derive programme state, all incumbents and predecessor truth only from canonical current state;
11. validate lane/state/merge wave/exact dependency IDs and canonical predecessor terminal/evidence identities;
12. obtain timezone-aware current UTC inside production wrapper;
13. require expiry > acquisition, expiry > validator-owned current UTC, and duration <= current generic maximum;
14. validate lane path family and all canonical owned/shared overlaps;
15. require forbidden authority flags false;
16. require ENTRY `repository_implementation=false` without requiring target artifacts PASS;
17. require canonical ENTRY predecessor + exact immutable independent PASS for both target artifacts before BOOTSTRAP/later;
18. any unavailable/missing/unknown/stale/incomplete current authority is an error, never a default PASS.

Run focused tests to GREEN before commit.

#### Step 3 — coordinator state-transaction contract

Document/test that the coordinator is the only writer of canonical programme state. Before any V2 worker write, the state/allocation transaction is already merged on trusted `develop`. Every state mutation increments generation exactly once and atomically rebinds retained active allocations to the new generation. Revoked/rebound allocations disappear/change in the complete canonical index, so stale worker tasks fail admission even if their local snapshots remain self-consistent.

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

- `Quant: implementacja v2` routes exactly to `QUANT_V2_IMPLEMENTATION_COORDINATOR.md`, never PAPER executor;
- standby cannot issue allocation unless current invocation is explicit owner activation;
- activation persists durable receipt/state transition before worker authority;
- first writable V2 lane is only `V2-ENTRY-EVIDENCE`;
- coordinator reconstructs live GitHub/current trusted `develop` state every invocation;
- coordinator uses canonical state and production validator before V2 writes;
- coordinator never supplies expected governance SHA, production time, partial incumbent/predecessor state or a stale worker snapshot as authority;
- coordinator serializes state/allocation mutations and rebinds stale interacting generations;
- coordinator may not self-qualify materially authored candidates;
- no deploy/private-exchange/real-capital authority is implied;
- PAPER executor YAML and machine contract contain all four exact legacy fence fields;
- `WDROŻENIE PAPER` / `WDROŻENIE PAPER dalej` may only close out valid legacy work or return reclassification-required, never continue new target-driven mutation under superseded authority;
- legacy PAPER routing rejects V2 lanes, Quant-v2 governance/state and V2 shared-surface mutation.

Observe RED.

#### Step 2 — minimal GREEN coordinator/routing implementation

Create coordinator prompt with:

```yaml
role: quant-v2-implementation-coordinator
run_scope: autonomous_program
machine_governance: docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json
programme_state: docs/agents/quant_v2/PROGRAMME_STATE.json
trusted_branch: develop
trusted_remote: origin
legacy_paper_authority: false
protected_environment_authority: false
private_trading_credential_authority: false
live_capital_authority: false
```

It reconstructs live GitHub/current trusted state on every invocation, persists activation before ENTRY allocation, issues exact bounded allocations via serialized control-plane transactions, requires trusted-current validator PASS before mutation, preserves merge waves, serializes shared surfaces, rebinds stale generations, and never bypasses independent audit/CI/E2E gates.

Update `PAPER_PLATFORM_EXECUTOR.md` and routing to implement exactly:

```yaml
quant_v2_authority: false
may_allocate_quant_v2_lanes: false
may_mutate_quant_v2_governance: false
treatment: legacy_closeout_or_reclassification_only
```

Existing valid legacy work remains closable. Further target-driven mutation requires reclassification first. Explicitly reject V2 governance/state, V2 lane and V2 shared-surface mutation from legacy PAPER aliases.

Create eval coverage for positive, negative, stale-governance, stale-worker-current-develop, production-now override injection, state-history/generation, canonical completeness, omitted incumbent, forged state, activation receipt, ENTRY-with-missing-evidence positive, BOOTSTRAP evidence gate, expired/oversized lease, dependency/evidence mismatch, path/shared overlap, standby activation and legacy PAPER scenarios.

Run focused tests to GREEN before commit.

---

### Task 4: Implement, qualify, merge and archive governance package

**Precondition:** Task 0 terminal `DESIGN_MERGED_QUALIFIED`.

Create a new post-design-merge active task:

`docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-implementation.md`

The implementation task itself must **not** contain `## Quant V2 allocation`, activation receipt, V2 allocation or activated `PROGRAMME_STATE.json`, and must state:

```yaml
runtime_access: none
programme_post_merge_state: GOVERNANCE_ACCEPTED_STANDBY
v2_s1_activation_authorized_by_this_task: false
risk:
  governance_or_ci: true
runtime_e2e: NOT_APPLICABLE_WITH_REASON
```

Execute Tasks 1-3 with TDD using separate RED then GREEN commits/evidence. Do not create `V2-ENTRY-EVIDENCE`, activation receipt, activated state or implementation allocation in this package.

Run focused governance tests plus repository-prescribed governance/CI validation. Open one truthful governance implementation PR and require exact-head CI, zero unresolved blockers and a genuinely fresh independent exact-head governance audit. The authoring context must not self-qualify its own candidate.

Squash-merge only with `expected_head_sha`. After merge verify on `develop`:

- static machine governance is present and valid;
- dynamic `docs/agents/quant_v2/PROGRAMME_STATE.json` is absent;
- canonical programme state is therefore `GOVERNANCE_ACCEPTED_STANDBY`, allocation count zero;
- no activation receipt exists;
- no Rust/Python/Portal runtime implementation landed;
- no runtime/deployment/model/private-exchange/real-capital authority widened;
- `WDROŻENIE PAPER` has complete fence/reclassification requirement.

Archive/release implementation task through repository closeout rules. Closeout must not activate programme.

---

## Required validation matrix

| Gate | Required result |
| --- | --- |
| Task 0 design exact-head CI | PASS |
| Task 0 independent design audit | PASS_ZERO_MATERIAL_FINDINGS |
| Static machine-contract tests | RED then GREEN |
| Trusted current `origin/develop` resolution | RED then GREEN |
| Caller expected-governance-SHA rejection | RED then GREEN |
| Production `--now`/time-override rejection | RED then GREEN |
| Stale worker after current revoke/rebind | RED then GREEN |
| Canonical state history/generation | RED then GREEN |
| Canonical activation matrix | RED then GREEN |
| Complete allocation-index / omitted-incumbent matrix | RED then GREEN |
| Dependency canonical-state/evidence matrix | RED then GREEN |
| ENTRY-EVIDENCE initial-UNKNOWN positive admission | PASS |
| BOOTSTRAP exact oracle+WH09 evidence gate | RED then GREEN |
| Generic lease inheritance | RED then GREEN |
| Routing/complete PAPER fence tests | RED then GREEN |
| Governance trusted-base self-validation | PASS |
| Governance exact-head repository CI | PASS |
| Governance independent exact-head audit | PASS_ZERO_MATERIAL_FINDINGS |
| Runtime/browser E2E | NOT_APPLICABLE_WITH_REASON |
| Post-governance dynamic state file | ABSENT |
| Post-governance canonical state | GOVERNANCE_ACCEPTED_STANDBY |
| Post-governance V2 allocations | 0 |

## Stop conditions

Stop before mutation if Task 0 is not proven. During governance implementation stop only for a real authority/safety/capability blocker, conflicting path ownership, material architecture change, or failed independent audit requiring remediation. Do not stop merely because a commit or PR exists.

## Self-review against independent audit findings

- `QV2-1679-001` — **REMEDIATED:** design qualification/merge is Task 0 and hard predecessor.
- `QV2-1679-002` — **REMEDIATED IN PLAN:** predecessor truth comes only from canonical state read from exact current trusted `develop`.
- `QV2-1679-003` — **REMEDIATED IN PLAN:** lease source/mirror and duration are current generic policy; production expiry uses validator-owned UTC with no CLI override.
- `QV2-1679-004` — **REMEDIATED IN PLAN:** current programme state, activation, complete incumbents and predecessors are canonical/exhaustive and read from trusted current `develop`.
- `QV2-1679-005` — **REMEDIATED IN PLAN:** ENTRY may produce missing evidence; exact PASS gates BOOTSTRAP/later.
- `QV2-1679-006` — **REMEDIATED IN PLAN:** full four-part PAPER fence plus reclassification-only routing.
- `QV2-1679-007` — **REMEDIATED IN PLAN:** production trust anchors are no longer caller-controlled. Validator verifies repository identity, fetches/resolves exact current `origin/develop`, reads authority from that immutable tree, derives governance SHA/current state history itself, obtains timezone-aware current UTC internally, rejects production time/governance/state overrides, and fail-closes stale worker/current-generation mismatches. State-generation monotonicity is bound mechanically to trusted Git history.

The owner-approved spec remains unchanged. This remediation changes only the implementation plan and design-task checkpoint, so PR #1679 requires fresh exact-head CI plus a fresh genuinely independent audit before merge.