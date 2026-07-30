---
task_id: FTAI-20260730-closure-feature-engine
status: ready
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
  - tests/ai_platform/portal/feature_registry/test_feature_registry.py
  - tests/ai_platform_integration/test_ase_fr_01_feature_registry_e2e.py
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
updated_at: 2026-07-30T17:20:00+02:00
head: de2c2481840284b81b48b4c4d217d91336aadd26
branch: agent/closure-feature-engine
pr: 780
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
  - tests/ai_platform/portal/feature_registry/test_feature_registry.py
  - tests/ai_platform_integration/test_ase_fr_01_feature_registry_e2e.py
proven:
  - The implementation consumes only confirmed PivotEvent inputs and emits append-only support or resistance confirmations with explicit timing.
  - Registry entry support_resistance.v1 is experimental, research-only and explicitly not approved for AI.
  - Numerical, timing, repaint-negative, future-pivot and registry tests pass.
  - Portal and integration tests derive registry counts dynamically and explicitly verify support_resistance.v1.
  - Exact implementation head de2c2481840284b81b48b4c4d217d91336aadd26 passed all required CI.
  - PR #780 has zero unresolved review threads.
derived:
  - Immutable anchor matching and one-time emission prevent later pivots from repainting an emitted level.
  - Dynamic count assertions preserve deterministic replay validation without coupling tests to each append-only registry addition.
unknown: []
conflicts: []
first_failure:
  marker: PORTAL_FEATURE_COUNT_ASSERTION_OUTSIDE_ORIGINAL_OWNERSHIP
  evidence: Earlier runs exposed three stale assertions fixed by the bounded owner-directed repair.
rejected_hypotheses:
  - Support or resistance may use an unconfirmed future pivot.
  - An experimental feature is automatically approved for AI.
  - An existing registered feature may be removed to preserve a stale count.
  - Portal tests should hardcode the total size of an append-only registry.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-feature-engine.md
  - ai_strategy_engine/src/strategy_engine/features/support_resistance.py
  - ai_strategy_engine/configs/feature_registry.v1.yaml
  - ai_strategy_engine/tests/unit/test_support_resistance.py
  - ai_strategy_engine/tests/integration/test_registry_support_resistance.py
  - tests/ai_platform/portal/feature_registry/test_feature_registry.py
  - tests/ai_platform_integration/test_ase_fr_01_feature_registry_e2e.py
validation:
  - command: python -m compileall -q ai_strategy_engine/src/strategy_engine/features/support_resistance.py
    result: PASS
    evidence: The new module compiles in the isolated validation workspace.
  - command: pytest -q ai_strategy_engine/tests/unit/test_support_resistance.py ai_strategy_engine/tests/integration/test_registry_support_resistance.py
    result: PASS
    evidence: 8 deterministic targeted tests passed.
  - command: GitHub AI Platform CI run 30554634298
    result: PASS
    evidence: Tests, Ruff, Ruff format and repository validations passed.
  - command: GitHub AI Strategy Engine run 30554634244
    result: PASS
    evidence: Package, Portal research, Ruff, mypy, compile, deterministic E2E and safety validations passed.
  - command: GitHub Freqtrade CI run 30554634234
    result: PASS
    evidence: Pre-commit, documentation, Python 3.11-3.14 core tests, coverage, distributions and CI Gate passed.
  - command: GitHub security run 30554634227
    result: PASS
    evidence: Workflow security analysis passed.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-closure-feature-engine.md --require-checkpoint
    result: PASS
    evidence: The terminal checkpoint satisfies the shared governance contract and compactness limits.
blockers: []
next_action: Mark PR #780 ready and merge normally with the expected final head after the task-only exact-head checks pass.
```
