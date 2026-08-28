---
task_id: FTAI-20260828-quant-v2-execution-governance-design
repository: blakinio/freqtrade
project_lane: freqtrade-core
branch: docs/quant-v2-execution-governance-design
status: validating
phase: audit_remediation_v2
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

This task remains **design/planning only**. It does not implement or activate the coordinator, dynamic programme state, allocation validator, Rust Quant Core, Python v2 strategy plane, Portal trace, deployment, model activation, private exchange access or real-capital behaviour.

## Authority freeze

Design/planning base: `develop@7aa9ce89d36adb503c83b20ffee8c9599982b33b`.

Binding authority:

- ADR-023 product authority;
- ADR-025 runtime/CI-placement authority;
- ADR-026 as promoted by ADR-027 for Quant Platform v2 core/migration target;
- repository `PROJECT_LANES.json`, `EXECUTION_PROTOCOL.md`, risk policy and closeout contracts.

The design and plan may narrow future implementation authority but cannot grant implementation by themselves.

## Owner-approved design

The exact owner-approved written spec remains unchanged at source commit `47f8c7196c0312a5fb5a013e3db4f4911f1239eb` and blob `9336b6a103a623261da90d3dafd467e478d1e101`.

Approved direction remains:

- dedicated V2 programme overlay; generic `PROJECT_LANES.json` remains generic authority;
- exactly one `quant-v2-implementation-coordinator`;
- fail-closed exact worker allocation authority;
- hard `V2-ENTRY-EVIDENCE` gate for exact reference/parity oracle plus canonical WickHunter/WH09 fixture before bootstrap;
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

Generation-1 remediation introduced Task 0, predecessor state/evidence checks and generic lease source/mirror enforcement.

### Generation 2

Exact audited head: `f83c7a811f198866e048f5ac97252151fe0b71b4`.

Durable independent audit comment: PR #1679 issue comment `5454136040`.

Verdict: `BLOCKED_MATERIAL_FINDINGS` with four material P1 findings.

Status of prior findings:

- `QV2-1679-001` — REMEDIATED;
- `QV2-1679-003` — REMEDIATED;
- `QV2-1679-002` — PARTIAL / STILL BLOCKING because predecessor truth remained caller-supplied rather than canonical.

New findings:

- `QV2-1679-004` — programme state and incumbent allocation census were caller-supplied/incomplete rather than canonical and exhaustive;
- `QV2-1679-005` — ENTRY-EVIDENCE admission self-deadlocked by requiring its own missing outputs to PASS before the lane could write them;
- `QV2-1679-006` — planned legacy PAPER fence implemented only `quant_v2_authority:false`, weaker than the approved four-part fence plus reclassification-only behaviour.

## Generation-2 remediation

Plan remediation commit: `7b551628288b05dce5540981c8a07d6614fba9c6`.

The owner-approved spec was not changed.

### QV2-1679-002 / QV2-1679-004 — canonical current-state authority

The plan no longer allows production validator callers to supply partial `active_allocations`, ad-hoc `predecessor_states`, free-form programme state or activation flags.

It now defines one canonical dynamic state path:

`docs/agents/quant_v2/PROGRAMME_STATE.json`

Semantics:

- absent on trusted `develop` means only `GOVERNANCE_ACCEPTED_STANDBY` with zero allocations;
- absence never grants worker write authority;
- after explicit owner activation the coordinator first persists an immutable activation receipt and canonical programme state;
- canonical state contains current programme state/generation, activation epoch/receipt binding, the complete active-allocation index and canonical predecessor terminal/evidence ledger;
- every allocation entry binds to the exact worker task path plus SHA-256 of task bytes;
- production validator derives all incumbent overlap and predecessor checks from canonical state only;
- omitted incumbents, forged programme state, incomplete indexes, stale predecessor evidence and state/receipt mismatches are mandatory fail-closed regression cases.

### QV2-1679-005 — ENTRY-EVIDENCE producer admission

The plan now explicitly permits a valid `V2-ENTRY-EVIDENCE` allocation after durable owner activation while the target oracle/WH09 artifacts are initially absent or `UNKNOWN`, provided all other fences pass and `repository_implementation=false`.

Exact immutable independent `PASS` evidence for both artifacts is required for `V2-BOOTSTRAP` and later lanes, not for admitting the ENTRY producer lane itself.

Mandatory regression pair:

- clean activation + ENTRY with missing/UNKNOWN target artifacts -> PASS;
- BOOTSTRAP while either artifact is not exact independent PASS -> FAIL.

### QV2-1679-006 — complete legacy PAPER fence

The plan now requires machine contract, prompt and routing to enforce exactly:

```yaml
quant_v2_authority: false
may_allocate_quant_v2_lanes: false
may_mutate_quant_v2_governance: false
treatment: legacy_closeout_or_reclassification_only
```

`WDROŻENIE PAPER` / `WDROŻENIE PAPER dalej` may close out valid legacy work but may not create/take over V2 allocations, mutate Quant-v2 governance/state, claim V2-owned/shared surfaces, or perform further target-driven mutation without reclassification under ADR-023/025/027.

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

Runtime/browser E2E is `NOT_APPLICABLE_WITH_REASON` for this design/planning-only documentation task.

## Owned paths

- `docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md`
- `docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md`
- `docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-design.md`

No other path is authorized by this design/planning task.

## Acceptance

- owner-approved spec blob remains exact and unchanged;
- generic repository execution policy remains authoritative and does not contain the V2 DAG;
- design merge is Task 0 and a hard predecessor of governance implementation;
- exactly one coordinator and the approved V2-S1 DAG remain explicit;
- canonical programme state is the sole dynamic programme-state/allocation/predecessor truth after activation;
- production validator cannot omit incumbents or self-assert programme/predecessor state;
- activation has a durable epoch/receipt binding;
- `V2-ENTRY-EVIDENCE` can legally produce missing evidence without self-deadlock;
- BOOTSTRAP/later lanes require exact independent PASS oracle + canonical WH09 fixture;
- generic lease policy is inherited mechanically from `PROJECT_LANES.execution.lease_minutes`;
- legacy PAPER path has the complete four-part fence and reclassification-only behaviour;
- design/plan creates no V2 implementation/deployment/model/private-exchange/real-capital authority;
- governance implementation remains blocked until this new exact PR head has fresh exact-head CI, a fresh genuinely independent audit with zero material P0/P1 findings, and guarded merge.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-28
branch: docs/quant-v2-execution-governance-design
pr: 1679
status: validating
phase: audit_remediation_v2
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
  - prior architecture-promotion lifecycle is terminal
  - owner-approved spec is unchanged
  - QV2-1679-001 is remediated
  - QV2-1679-003 is remediated
  - generation-2 independent audit is durable as PR comment 5454136040
  - generation-2 plan remediation commit is 7b551628288b05dce5540981c8a07d6614fba9c6
validation:
  - owner-approved spec unchanged: PASS
  - QV2-1679-002 canonical predecessor truth remediation: PASS_SELF_REVIEW
  - QV2-1679-004 canonical programme/allocation census remediation: PASS_SELF_REVIEW
  - QV2-1679-005 ENTRY self-deadlock remediation: PASS_SELF_REVIEW
  - QV2-1679-006 complete legacy PAPER fence remediation: PASS_SELF_REVIEW
blockers:
  - new exact head requires fresh repository CI and genuinely independent exact-head re-audit
  - governance implementation remains forbidden until this design PR is qualified and merged
next_action: Require exact-head CI plus a fresh independent audit explicitly retesting QV2-1679-001..006; guarded squash-merge only on zero material findings, then create the post-merge governance implementation task/branch.
```
