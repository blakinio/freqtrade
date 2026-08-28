---
task_id: FTAI-20260828-quant-v2-execution-governance-design
repository: blakinio/freqtrade
project_lane: freqtrade-core
branch: docs/quant-v2-execution-governance-design
status: validating
phase: audit_remediation
execution_mode: github_only
task_kind: architecture_design
implementation_authorized: false
trusted_base: 7aa9ce89d36adb503c83b20ffee8c9599982b33b
spec_head: 47f8c7196c0312a5fb5a013e3db4f4911f1239eb
spec_owner_review: approved
runtime_access: none
ownership_released: false
---

# Quant Platform v2 execution-governance design

## Objective

Persist the owner-approved design and a qualified implementation plan for the separate Quant Platform v2 execution-governance package required by ADR-027 before any mutating v2 implementation begins.

This task remains **design/planning only**. It does not implement the coordinator, machine governance overlay, aliases, validators, lanes, Rust Quant Core, Python v2 strategy plane, Portal trace, deployment or runtime behaviour.

## Authority freeze

Design/planning base: `develop@7aa9ce89d36adb503c83b20ffee8c9599982b33b`.

Binding architecture:

- ADR-023 product authority;
- ADR-025 runtime/CI-placement authority;
- ADR-026 as promoted by ADR-027 for Quant Platform v2 core/migration target;
- repository `PROJECT_LANES.json`, `EXECUTION_PROTOCOL.md`, risk policy and closeout contracts.

The design and plan may narrow future implementation authority but cannot grant implementation by themselves.

## Owner-approved design

The owner approved the committed written spec at `47f8c7196c0312a5fb5a013e3db4f4911f1239eb`. That spec is intentionally unchanged by this audit-remediation cycle.

Approved direction remains:

- dedicated V2 programme overlay rather than turning generic `PROJECT_LANES.json` into a V2 control plane;
- exactly one `quant-v2-implementation-coordinator`;
- fail-closed exact allocation authority;
- hard `V2-ENTRY-EVIDENCE` gate requiring exact reference/parity oracle plus canonical WickHunter/WH09 fixture evidence;
- serial bootstrap, bounded Core/Strategy/QA parallelism, Durability, Portal trace and serial V2-S1 integration;
- shared-contract serialization and stale-generation rebind;
- future `Quant: implementacja v2` activation only after the governance package is independently qualified and merged;
- legacy `WDROŻENIE PAPER` outside Quant v2 authority;
- governance implementation merge ends in `GOVERNANCE_ACCEPTED_STANDBY` with zero V2 allocations.

Approved DAG:

```text
QUANT-V2-COORD
      |
      v
V2-ENTRY-EVIDENCE
      |
      v
V2-BOOTSTRAP [SERIAL]
      |
      +--> V2-CORE
      +--> V2-STRATEGY
      +--> V2-QA
               |
V2-CORE ------> V2-DURABILITY
               |
V2-CORE + V2-STRATEGY + V2-DURABILITY
      -> V2-PORTAL-TRACE
               |
V2-CORE + V2-STRATEGY + V2-DURABILITY + V2-PORTAL-TRACE + V2-QA
      -> V2-S1-INTEGRATION [SERIAL]
```

Implementation plan:

`docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md`

## Independent audit remediation

A genuinely fresh independent audit froze PR #1679 at exact head:

`58d5f5afaf4c208307f0681218ca869e2bfcb9b0`

Terminal content verdict for that generation was:

`BLOCKED / MATERIAL_P1_FINDINGS`

No standalone GitHub review object was emitted; this task records the findings as remediation evidence only, not as a fabricated review submission.

### QV2-1679-001 — design merge gate ordered too late

**Finding:** the prior plan placed the required design qualification/merge inside Task 4 after implementation Tasks 1-3, despite claiming governance implementation must not begin before the design PR merges.

**Remediation:** the plan now makes design qualification and guarded merge **Task 0**, with hard order `Task 0 -> Task 1 -> Task 2 -> Task 3 -> Task 4`. Tasks 1-3 explicitly may not execute on the design branch or before Task 0 is terminal `DESIGN_MERGED_QUALIFIED`.

### QV2-1679-002 — dependency admission did not prove predecessor truth

