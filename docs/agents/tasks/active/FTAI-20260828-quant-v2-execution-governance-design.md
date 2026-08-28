---
task_id: FTAI-20260828-quant-v2-execution-governance-design
repository: blakinio/freqtrade
project_lane: freqtrade-core
branch: docs/quant-v2-execution-governance-design
status: validating
phase: audit_remediation_v3
execution_mode: github_only
task_kind: architecture_design
implementation_authorized: false
trusted_base: 7aa9ce89d36adb503c83b20ffee8c9599982b33b
spec_head: 47f8c7196c0312a5fb5a013e3db4f4911f1239eb
spec_blob_sha: 9336b6a103a623261da90d3dafd467e478d1e101
spec_owner_review: approved
runtime_access: none
ownership_released: false
---

# Quant Platform v2 execution-governance design

## Objective

Persist the owner-approved design and a qualified implementation plan for the separate Quant Platform v2 execution-governance package required by ADR-027 before any mutating v2 implementation begins.

This task is design/planning only. It does not implement or activate the coordinator, programme state, allocation validator, Rust Quant Core, Python v2 strategy plane, Portal trace, deployment, model activation, private exchange access or real-capital behaviour.

## Authority freeze

Design/planning base: `develop@7aa9ce89d36adb503c83b20ffee8c9599982b33b`.

Binding authority:

- ADR-023 product authority;
- ADR-025 runtime/CI-placement authority;
- ADR-026 as promoted by ADR-027 for Quant Platform v2 core/migration target;
- repository `PROJECT_LANES.json`, `EXECUTION_PROTOCOL.md`, risk policy and closeout contracts.

The design/plan may narrow future implementation authority but cannot grant implementation by themselves.

## Owner-approved design

The exact owner-approved written spec remains unchanged from source commit `47f8c7196c0312a5fb5a013e3db4f4911f1239eb`, blob `9336b6a103a623261da90d3dafd467e478d1e101`.

Approved direction remains:

- dedicated V2 programme overlay; generic `PROJECT_LANES.json` remains generic authority;
- exactly one `quant-v2-implementation-coordinator`;
- fail-closed exact worker allocation authority;
- hard `V2-ENTRY-EVIDENCE` gate before bootstrap;
- serial bootstrap, bounded Core/Strategy/QA parallelism, Durability, Portal trace and serial V2-S1 integration;
- shared-contract serialization and stale-generation rebind;
- governance implementation merge ends in `GOVERNANCE_ACCEPTED_STANDBY` with zero V2 allocations;
- a later explicit owner command `Quant: implementacja v2` is required before activation;
- legacy `WDROŻENIE PAPER` is outside Quant v2 authority.

Implementation plan:

`docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md`

## Independent audit history

### Generation 1

Exact audited head: `58d5f5afaf4c208307f0681218ca869e2bfcb9b0`.

Verdict: `BLOCKED / MATERIAL_P1_FINDINGS`.

Findings:

- `QV2-1679-001` — design merge gate ordered after implementation;
- `QV2-1679-002` — dependency admission did not prove current predecessor truth;
- `QV2-1679-003` — generic 45-minute lease policy was not mechanically inherited.

### Generation 2

Exact audited head: `f83c7a811f198866e048f5ac97252151fe0b71b4`.

Durable audit comment: PR #1679 issue comment `5454136040`.

Verdict: `BLOCKED_MATERIAL_FINDINGS`.

New/remaining material findings:

- `QV2-1679-002` — predecessor truth remained caller-supplied;
- `QV2-1679-004` — programme state/incumbent census not canonical and exhaustive;
- `QV2-1679-005` — ENTRY-EVIDENCE self-deadlock;
- `QV2-1679-006` — incomplete legacy PAPER fence.

These were structurally remediated by introducing canonical `PROGRAMME_STATE.json`, complete allocation/task SHA bindings, ENTRY producer semantics, BOOTSTRAP evidence gate and full four-part PAPER fence.

### Generation 3

Exact audited head: `892cee6c4c5727da1d1da7720e43431eb7be9e01`.

Durable audit comment: PR #1679 issue comment `5455400415`.

Verdict: `BLOCKED_MATERIAL_FINDINGS` with one P1.

Prior status at generation 3:

- `QV2-1679-001` — REMEDIATED;
- `QV2-1679-002` — REMEDIATED IN STRUCTURE, subject to currentness issue below;
- `QV2-1679-003` — REMEDIATED IN STRUCTURE, subject to production-time issue below;
- `QV2-1679-004` — REMEDIATED IN STRUCTURE, subject to currentness issue below;
- `QV2-1679-005` — REMEDIATED;
- `QV2-1679-006` — REMEDIATED.

New finding:

- `QV2-1679-007` — production validator trust anchors remained caller-controlled: worker-selected repository snapshot/root, caller `expected_governance_sha`, caller-injected production `now`, and unsupported one-snapshot monotonic generation allowed stale self-consistent authority to appear current.

## Generation-3 remediation: trusted-current production authority

