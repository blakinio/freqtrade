# Quant v2 Execution Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` (or the repository-approved equivalent) and `superpowers:test-driven-development`. This plan is test-first and fail-closed.

**Goal:** Deliver the accepted Quant Platform v2 execution-governance package: one machine-readable programme authority, one fail-closed implementation coordinator, deterministic allocation admission, unambiguous owner routing, and a legacy PAPER fence, while leaving the merged programme in `GOVERNANCE_ACCEPTED_STANDBY` with zero V2 implementation allocations.

**Architecture:** Keep generic execution, lease, risk and closeout behaviour authoritative in `docs/agents/PROJECT_LANES.json`, `docs/agents/EXECUTION_PROTOCOL.md`, `docs/agents/RISK_BASED_EXECUTION_POLICY.json` and `docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md`. Add one narrower `docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json` programme overlay. The coordinator consumes that overlay; worker authority is persisted as one fenced JSON allocation in an active task record and is mechanically validated before any V2 write.

**Tech stack:** JSON, Python 3 standard library, pytest, Markdown prompt/eval contracts, repository GitHub Actions/pre-commit/CodeQL/zizmor.

**Approved spec:** `docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md`

## Global constraints

- This plan implements governance/CI only. It must not add Rust Quant Core runtime, Python V2 strategy runtime, Portal causal-trace runtime, deployment, model activation, private exchange credentials, real orders, withdrawals, or real-capital authority.
- `PROJECT_LANES.json` remains the repo-wide generic execution authority. Do not place the V2 DAG or V2 lane semantics in it.
- The governance implementation merge ends in `GOVERNANCE_ACCEPTED_STANDBY`; it must not itself issue `Quant: implementacja v2` or create any V2 allocation.
- Only a later explicit owner invocation `Quant: implementacja v2` may move the programme from standby to `ENTRY_EVIDENCE_PENDING`, and only `V2-ENTRY-EVIDENCE` is eligible at that point.
- `V2-BOOTSTRAP` remains blocked until both `reference_parity_oracle` and `canonical_wickhunter_wh09_fixture` have exact immutable identities and independently verified `PASS` evidence.
- Missing, malformed, expired, stale-governance, wrong-lane, wrong-state, dependency-unsatisfied, path-outside-lane, owned-path-overlap, shared-surface-overlap, stale/unknown-evidence, or authority-widening allocations fail closed to read-only.
- Generic lease authority is inherited mechanically from `PROJECT_LANES.execution.lease_minutes`; the accepted value on the design base is 45 minutes and the V2 overlay must fail closed if its mirror differs from the generic source.
- `WDROŻENIE PAPER` / `PAPER_PLATFORM_EXECUTOR.md` has `quant_v2_authority: false`.
- Oteryn is non-authoritative design precedent only.
- Governance/CI risk is true: test-first policy regression, trusted-base self-validation, exact-head CI and a fresh independent exact-head audit are mandatory before governance merge.
- Runtime/browser E2E is `NOT_APPLICABLE_WITH_REASON` for this governance-only package.

## Hard execution order

```text
Task 0: DESIGN MERGE GATE
  -> Task 1: machine programme contract
  -> Task 2: allocation parser/admission validator
  -> Task 3: coordinator routing + legacy PAPER fence
  -> Task 4: qualify/merge/archive governance package
```

Tasks 1-3 **MUST NOT** execute on the design branch or before Task 0 is terminally successful. A plan worker that cannot prove Task 0 must stop before creating the implementation task/branch.

---

### Task 0: Mandatory design/spec/plan merge gate

**Files:** none.

**Purpose:** make the independent design qualification and merge a real prerequisite, not a late closeout step.

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

**Interfaces:**
- Consumes: merged approved spec plus current generic repository execution contracts.
- Produces: schema `1` programme contract with state machine, lane DAG, allowed path families, shared surfaces, activation gate, entry-evidence gate, lease-policy binding, authority defaults, allocation record format and legacy executor fence.

#### Step 1 — RED static-contract tests

Add tests that require at minimum:

```python
assert data["schema_version"] == 1
assert data["programme_id"] == "quant-v2"
assert data["coordinator_role"] == "quant-v2-implementation-coordinator"
assert data["initial_state"] == "GOVERNANCE_ACCEPTED_STANDBY"
assert data["owner_command_required_for_activation"] is True
assert data["activation_command"] == "Quant: implementacja v2"
```