**Finding:** the prior validator plan checked the exact dependency ID set but did not mechanically prove that each predecessor is currently in its required terminal state/status with the exact current immutable evidence identity.

**Remediation:** the validator contract now consumes `predecessor_states` and requires for every dependency: exact ID, current required state, immutable 40-hex evidence identity and exact equality between allocation evidence and the current predecessor evidence. Missing, stale, nonterminal or mismatched evidence fails closed. The negative test matrix now includes missing predecessor state, nonterminal predecessor and evidence mismatch cases.

### QV2-1679-003 — inherited 45-minute lease policy was not mechanically enforced

**Finding:** generic repository authority fixes `PROJECT_LANES.execution.lease_minutes` at 45 minutes, while the prior V2 validator only checked lease expiry at injected `now`.

**Remediation:** the plan now requires the V2 machine contract to mirror the generic lease source and the validator to load `PROJECT_LANES.json`, require source/mirror equality, require expiry after acquisition, require unexpired lease, and enforce `(lease_expires_at - lease_acquired_at) <= lease_minutes`. The accepted-base value is exactly 45 minutes. Oversized leases and policy-source mismatch have mandatory RED/GREEN regressions.

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

Runtime/browser E2E is `NOT_APPLICABLE` for this design/planning-only documentation task.

## Owned paths

- `docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md`
- `docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md`
- `docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-design.md`

No other path is authorized by this design/planning task.

## Acceptance

- owner-approved written spec remains exact and unchanged at `47f8c7196c0312a5fb5a013e3db4f4911f1239eb`;
- generic repository execution policy remains authoritative and is not duplicated;
- design merge is mechanically ordered before governance implementation;
- one coordinator and approved V2-S1 DAG remain explicit;
- validator design is fail-closed for governance SHA, exact dependency ID set, current predecessor terminal state/evidence, generic 45-minute lease policy, lane path families, owned-path overlap, shared-surface overlap, programme state and forbidden authority widening;
- V2-ENTRY-EVIDENCE requires exact reference/parity oracle plus canonical WickHunter/WH09 fixture before bootstrap;
- legacy `WDROŻENIE PAPER` is fenced from V2 authority in planned implementation;
- design/plan creates no V2 implementation/deployment/model/private-exchange/real-capital authority;
- governance implementation remains blocked until this remediated exact PR head has fresh exact-head CI, a fresh independent audit with zero material P0/P1 findings, and guarded merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-28
branch: docs/quant-v2-execution-governance-design
pr: 1679
status: validating
phase: audit_remediation
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
authority_freeze:
  current_base_commit: 7aa9ce89d36adb503c83b20ffee8c9599982b33b
  owner_approved_spec_head: 47f8c7196c0312a5fb5a013e3db4f4911f1239eb
owned_paths:
  - docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md
  - docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md
  - docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-design.md
proven:
  - ADR-027 is merged binding Quant Platform v2 promotion authority
  - prior architecture-promotion lifecycle is terminal
  - owner approved the exact dedicated-overlay design spec
  - develop remains frozen at 7aa9ce89d36adb503c83b20ffee8c9599982b33b during this remediation
  - independent audit of 58d5f5afaf4c208307f0681218ca869e2bfcb9b0 returned QV2-1679-001, QV2-1679-002 and QV2-1679-003 as material P1 findings
  - remediated plan orders the design merge gate before implementation, validates current predecessor state/evidence, and mechanically inherits the generic 45-minute lease policy
unknown: []
conflicts: []
first_failure: independent audit material P1 findings on prior head 58d5f5afaf4c208307f0681218ca869e2bfcb9b0
changed_paths:
  - docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md
  - docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-design.md
validation:
  - owner-approved spec unchanged: PASS
  - QV2-1679-001 plan ordering remediation: PASS_SELF_REVIEW
  - QV2-1679-002 dependency truth/evidence remediation: PASS_SELF_REVIEW
  - QV2-1679-003 generic lease inheritance remediation: PASS_SELF_REVIEW
blockers:
  - new exact head requires fresh repository CI and genuinely independent exact-head re-audit
  - governance implementation remains forbidden until this design PR is qualified and merged
next_action: Require exact-head CI plus a fresh independent re-audit explicitly retesting QV2-1679-001/002/003; guarded squash-merge only on zero material findings, then create the post-merge governance implementation task/branch.
```