Plan remediation commit: `f7134a696de10c4b492c13a6b8d8b61dbaf57c38`.

The owner-approved spec was not changed.

The implementation plan now requires production admission to:

1. accept a repository location only as a Git locator plus candidate task path;
2. verify repository remote identity is `blakinio/freqtrade`;
3. fetch and resolve exact current `origin/develop` without changing the worker branch;
4. read `QUANT_V2_EXECUTION_GOVERNANCE.json`, `PROJECT_LANES.json` and `quant_v2/PROGRAMME_STATE.json` from that exact immutable trusted tree, never from caller-selected worker-tree files;
5. derive current governance identity from trusted `develop` history as the last commit changing the static governance file;
6. resolve previous/current `PROGRAMME_STATE.json` versions from trusted history and mechanically require generation `1` on creation or exact previous+1 on mutation;
7. require every active allocation to bind to current state generation;
8. obtain production time internally as timezone-aware current UTC;
9. expose no production CLI authority override for governance SHA, time, programme state, incumbent census, predecessor ledger, activation flags or develop SHA;
10. fail closed if current `develop`, current governance identity, state history or repository identity cannot be resolved.

Mandatory negative regressions now include:

- stale worker branch after allocation revoke/rebind on newer current `develop`;
- self-consistent stale governance snapshot versus newer trusted governance;
- attempted production `--now`/time override;
- attempted caller expected-governance-SHA override;
- regressed/skipped/non-current state generation;
- active allocation bound to prior generation;
- unavailable/ambiguous trusted `origin/develop` or wrong repository identity.

This closes the remaining trust-anchor gap without changing the owner-approved architecture.

## Risk

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
risk_gates:
  - deterministic_policy_regression
  - trusted_base_self_validation
  - independent_audit
```

Runtime/browser E2E is `NOT_APPLICABLE_WITH_REASON` for this design/planning-only task.

## Owned paths

- `docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md`
- `docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md`
- `docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-design.md`

No other path is authorized by this task.

## Acceptance

- owner-approved spec blob remains exact and unchanged;
- generic repository execution policy remains authoritative and contains no V2 DAG;
- design merge is Task 0 and hard predecessor of governance implementation;
- exactly one coordinator and approved DAG remain explicit;
- production worker authority is anchored to exact current trusted `origin/develop`, not a caller snapshot;
- expected governance identity is derived from trusted current history, not a CLI parameter;
- production lease expiry uses validator-owned current UTC with no ordinary override;
- canonical programme state is the sole dynamic state/allocation/predecessor truth after activation;
- state generation is mechanically bound to trusted Git history and current allocations bind current generation;
- production validator cannot omit incumbents or self-assert state/predecessor truth;
- activation has durable epoch/receipt binding;
- ENTRY can legally produce missing evidence without self-deadlock;
- BOOTSTRAP/later require exact independent PASS oracle + WH09 fixture;
- generic lease policy is inherited mechanically from current `PROJECT_LANES.execution.lease_minutes`;
- legacy PAPER path has complete four-part fence and reclassification-only behaviour;
- design/plan grants no V2 runtime/deployment/model/private-exchange/real-capital authority;
- governance implementation remains forbidden until the current exact PR head has fresh exact-head CI, fresh genuinely independent audit with zero material P0/P1 findings, and guarded merge.

## Context checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-28
branch: docs/quant-v2-execution-governance-design
pr: 1679
status: validating
phase: audit_remediation_v3
risk:
  governance_or_ci: true
authority_freeze:
  current_base_commit: 7aa9ce89d36adb503c83b20ffee8c9599982b33b
  owner_approved_spec_head: 47f8c7196c0312a5fb5a013e3db4f4911f1239eb
  owner_approved_spec_blob: 9336b6a103a623261da90d3dafd467e478d1e101
owned_paths:
  - docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md
  - docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md
  - docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-design.md
proven:
  - ADR-027 is merged binding Quant Platform v2 promotion authority
  - owner-approved spec is unchanged
  - generation-2 audit is durable as PR comment 5454136040
  - generation-3 audit is durable as PR comment 5455400415
  - QV2-1679-001 is remediated
  - QV2-1679-005 is remediated
  - QV2-1679-006 is remediated
validation:
  - owner-approved spec unchanged: PASS
  - QV2-1679-002 trusted-current predecessor truth remediation: PASS_SELF_REVIEW
  - QV2-1679-003 validator-owned UTC lease expiry remediation: PASS_SELF_REVIEW
  - QV2-1679-004 trusted-current programme/allocation census remediation: PASS_SELF_REVIEW
  - QV2-1679-007 production trust-anchor remediation: PASS_SELF_REVIEW
blockers:
  - new exact head requires fresh repository CI and genuinely independent exact-head re-audit
  - governance implementation remains forbidden until this design PR is qualified and merged
next_action: Require exact-head CI plus fresh independent audit explicitly retesting QV2-1679-001..007; guarded squash-merge only on zero material findings, then create post-merge governance implementation task/branch.
```
