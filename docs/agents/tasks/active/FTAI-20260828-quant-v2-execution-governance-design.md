---
task_id: FTAI-20260828-quant-v2-execution-governance-design
repository: blakinio/freqtrade
project_lane: freqtrade-core
branch: docs/quant-v2-execution-governance-design
status: designing
phase: design_spec
execution_mode: github_only
task_kind: architecture_design
implementation_authorized: false
trusted_base: 7aa9ce89d36adb503c83b20ffee8c9599982b33b
runtime_access: none
ownership_released: false
---

# Quant Platform v2 execution-governance design

## Objective

Persist the owner-approved design for the separate Quant Platform v2 execution-governance package required by ADR-027 before any mutating v2 implementation begins.

This task is **specification only**. It must not implement the coordinator, machine governance overlay, aliases, validators, lanes, Rust Quant Core, Python v2 strategy plane, Portal trace, deployment or runtime behavior.

## Authority freeze

Design base: `develop@7aa9ce89d36adb503c83b20ffee8c9599982b33b`.

Binding architecture:

- ADR-023 product authority;
- ADR-025 runtime/CI-placement authority;
- ADR-026 as promoted by ADR-027 for Quant Platform v2 core/migration target;
- repository `PROJECT_LANES.json`, `EXECUTION_PROTOCOL.md`, risk policy and closeout contracts.

The design may narrow future implementation authority but cannot grant implementation by itself.

## Approved direction

The owner approved the dedicated V2 overlay approach rather than expanding the generic `PROJECT_LANES.json` into a full V2 control plane or creating one permanent lead prompt per lane.

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

Runtime/browser E2E is `NOT_APPLICABLE` for this design-only documentation task.

## Owned paths

- `docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md`
- `docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-design.md`

No other path is authorized by this design task.

## Acceptance

- written spec faithfully captures the owner-approved dedicated-overlay approach;
- generic repository execution policy remains authoritative and is not duplicated;
- one coordinator and the approved V2-S1 DAG are explicit;
- allocation, path ownership, dependency, lease, shared-surface and stale-state handling are fail-closed;
- V2-ENTRY-EVIDENCE requires exact reference/parity oracle plus canonical WickHunter/WH09 fixture before bootstrap;
- legacy `WDROŻENIE PAPER` is fenced from V2 authority in the future implementation design;
- spec creates no V2 implementation/deployment/model/private-exchange/real-capital authority;
- no placeholder/TBD ambiguity remains in the written design;
- owner reviews the written spec before any implementation plan is created.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-28T14:44:08+02:00
branch: docs/quant-v2-execution-governance-design
head: 7aa9ce89d36adb503c83b20ffee8c9599982b33b
pr: none
status: designing
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
  - docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-design.md
proven:
  - ADR-027 is merged binding Quant Platform v2 promotion authority
  - the prior architecture-promotion task is terminally archived and ownership released
  - ADR-027 requires a separate execution-governance package before mutating v2 implementation
  - V2-S1 entry still requires reference/parity oracle and canonical WickHunter/WH09 fixture evidence
  - repository PROJECT_LANES schema version 2 provides generic 30-minute checkpoint and 45-minute lease/staleness policy plus validation/decomposition defaults
  - repository EXECUTION_PROTOCOL requires one writer per branch/path and exact-state/risk-based validation
  - owner approved the dedicated V2 overlay and the proposed V2-S1 DAG
unknown:
  - owner written-spec review verdict
conflicts: []
first_failure: none
changed_paths:
  - docs/superpowers/specs/2026-08-28-quant-v2-execution-governance-design.md
  - docs/agents/tasks/active/FTAI-20260828-quant-v2-execution-governance-design.md
validation:
  - repository live-state and overlap preflight: PASS
  - written-spec self-review: PENDING_AFTER_COMMIT
blockers:
  - implementation planning is blocked until owner reviews and approves the committed written spec
next_action: Commit the design spec and checkpoint, self-review the exact diff, open a draft spec-review PR, then ask the owner to approve or request changes to the written spec.
```