Require exact fail-closed state transitions:

```json
{
  "GOVERNANCE_ACCEPTED_STANDBY": ["ENTRY_EVIDENCE_PENDING", "BLOCKED", "REVOKED"],
  "ENTRY_EVIDENCE_PENDING": ["READY_FOR_BOOTSTRAP", "BLOCKED", "REVOKED"],
  "READY_FOR_BOOTSTRAP": ["IMPLEMENTING", "BLOCKED", "REVOKED"],
  "IMPLEMENTING": ["S1_INTEGRATION_READY", "BLOCKED", "REVOKED"],
  "S1_INTEGRATION_READY": ["S1_TERMINAL", "BLOCKED", "REVOKED"],
  "S1_TERMINAL": [],
  "BLOCKED": ["ENTRY_EVIDENCE_PENDING", "READY_FOR_BOOTSTRAP", "IMPLEMENTING", "REVOKED"],
  "REVOKED": []
}
```

Require inheritance from:

```text
docs/agents/PROJECT_LANES.json
docs/agents/EXECUTION_PROTOCOL.md
docs/agents/RISK_BASED_EXECUTION_POLICY.json
docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md
```

Require generic policy remains generic:

```python
project_lanes = json.loads(PROJECT_LANES_PATH.read_text())
assert project_lanes["schema_version"] == 2
assert "v2_lane_dag" not in project_lanes
```

Require lease inheritance mechanically:

```python
assert project_lanes["execution"]["lease_minutes"] == 45
assert data["lease_policy"] == {
    "source": "docs/agents/PROJECT_LANES.json",
    "source_field": "execution.lease_minutes",
    "max_duration_minutes": 45,
    "must_equal_source": True,
}
```

Run:

```bash
pytest -q tests/ci/test_quant_v2_execution_governance.py
```

Expected RED: machine contract does not exist yet.

#### Step 2 — minimal GREEN machine contract

Create `docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json` with:

- schema/programme/coordinator/activation fields above;
- exact state transitions above;
- `inherits_repository_execution_from` list above;
- `lease_policy` binding above;
- authority defaults all false for repository implementation, deployment, protected-environment mutation, model activation, private-exchange credentials and real capital;
- `entry_evidence` requiring both `reference_parity_oracle` and `canonical_wickhunter_wh09_fixture`, verdict `PASS`, blocking `V2-BOOTSTRAP`;
- allocation record format `task_markdown_json_block_v1`, heading `## Quant V2 allocation`;
- shared surfaces `cross_language_schema`, `database_migration`, `stable_identity_vocabulary`, `programme_command_routing`;
- `WDROŻENIE PAPER` legacy executor fence with `quant_v2_authority: false`;
- eight V2 lane objects with approved dependencies, merge waves, serial flags and eligibility path families.

Approved lane dependencies:

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

Approved eligibility path families:

```text
V2-ENTRY-EVIDENCE -> docs/agents/evidence/quant_v2/, tests/fixtures/quant_v2/
V2-BOOTSTRAP -> quant_core/, ai_platform/contracts/quant_v2/, ai_platform/quant_v2/, tests/quant_v2/
V2-CORE -> quant_core/
V2-STRATEGY -> ai_platform/quant_v2/
V2-QA -> tests/quant_v2/, tests/fixtures/quant_v2/, docs/agents/evidence/quant_v2/
V2-DURABILITY -> quant_core/, ai_platform/contracts/quant_v2/, tests/quant_v2/
V2-PORTAL-TRACE -> ai_platform/portal/, tests/quant_v2/
V2-S1-INTEGRATION -> tests/quant_v2/, docs/agents/evidence/quant_v2/
```

These are eligibility families only; an allocation grants a smaller exact `owned_paths` set.

Run the focused tests again. Expected GREEN.

Commit only after observed GREEN:

```bash
git add docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json tests/ci/test_quant_v2_execution_governance.py
git commit -m "feat(governance): add Quant v2 execution contract"
```

---

### Task 2: Allocation parser and fail-closed admission validator

**Files:**
- Create: `tools/agents/validate_quant_v2_execution_governance.py`
- Modify: `tests/ci/test_quant_v2_execution_governance.py`

