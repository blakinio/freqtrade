---
task_id: FTAI-20260730-closure-feature-engine
status: in_progress
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
updated_at: 2026-07-30T16:52:00+02:00
head: 2c729d5309357a88726e0cc676568e440bbd6737
branch: agent/closure-feature-engine
pr: 780
status: in_progress
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
  - Gate 0 is merged and the workstream is READY with no implementation dependency or original owned-path overlap.
  - The implementation consumes only confirmed PivotEvent inputs and emits one append-only support or resistance confirmation after the configured source pivots become available.
  - Registry entry support_resistance.v1 is experimental, research-only and explicitly not approved for AI.
  - The prior exact-head failures were limited to three stale assertions that hardcoded the registry size as 21.
  - The bounded repair now derives counts from returned feature collections and explicitly verifies support_resistance.v1 is present.
derived:
  - Immutable anchor matching and one-time emission prevent later pivots from repainting an emitted level.
  - Dynamic count assertions preserve deterministic replay checks without coupling Portal tests to every append-only registry addition.
unknown:
  - Exact-head AI Strategy Engine and Freqtrade CI conclusions after the bounded repair.
  - Unresolved review-thread count after implementation review.
conflicts: []
first_failure:
  marker: PORTAL_FEATURE_COUNT_ASSERTION_OUTSIDE_ORIGINAL_OWNERSHIP
  evidence: Runs 30535356595 and 30535547703 exposed stale count assertions; the owner directed completion of this task and the bounded repair is now included.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
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
    evidence: The new module compiles in the isolated Python validation workspace.
  - command: pytest -q ai_strategy_engine/tests/unit/test_support_resistance.py ai_strategy_engine/tests/integration/test_registry_support_resistance.py
    result: PASS
    evidence: 8 deterministic tests passed in the isolated validation workspace.
  - command: GitHub AI Strategy Engine run 30535547703 on 886722a7b65f49ce75d1e905baa1d5ad3f2c800f
    result: FAIL
    evidence: Package tests passed; Portal research tests failed only at stale feature-count assertions expecting 21 instead of 22.
  - command: GitHub Freqtrade CI run 30535547695 on 886722a7b65f49ce75d1e905baa1d5ad3f2c800f
    result: FAIL
    evidence: 5817 tests passed and only three stale feature-count assertions failed across Portal and integration layers.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-closure-feature-engine.md --require-checkpoint
    result: PENDING
    evidence: Must be rerun on the repaired exact head.
blockers: []
next_action: Run required exact-head CI, resolve any evidenced review or validation failure, then mark PR ready and merge normally.
```
