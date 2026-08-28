---
task_id: FTAI-20260828-quant-v2-execution-governance-design
repository: blakinio/freqtrade
project_lane: freqtrade-core
branch: docs/quant-v2-execution-governance-design
status: planning
phase: implementation_plan
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

This task is still **design/planning only**. It does not implement the coordinator, machine governance overlay, aliases, validators, lanes, Rust Quant Core, Python v2 strategy plane, Portal trace, deployment or runtime behavior.

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

The implementation plan is recorded at:

`docs/superpowers/plans/2026-08-28-quant-v2-execution-governance.md`

It requires the later governance implementation package to end in `GOVERNANCE_ACCEPTED_STANDBY`. Neither this design task nor the governance merge may automatically issue `Quant: implementacja v2` or create a V2 implementation allocation.

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
- owner has approved the exact committed written spec;
- implementation plan covers the machine overlay, validator, coordinator prompt, owner routing, legacy PAPER fence, prompt regression, exact-head validation/audit and lifecycle closeout;
- generic repository execution policy remains authoritative and is not duplicated;
- one coordinator and the approved V2-S1 DAG are explicit;
- allocation, path ownership, dependency, lease, shared-surface and stale-state handling are fail-closed;
- V2-ENTRY-EVIDENCE requires exact reference/parity oracle plus canonical WickHunter/WH09 fixture before bootstrap;
- legacy `WDROŻENIE PAPER` is fenced from V2 authority in the planned implementation;
- design/plan creates no V2 implementation/deployment/model/private-exchange/real-capital authority;
- governance implementation remains blocked until this design/spec/plan package itself is independently validated and merged.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-28T15:51:09+02:00
branch: docs/quant-v2-execution-governance-design
head: 47f8c7196c0312a5fb5a013e3db4f4911f1239eb
pr: 1679
status: planning
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
  - the prior architecture-promotion task is terminally archived and ownership released
  - ADR-027 requires a separate execution-governance package before mutating v2 implementation
  - V2-S1 entry still requires reference/parity oracle and canonical WickHunter/WH09 fixture evidence
  - repository PROJECT_LANES schema version 2 provides generic checkpoint/lease/staleness policy plus validation/decomposition defaults
  - repository EXECUTION_PROTOCOL requires one writer per branch/path and exact-state/risk-based validation
  - owner approved the dedicated V2 overlay and the proposed V2-S1 DAG
  - owner approved the committed written spec at 47f8c7196c0312a5fb5a013e3db4f4911f1239eb
  - governance merge is designed to stop in GOVERNANCE_ACCEPTED_STANDBY until a later explicit Quant: implementacja v2 owner command
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
  - implementation-plan self-review: PENDING_AFTER_COMMIT
blockers:
  - governance implementation must not begin until the design/spec/plan PR is exact-head validated, independently audited and merged
next_action: Commit the implementation plan and refreshed checkpoint, self-review the exact PR diff, then run exact-head CI and a fresh independent design/governance audit before merge.
```