**Required interfaces:**

```python
load_governance(path: Path) -> dict[str, Any]
load_repository_policy(path: Path) -> dict[str, Any]
extract_allocation(task_path: Path) -> dict[str, Any] | None
validate_governance(governance: dict[str, Any], repository_policy: dict[str, Any]) -> list[str]
validate_allocation(
    allocation: dict[str, Any],
    governance: dict[str, Any],
    repository_policy: dict[str, Any],
    active_allocations: Iterable[dict[str, Any]],
    predecessor_states: Mapping[str, dict[str, Any]],
    *,
    expected_governance_sha: str,
    now: datetime,
) -> list[str]
```

CLI must accept `--governance`, `--project-lanes`, `--expected-governance-sha`, repeatable `--task`, repeatable `--active-task`, and predecessor-state evidence input. Exit `0` only when every supplied contract/allocation is valid; otherwise exit `2`.

#### Step 1 — RED negative tests

Build a valid V2-CORE allocation fixture whose dependency is:

```json
{
  "id": "V2-BOOTSTRAP",
  "required_state": "terminal",
  "exact_evidence_ref": "cccccccccccccccccccccccccccccccccccccccc"
}
```

and a matching current predecessor-state fixture:

```python
predecessor_states = {
    "V2-BOOTSTRAP": {
        "state": "terminal",
        "exact_evidence_ref": "c" * 40,
    }
}
```

The valid allocation lease fixture may be exactly 45 minutes, never more.

Add RED tests for all of these failures:

1. stale `governance_sha`;
2. expired lease;
3. lease expiry not after acquisition;
4. lease duration greater than generic `PROJECT_LANES.execution.lease_minutes` (45 minutes on the accepted base), expecting e.g. `allocation lease exceeds repository maximum of 45 minutes`;
5. V2 governance lease mirror differs from the generic policy source, expecting fail-closed policy mismatch;
6. path outside lane family;
7. owned-path overlap with an active incumbent;
8. shared-surface overlap with an active incumbent;
9. wrong dependency ID set;
10. missing predecessor state for a declared dependency;
11. predecessor not in the allocation's required terminal state;
12. predecessor evidence ref missing/malformed/non-immutable;
13. allocation dependency evidence ref differs from the current predecessor evidence identity;
14. wrong programme state for lane;
15. wrong merge wave;
16. forbidden authority widening;
17. malformed/missing required allocation fields;
18. `V2-ENTRY-EVIDENCE.repository_implementation` not exactly false.

Observe RED before implementation.

#### Step 2 — minimal GREEN validator

Implement validation in this order and never default missing data to PASS:

1. allocation schema/required-field identity;
2. current merged governance SHA;
3. canonical coordinator role;
4. known lane;
5. programme-state eligibility;
6. exact lane merge wave;
7. exact dependency ID set;
8. for every dependency, prove against `predecessor_states`:
   - the predecessor ID exists;
   - live/current predecessor state equals allocation `required_state` and satisfies the lane contract;
   - allocation `exact_evidence_ref` is a 40-hex immutable identity;
   - current predecessor `exact_evidence_ref` is a 40-hex immutable identity;
   - both evidence identities are exactly equal;
9. parse timezone-aware `lease_acquired_at` and `lease_expires_at`;
10. load `PROJECT_LANES.execution.lease_minutes`; require it to exist and equal the V2 governance lease mirror;
11. require expiry > acquisition;
12. require `lease_expires_at > now`;
13. require `(lease_expires_at - lease_acquired_at) <= timedelta(minutes=lease_minutes)`;
14. every owned path must be inside at least one lane eligibility prefix;
15. no owned-path overlap with active incumbents;
16. no shared-surface overlap with active incumbents;
17. all forbidden authority flags exactly false;
18. `V2-ENTRY-EVIDENCE.repository_implementation` exactly false.

For the entry-evidence lane, separately require current exact evidence records for both required artifacts with immutable identities and independent verdict `PASS`; stale/unknown/missing evidence fails closed.

Run focused tests. Expected GREEN.

Commit only after observed GREEN:

```bash
git add tools/agents/validate_quant_v2_execution_governance.py tests/ci/test_quant_v2_execution_governance.py
git commit -m "feat(governance): validate Quant v2 allocations"
```

---

