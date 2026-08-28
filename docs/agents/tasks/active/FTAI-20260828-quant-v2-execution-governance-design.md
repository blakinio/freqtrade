---
task_id: FTAI-20260828-quant-v2-execution-governance-design
repository: blakinio/freqtrade
project_lane: freqtrade-core
branch: docs/quant-v2-execution-governance-design
status: validating
phase: design_plan_review
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

Persist the owner-approved design and implementation plan for the separate Quant Platform v2 execution-governance package required by ADR-027 before any mutating v2 implementation begins.

This task remains **design/planning only**. It does not implement the coordinator, machine governance overlay, aliases, validators, lanes, Rust Quant Core, Python v2 strategy plane, Portal trace, deployment or runtime behavior.

## Authority freeze

Design/planning base: `develop@7aa9ce89d36adb503c83b20ffee8c9599982b33b`.

Binding architecture:

- ADR-023 product authority;
- ADR-025 runtime/CI-placement authority;
- ADR-026 as promoted by ADR-027 for Quant Platform v2 core/migration target;
- repository `PROJECT_LANES.json`, `EXECUTION_PROTOCOL.md`, risk policy and closeout contracts.

The design and plan may narrow future implementation authority but cannot grant implementation by themselves.

## Owner-approved design

The owner approved the committed written spec at `47f8c7196c0312a5fb5a013e3db4f4911f1239eb` and the dedicated V2 overlay approach rather than expanding the generic `PROJECT_LANES.json` into a full V2 control plane or creating one permanent lead prompt per lane.

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

The self-reviewed implementation plan is:

`docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md`

It explicitly requires mechanical validation of stale governance SHA, lease expiry, exact dependency IDs, lane allowed-path families, path overlap, shared-surface overlap, programme-state eligibility and forbidden authority widening.

The later governance implementation package must end in `GOVERNANCE_ACCEPTED_STANDBY`. Neither this design task nor the governance merge may automatically issue `Quant: implementacja v2` or create a V2 implementation allocation.

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

- written spec faithfully captures the owner-approved dedicated-overlay approach;
- owner approved the exact committed written spec;
- implementation plan covers the machine overlay, state machine, validator, coordinator prompt, owner routing, legacy PAPER fence, prompt regression, exact-head validation/audit and lifecycle closeout;
- validator plan includes fail-closed stale-governance, lease, dependency, path-family, path/shared-surface overlap and authority-widening cases;
- generic repository execution policy remains authoritative and is not duplicated;
- one coordinator and the approved V2-S1 DAG are explicit;
- V2-ENTRY-EVIDENCE requires exact reference/parity oracle plus canonical WickHunter/WH09 fixture before bootstrap;
- legacy `WDROŻENIE PAPER` is fenced from V2 authority in the planned implementation;
- design/plan creates no V2 implementation/deployment/model/private-exchange/real-capital authority;
- governance implementation remains blocked until this design/spec/plan package is exact-head validated, independently audited and merged.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-28T15:51:09+02:00
branch: docs/quant-v2-execution-governance-design
head_before_checkpoint: 16bd5415276369999b352bcc899c4ba1a086f550
pr: 1679
status: validating
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
owned_paths:
  - docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md
  - docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md
  - docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-design.md
proven:
  - ADR-027 is merged binding Quant Platform v2 promotion authority
  - prior architecture-promotion lifecycle is terminal
  - owner approved the dedicated V2 overlay, DAG and exact committed written spec
  - implementation plan preserves PROJECT_LANES as generic authority
  - implementation plan mechanically covers stale governance SHA, lease expiry, lane paths, dependency IDs, owned-path overlap, shared-surface overlap and authority widening
  - governance implementation post-merge state is GOVERNANCE_ACCEPTED_STANDBY until a later explicit Quant: implementacja v2 owner command
unknown: []
conflicts: []
first_failure: none
changed_paths:
  - docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md
  - docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md
  - docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-design.md
validation:
  - repository live-state and overlap preflight: PASS
  - written-spec self-review: PASS
  - owner written-spec review: APPROVED
  - implementation-plan spec coverage: PASS
  - implementation-plan placeholder scan: PASS
  - implementation-plan interface/type consistency: PASS
  - implementation-plan scope check: PASS
blockers:
  - governance implementation must not begin until PR #1679 is exact-head validated, independently audited and merged
next_action: Make PR #1679 ready for review, require exact-head CI and a fresh independent design/governance audit, then guarded squash-merge only if the unchanged head has zero material findings.
```
