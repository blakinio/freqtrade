---
task_id: FTAI-20260730-closure-feature-engine
status: validating
branch: agent/closure-feature-engine
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 780
dependencies:
  - none
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-feature-engine.md
  - ai_strategy_engine/src/strategy_engine/features/support_resistance.py
  - ai_strategy_engine/configs/feature_registry.v1.yaml
  - ai_strategy_engine/tests/unit/test_support_resistance.py
  - ai_strategy_engine/tests/integration/test_registry_support_resistance.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - ai_strategy_engine/TASKS.md
search_first:
  - current develop, open PRs and exact owned-path conflicts
  - canonical implementation and tests before adding code
  - shared contract freeze commit and dependency state
---

# Closure support and resistance feature

## Goal

Implement only the remaining support/resistance feature gap and register it with point-in-time semantics.

## Evidence at Gate 0

ATR, moving averages, BB/KC, corrected and legacy squeeze, linear-regression momentum, Supertrend, MACD, candle geometry, robust volume and confirmed pivots are already implemented and tested. Support/resistance has no implementation or registry entry.

## Deliverables

- Independent support/resistance event implementation based only on confirmed inputs.
- Explicit event, detection and availability timing.
- Registry metadata, warm-up, parameters, provenance and AI approval decision.
- Numerical, repaint-negative and registry tests.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.

## Acceptance criteria

- The feature cannot use an unconfirmed future pivot.
- Fixtures are deterministic and document tolerance.
- No proprietary indicator code or parity claim is introduced.

## Validation

Run narrow tests first, then all repository workflows required by the changed paths. Validate this task checkpoint before every handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T12:37:00+02:00
head: eb775b38e685223aa80c4b22c4e02e7dee44b642
branch: agent/closure-feature-engine
pr: 780
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-feature-engine.md
  - ai_strategy_engine/src/strategy_engine/features/support_resistance.py
  - ai_strategy_engine/configs/feature_registry.v1.yaml
  - ai_strategy_engine/tests/unit/test_support_resistance.py
  - ai_strategy_engine/tests/integration/test_registry_support_resistance.py
proven:
  - Gate 0 is merged and the workstream is READY with no dependencies or owned-path overlap.
  - The implementation consumes only confirmed PivotEvent inputs and emits one append-only support or resistance confirmation after the configured number of available source pivots.
  - Registry entry support_resistance.v1 is experimental, research-only and explicitly not approved for AI.
  - PR #780 contains only the five owned paths and is zero commits behind develop at implementation head eb775b38e685223aa80c4b22c4e02e7dee44b642.
derived:
  - Immutable anchor matching and one-time emission prevent later pivots from repainting an already emitted level.
  - Explicit event_time, detected_at and available_at are the maxima across the source confirmations, preserving point-in-time availability.
unknown:
  - Exact-head required CI conclusions and workflow run IDs after the checkpoint commit.
  - Unresolved review-thread count after PR review starts.
conflicts: []
first_failure:
  marker: EXACT_HEAD_VALIDATION_PENDING
  evidence: The implementation and focused tests pass locally, but required GitHub workflows have not completed on the checkpoint head.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - Support or resistance may use an unconfirmed future pivot.
  - A newly implemented experimental feature is automatically approved for AI.
  - Repository fixtures may be described as real external acceptance.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-feature-engine.md
  - ai_strategy_engine/src/strategy_engine/features/support_resistance.py
  - ai_strategy_engine/configs/feature_registry.v1.yaml
  - ai_strategy_engine/tests/unit/test_support_resistance.py
  - ai_strategy_engine/tests/integration/test_registry_support_resistance.py
validation:
  - command: python -m compileall -q ai_strategy_engine/src/strategy_engine/features/support_resistance.py
    result: PASS
    evidence: The new module compiles in the isolated Python validation workspace.
  - command: pytest -q ai_strategy_engine/tests/unit/test_support_resistance.py ai_strategy_engine/tests/integration/test_registry_support_resistance.py
    result: PASS
    evidence: 8 deterministic tests passed in the isolated validation workspace.
  - command: compare develop...agent/closure-feature-engine
    result: PASS
    evidence: Branch was zero commits behind develop and changed only four implementation paths before this checkpoint-only update.
blockers:
  - Exact-head required CI and review-thread verification are pending.
next_action: Validate this checkpoint, mark PR #780 ready for review, verify exact-head CI and unresolved review threads, repair only evidenced failures, and merge normally when green.
```