### Task 3: Coordinator routing, prompt regression and legacy PAPER fence

**Files:**
- Create: `docs/agents/prompts/QUANT_V2_IMPLEMENTATION_COORDINATOR.md`
- Create: `docs/agents/evals/QUANT_V2_IMPLEMENTATION_COORDINATOR_V1.md`
- Modify: `docs/agents/prompts/AGENT_COMMANDS.md`
- Modify: `docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md`
- Modify: `tests/ci/test_quant_v2_execution_governance.py`

#### Step 1 — RED routing/fence tests

Add tests requiring:

- `Quant: implementacja v2` routes exactly to `QUANT_V2_IMPLEMENTATION_COORDINATOR.md`;
- `Quant: implementacja v2` does not route to `PAPER_PLATFORM_EXECUTOR.md`;
- `WDROŻENIE PAPER` remains routed to the legacy executor and cannot satisfy Quant v2 allocation authority;
- the PAPER executor YAML contains `quant_v2_authority: false`;
- the coordinator prompt names `QUANT_V2_EXECUTION_GOVERNANCE.json` as its V2 machine authority;
- the coordinator must run the allocation validator before any V2 repository write;
- the coordinator may not self-qualify a candidate it materially authored;
- standby cannot issue an allocation without a fresh explicit owner `Quant: implementacja v2` invocation;
- first post-activation writable V2 lane is still `V2-ENTRY-EVIDENCE`, not Core/Strategy/Portal;
- no deploy/private-exchange/real-capital authority is implied.

Observe RED.

#### Step 2 — minimal GREEN prompt/routing implementation

Create the coordinator prompt with:

```yaml
role: quant-v2-implementation-coordinator
run_scope: autonomous_program
machine_governance: docs/agents/QUANT_V2_EXECUTION_GOVERNANCE.json
legacy_paper_authority: false
protected_environment_authority: false
private_trading_credential_authority: false
live_capital_authority: false
```

It must:

- reconstruct live GitHub state on every invocation;
- require exact merged governance identity;
- reject writes when programme is standby unless the current invocation is the explicit owner activation command;
- on activation, move only to `ENTRY_EVIDENCE_PENDING` and allocate only `V2-ENTRY-EVIDENCE`;
- issue exact bounded allocations and mechanically validate them before mutation;
- serialize shared surfaces and rebind stale generations;
- preserve the approved DAG and merge waves;
- never bypass independent audit/CI/E2E gates;
- never self-qualify work materially authored in the same context;
- never authorize deployment, private exchange credentials, real orders or real capital.

Create the eval document with positive, negative, stale-governance, expired/oversized-lease, wrong-dependency-state, evidence-mismatch, path-overlap, shared-surface-overlap, standby-activation and legacy-PAPER scenarios.

Update command routing and add `quant_v2_authority: false` to `PAPER_PLATFORM_EXECUTOR.md` YAML.

Run focused tests. Expected GREEN.

Commit only after observed GREEN:

```bash
git add docs/agents/prompts/QUANT_V2_IMPLEMENTATION_COORDINATOR.md \
        docs/agents/evals/QUANT_V2_IMPLEMENTATION_COORDINATOR_V1.md \
        docs/agents/prompts/AGENT_COMMANDS.md \
        docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md \
        tests/ci/test_quant_v2_execution_governance.py
git commit -m "feat(governance): route Quant v2 implementation"
```

---

### Task 4: Implement, qualify, merge and archive the governance package

**Precondition:** Task 0 is terminal `DESIGN_MERGED_QUALIFIED`. Task 4 does not merge the design PR; that already happened before Task 1.

**Files:**
- Create on a new post-design-merge branch: `docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-implementation.md`
- Optional discoverability-only pointer in `docs/agents/AGENTS.md` only if a failing test proves it necessary.
- Do not modify `PROJECT_LANES.json` unless a failing discoverability test proves a minimal pointer is required; if changed, it may contain only a pointer/keyword and no V2 DAG semantics.

#### Step 1 — create governance implementation task after Task 0

Freeze the post-design-merge `develop` SHA as trusted base. The governance implementation task itself must **not** contain a `## Quant V2 allocation` block and must state:

