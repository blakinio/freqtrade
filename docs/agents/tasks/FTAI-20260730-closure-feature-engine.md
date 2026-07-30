---
task_id: FTAI-20260730-closure-feature-engine
status: blocked
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
updated_at: 2026-07-30T12:42:00+02:00
head: e1f8248a6fca02cd9798e25ed6889b4a674c9915
branch: agent/closure-feature-engine
pr: 780
status: blocked
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
  - Gate 0 is merged and the workstream is READY with no implementation dependency or owned-path overlap.
  - The implementation consumes only confirmed PivotEvent inputs and emits one append-only support or resistance confirmation after the configured source pivots become available.
  - Registry entry support_resistance.v1 is experimental, research-only and explicitly not approved for AI.
  - PR #780 contains exactly the five owned paths.
  - Exact-head AI Strategy Engine run 30535356595 passed package tests before failing in two existing Portal registry count assertions.
derived:
  - Immutable anchor matching and one-time emission prevent later pivots from repainting an emitted level.
  - The Portal assertions expecting 21 features are stale after the required append-only 22nd registry entry.
unknown:
  - Final exact-head Freqtrade CI conclusion after resolution of the ownership blocker.
  - Unresolved review-thread count after implementation review.
conflicts:
  - Required update is in tests/ai_platform/portal/feature_registry/test_feature_registry.py, outside this task's exact owned paths.
first_failure:
  marker: PORTAL_FEATURE_COUNT_ASSERTION_OUTSIDE_OWNERSHIP
  evidence: AI Strategy Engine run 30535356595 failed only because feature_count and replay range are hardcoded to 21 while the required registry now contains 22 entries.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - Support or resistance may use an unconfirmed future pivot.
  - An experimental feature is automatically approved for AI.
  - An existing registered feature may be removed to preserve a stale count.
  - The worker may silently edit a path not assigned in the Gate 0 matrix.
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
  - command: GitHub AI Strategy Engine run 30535356595 on e1f8248a6fca02cd9798e25ed6889b4a674c9915
    result: FAIL
    evidence: Package tests passed; Portal research tests failed at two hardcoded feature-count assertions expecting 21 instead of 22.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-closure-feature-engine.md --require-checkpoint
    result: PASS
    evidence: The checkpoint satisfies required fields, evidence separation, status and compactness limits.
blockers:
  - Explicit ownership transfer or a coordinator-owned repair is required for tests/ai_platform/portal/feature_registry/test_feature_registry.py.
next_action: Agent 0 must assign a bounded update of the stale Portal registry count assertions; then this branch can integrate that authorized repair, rerun exact-head CI and continue normal review and merge.
```
