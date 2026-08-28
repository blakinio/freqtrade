---
task_id: FTAI-20260828-quant-platform-v2-architecture-promotion
repository: blakinio/freqtrade
branch: docs/quant-v2-architecture-promotion
status: implementing
execution_mode: github_only
trusted_base: c9bbd17c716162edffd5b695eac4fb197c7bbf38
candidate_pr: 1676
promotion_pr: null
---

# Quant Platform v2 bounded architecture promotion

## Objective

Promote the independently qualified ADR-026 / Quant Platform v2 target to binding architecture through a separate governance-only change, while preserving ADR-023 product authority, ADR-025 runtime/CI placement, historical candidate evidence and the architecture-before-execution gate.

## Authority freeze

This governance change closes under the trusted-base rules at `develop@c9bbd17c716162edffd5b695eac4fb197c7bbf38`. Unmerged changes in this branch may not waive or reduce their own policy regression, trusted-base self-validation or independent-audit requirements.

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
  - policy_regression
  - trusted_base_self_validation
  - independent_audit
```

E2E: `NOT_APPLICABLE` for the promotion itself because it changes architecture/governance documentation only and no user/runtime behavior. Runtime/E2E proof remains required by the promoted architecture at implementation/deployment gates.

## Non-goals

- no Rust/Python/TypeScript runtime implementation;
- no implementation lanes/control-plane/DAG in this promotion change;
- no deployment, Synology mutation, model/strategy activation or private credentials;
- no real order, withdrawal or real-capital authority;
- no rewriting historical PR/ADR evidence.

## Owned paths

- `ARCHITECTURE_REGISTRY.yaml`
- `AGENTS.md`
- `docs/agents/AGENTS.md`
- `docs/ai_platform/portal/README.md`
- `docs/ai_platform/portal/ADR-027_QUANT_PLATFORM_V2_ARCHITECTURE_PROMOTION.md`
- `docs/ai_platform/reviews/2026-08-28-quant-platform-v2-architecture-qualification.md`
- this task record

## Acceptance

- ADR-026 exact qualified candidate is durably identified by PR/head and qualification evidence.
- A separate accepted promotion decision makes the v2 target binding without rewriting the candidate's historical lifecycle metadata.
- `ARCHITECTURE_REGISTRY.yaml` moves `latest_architecture_change` to the promotion and marks the candidate `qualified_and_promoted` while preserving implementation status as target-only/unproven.
- Root/agent/Portal authority routing points agents to ADR-023 + ADR-025 + promoted ADR-026/ADR-027 with no duplicate authority.
- Freqtrade current paths are explicitly migration/reference compatibility, not permanent v2 target state ownership.
- No implementation/control-plane authority is created by promotion; V2-S1 remains gated on a separate execution-governance package and entry evidence.
- Focused policy regression and trusted-base self-validation pass.
- Relevant CI is green on the exact final promotion PR head.
- Fresh independent audit of the promotion diff has no unresolved material finding before merge.
- Merge, if authorized by all gates, is squash to `develop` with source-branch cleanup.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-28T08:37:00Z
branch: docs/quant-v2-architecture-promotion
head: 0c1babddf497176602c546ed4fe548a6b482f033
pr: null
status: implementing
authority_freeze:
  current_base_commit: c9bbd17c716162edffd5b695eac4fb197c7bbf38
proven:
  - PR #1676 exact candidate head is 5efda8fc9297f9387fffcfc7c81e604baee4e8bf and merged candidate commit is c9bbd17c716162edffd5b695eac4fb197c7bbf38
  - exact candidate changed three architecture files
  - exact candidate checks are terminal with no observed failure/in-progress; CI Gate and CodeQL succeeded
  - read-only exact-state candidate qualification found no unresolved current-gate P0/P1 architecture blocker
  - ADR-027 now records the bounded promotion relationship without implementation/live authority
unknown:
  - final promotion diff/validation and exact-head CI
  - fresh independent audit result for the promotion PR itself
conflicts: []
validation:
  - candidate architecture qualification: QUALIFIED
  - promotion policy regression: NOT_RUN
  - trusted-base self-validation: NOT_RUN
  - exact-final-head CI: NOT_RUN
blockers: []
next_action: Synchronize canonical registry and agent/Portal authority routing with ADR-027, then run focused governance validation and open the promotion PR.
```