```yaml
runtime_access: none
programme_post_merge_state: GOVERNANCE_ACCEPTED_STANDBY
v2_s1_activation_authorized_by_this_task: false
risk:
  governance_or_ci: true
runtime_e2e: NOT_APPLICABLE_WITH_REASON
```

Its owned paths are only the governance/test/prompt/routing paths needed for Tasks 1-3. No runtime/deployment/model/private-exchange/real-capital paths are authorized.

#### Step 2 — execute Tasks 1-3 with TDD

For each behavioural change:

1. add one or more failing tests;
2. run them and observe the expected RED failure;
3. implement the smallest behaviour;
4. rerun focused tests to GREEN;
5. commit only coherent increments.

Do not create `V2-ENTRY-EVIDENCE` or any implementation allocation as part of this package.

#### Step 3 — trusted-base self-validation

Run focused governance tests plus repository-prescribed governance/CI validation. Validate JSON parsing, prompt/eval routing and repository contract consistency. Runtime/browser E2E is `NOT_APPLICABLE_WITH_REASON` because no runtime/product path changes.

#### Step 4 — exact-head CI and fresh independent audit

Open one truthful governance implementation PR. Require:

- exact current head and full intended diff;
- latest qualifying Freqtrade CI success;
- latest qualifying Risk-aware component CI success;
- CodeQL and zizmor success;
- zero unresolved blocking reviews/threads;
- fresh genuinely independent exact-head governance audit with zero material P0/P1 findings;
- authoring context does not self-qualify its own candidate;
- re-resolved unchanged head immediately before merge.

Any head move invalidates prior audit evidence.

#### Step 5 — guarded governance merge

Squash-merge only with `expected_head_sha`. After merge verify on `develop`:

- machine governance is present and valid;
- programme status is still `GOVERNANCE_ACCEPTED_STANDBY`;
- there is no Quant V2 allocation;
- no owner activation command has been synthesized;
- no Rust/Python/Portal runtime implementation landed;
- no runtime/deployment/model/private-exchange/real-capital authority widened;
- `WDROŻENIE PAPER` remains fenced with `quant_v2_authority: false`.

#### Step 6 — lifecycle closeout

Archive/release the governance implementation task through repository closeout rules, using a separate minimal lifecycle PR if required. Do not use lifecycle closeout to activate the programme. Terminal result is governance accepted in standby.

---

## Required validation matrix

| Gate | Required result |
| --- | --- |
| Task 0 design exact-head CI | PASS |
| Task 0 independent design audit | PASS_ZERO_MATERIAL_FINDINGS |
| Static machine-contract tests | RED then GREEN |
| Allocation validator negative matrix | RED then GREEN |
| Dependency live-state/evidence matrix | RED then GREEN |
| Generic 45-minute lease inheritance matrix | RED then GREEN |
| Routing/PAPER fence tests | RED then GREEN |
| Governance trusted-base self-validation | PASS |
| Governance exact-head repository CI | PASS |
| Governance independent exact-head audit | PASS_ZERO_MATERIAL_FINDINGS |
| Runtime/browser E2E | NOT_APPLICABLE_WITH_REASON |
| Post-merge programme state | GOVERNANCE_ACCEPTED_STANDBY |
| Post-merge V2 allocations | 0 |

## Stop conditions

Stop before mutation if Task 0 is not proven. During governance implementation stop only for a real authority/safety/capability blocker, conflicting path ownership, material architecture change, or failed independent audit that requires remediation. Do not stop merely because a commit or PR exists.

## Self-review against independent audit findings

- `QV2-1679-001` — **REMEDIATED IN PLAN:** design qualification/merge is now Task 0 and a hard predecessor of Tasks 1-3; implementation cannot start on the design branch.
- `QV2-1679-002` — **REMEDIATED IN PLAN:** dependency admission now requires the exact dependency ID set **and** current predecessor state/status **and** matching immutable current evidence identity; missing/stale/mismatched predecessor evidence fails closed.
- `QV2-1679-003` — **REMEDIATED IN PLAN:** V2 governance mirrors the generic lease source and the validator loads `PROJECT_LANES.execution.lease_minutes`, requires source/mirror equality and enforces total lease duration `<= 45 minutes` on the accepted base in addition to expiry-at-`now`.

The owner-approved spec is unchanged. This remediation changes only the implementation plan/checkpoint and requires a fresh independent audit on the new exact PR head before merge.
