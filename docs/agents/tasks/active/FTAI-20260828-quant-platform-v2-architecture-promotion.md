---
task_id: FTAI-20260828-quant-platform-v2-architecture-promotion
repository: blakinio/freqtrade
branch: docs/quant-v2-architecture-promotion
status: validating
execution_mode: github_only
trusted_base: c9bbd17c716162edffd5b695eac4fb197c7bbf38
candidate_pr: 1676
promotion_pr: 1677
---

# Quant Platform v2 bounded architecture promotion

## Objective

Promote the independently qualified ADR-026 / Quant Platform v2 target to binding architecture through a separate governance change, while preserving ADR-023 product authority, ADR-025 runtime/CI placement, historical candidate evidence and the architecture-before-execution gate. The promotion may include only the minimum CI/governance compatibility repair required for the existing trusted-base validators to interpret the promoted layered authority correctly.

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

Runtime/product E2E is `NOT_APPLICABLE` for the promotion itself because it changes architecture/governance authority plus a bounded CI authority-resolution helper only; it does not change user/runtime behavior. The CI compatibility repair is covered by its focused regression test and the exact-head component workflow. Runtime/E2E proof remains required by the promoted architecture at implementation/deployment gates.

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
- `docs/agents/tasks/active/FTAI-20260828-quant-platform-v2-architecture-promotion.md`
- `docs/ai_platform/portal/README.md`
- `docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md`
- `docs/ai_platform/portal/ADR-027_QUANT_PLATFORM_V2_ARCHITECTURE_PROMOTION.md`
- `docs/ai_platform/reviews/2026-08-28-quant-platform-v2-architecture-qualification.md`
- `.github/workflows/portal-completeness-audit.yml`
- `tools/portal_audit/validate_issue_states.py`
- `tools/portal_audit/tests/test_audit_ledger.py`

## Acceptance

- ADR-026 exact qualified candidate is durably identified by PR/head and qualification evidence.
- A separate accepted promotion decision makes the v2 target binding without rewriting the candidate's historical lifecycle metadata.
- `ARCHITECTURE_REGISTRY.yaml` moves `latest_architecture_change` to the promotion and marks the candidate `qualified_and_promoted` while preserving implementation status as target-only/unproven.
- Root/agent/Portal authority routing points agents to ADR-023 + ADR-025 + promoted ADR-026/ADR-027 with no duplicate authority.
- Freqtrade current paths are explicitly migration/reference compatibility, not permanent v2 target state ownership.
- No implementation/control-plane authority is created by promotion; V2-S1 remains gated on a separate execution-governance package and entry evidence.
- Existing Portal audit CI recognizes ADR-023 as retained product authority under ADR-027 without weakening its fail-closed fallback when that authority is not proven.
- Focused policy regression and trusted-base self-validation pass.
- Relevant CI is green on the exact final promotion PR head.
- Fresh independent audit of the promotion diff has no unresolved material finding before merge.
- Merge, if authorized by all gates, is squash to `develop` with source-branch cleanup.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-28T10:38:00Z
branch: docs/quant-v2-architecture-promotion
head_before_checkpoint_commit: 0873c9305b065643b8f315e764bba5f2b9120287
pr: 1677
status: validating
authority_freeze:
  current_base_commit: c9bbd17c716162edffd5b695eac4fb197c7bbf38
proven:
  - PR #1676 exact candidate head is 5efda8fc9297f9387fffcfc7c81e604baee4e8bf and merged candidate commit is c9bbd17c716162edffd5b695eac4fb197c7bbf38
  - exact candidate changed three architecture files and was independently qualified with no unresolved current-gate P0/P1 architecture blocker
  - PR #1677 is the separate bounded promotion PR targeting frozen develop@c9bbd17c716162edffd5b695eac4fb197c7bbf38
  - accepted decision log changes only by appending ADR-027; historical ADR-020 wording was restored after self-review
  - canonical registry points latest_architecture_change to ADR-027 and records ADR-026 as qualified_and_promoted while keeping implementation target_only/unproven
  - ADR-023 product and ADR-025 placement authority remain explicit; ADR-027 adds only v2 core/migration target authority
  - architecture promotion leaves implementation lanes/control-plane/DAG behind a separate execution-governance gate and leaves V2-S1 reference-oracle/WH09 fixture entry evidence gated
  - exact-head CI on 908d7ac2a4b3f7e2b4b12c26a0376d2e9a28bfc1 exposed an EOF formatting defect in three promotion documents and a stale Portal audit authority detector that incorrectly re-enabled the legacy closed-Issue gate after ADR-027 promotion
  - TDD RED was proven on 0873c9305b065643b8f315e764bba5f2b9120287 in Risk-aware component CI run 33163711048, job 98825127743; test_adr027_registry_retains_adr023_product_authority failed exactly with AssertionError True is not false before authority resolution executed
  - the bounded repair centralizes ADR-023 retained-authority detection in validate_issue_states.py, accepts either direct ADR-023 decision or ADR-027 product_decision layering, and retains fail-closed legacy behavior when the required authority/vocabulary markers are not proven
unknown:
  - exact-final-head relevant CI result after the GREEN repair commit
  - fresh independent audit result for promotion PR #1677
conflicts: []
validation:
  - candidate architecture qualification: QUALIFIED
  - promotion full-diff self-review: PASS_BEFORE_CI_REPAIR
  - TDD RED for ADR-027 retained ADR-023 authority: PASS_EXPECTED_FAILURE_OBSERVED
  - trusted-base self-validation: PENDING_EXACT_HEAD_GREEN
  - promotion policy regression: PENDING_EXACT_HEAD_GREEN
  - exact-final-head CI: PENDING
  - promotion independent audit: PENDING
blockers:
  - merge remains gated on exact-final-head CI and a fresh independent promotion audit
next_action: Verify the GREEN repair on exact-final-head CI for PR #1677, then obtain a fresh independent audit and merge only if both gates pass with no unresolved material finding.
```
