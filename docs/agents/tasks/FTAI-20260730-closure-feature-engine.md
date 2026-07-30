---
task_id: FTAI-20260730-closure-feature-engine
status: ready
branch: agent/closure-feature-engine
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
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
updated_at: 2026-07-30T10:55:00+02:00
head: 1d347a785eddc900f4484c30e06c3ab4e8851b29
branch: agent/closure-feature-engine
pr: null
status: ready
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
  - ATR, moving averages, BB/KC, corrected and legacy squeeze, linear-regression momentum, Supertrend, MACD, candle geometry, robust volume and confirmed pivots are already implemented and tested. Support/resistance has no implementation or registry entry.
derived:
  - The bounded implementation scope is restricted to 5 exact path entries.
unknown:
  - Exact implementation HEAD, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: PRE_IMPLEMENTATION_GATE
  evidence: Implementation has not started; the Gate 0 dispatch condition is the first enforced gate.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts.
  - Repository fixtures may be described as real external acceptance.
changed_paths: []
validation:
  - command: python tools/agents/checkpoint.py <task-path> --require-checkpoint
    result: PASS
    evidence: Gate 0 validates this compact checkpoint before dispatch.
blockers: []
next_action: Create the branch from current develop, implement support/resistance and its exclusive registry entry, then open one focused PR.
```
