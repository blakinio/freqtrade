---
task_id: FTAI-20260730-closure-ai-routing-ranking
status: active
branch: agent/closure-ai-routing-ranking
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 829
dependencies:
  - FTAI-20260730-closure-contracts merged
  - FTAI-20260730-closure-feature-engine merged
  - FTAI-20260730-closure-research-data merged for liquidation regime
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ai-routing-ranking.md
  - ai_strategy_engine/src/strategy_engine/ai/__init__.py
  - ai_strategy_engine/src/strategy_engine/ai/regime_router.py
  - ai_strategy_engine/src/strategy_engine/ai/ensemble_ranker.py
  - ai_strategy_engine/tests/unit/test_regime_router.py
  - ai_strategy_engine/tests/unit/test_ensemble_ranker.py
  - ai_strategy_engine/tests/integration/test_routing_ranking_evidence.py
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

# Closure AI routing and ranking

## Goal

Implement deterministic Regime Router and Ensemble Ranker research services with no promotion or execution authority.

## Evidence at Gate 0

The roadmap still marks the regime layer planned, and no canonical Regime Router or Ensemble Ranker implementation exists. Candidate generation and constrained optimization are already complete and must be reused.

## Deliverables

- Trend/range, high/low-volatility, liquidation and unknown regime states.
- Drift monitoring that cannot mutate the active model.
- Correlation, OOS stability, drawdown contribution and calibration penalties.
- Immutable explanation and ranking evidence.
- Protected-holdout and no-promotion guards.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.

## Acceptance criteria

- Missing regime inputs fail closed to unknown.
- Ranking is deterministic for the same evidence manifest.
- Authoritative `selected_model = null` is unchanged.
- No score can bypass validation or Risk Core.

## Validation

Run narrow tests first, then all repository workflows required by the changed paths. Validate this task checkpoint before every handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T23:38:25+02:00
head: dcf36b0223b36ccc298d7d50c4708c53bf9346c6
branch: agent/closure-ai-routing-ranking
pr: 829
status: active
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ai-routing-ranking.md
  - ai_strategy_engine/src/strategy_engine/ai/__init__.py
  - ai_strategy_engine/src/strategy_engine/ai/regime_router.py
  - ai_strategy_engine/src/strategy_engine/ai/ensemble_ranker.py
  - ai_strategy_engine/tests/unit/test_regime_router.py
  - ai_strategy_engine/tests/unit/test_ensemble_ranker.py
  - ai_strategy_engine/tests/integration/test_routing_ranking_evidence.py
proven:
  - Shared Contracts PR 781, Feature Engine PR 780 and Research Data PR 821 are merged.
  - Branch was created from develop 0e6de6a2a6e441b4f334103ffff6fd071aa773f8.
  - Open PRs 825, 816 and 758 do not overlap the seven owned paths.
  - Regime routing consumes approved identity-bound features and point-in-time liquidation alignment, with explicit unknown states and immutable explanation hashes.
  - Ensemble ranking exposes OOS profit, correlation, instability, drawdown and calibration components without selection, promotion, Risk Core bypass or execution authority.
  - Focused PR 829 targets develop and changes exactly the seven owned paths.
  - AI Strategy Engine run 30583049517 is green on head b2a8aecd68cbebdf472546ca2da01c42707f570d.
  - GitHub Actions Security Analysis run 30583049726 is green on head b2a8aecd68cbebdf472546ca2da01c42707f570d.
  - Freqtrade CI run 30583049602 has green pre-commit, scope, documentation and Python 3.11, 3.13 and 3.14 jobs; Python 3.12 coverage remained active when develop advanced.
  - develop advanced to 0bc35521debd33312820dfad9f010e22aa651610 via disjoint PR 825 after the previous merge-ref was created.
  - Freqtrade CI job 91006387007 exposed test-protocol covariance, Optional narrowing and formatter-only differences.
  - Commits d9da3c41acc8a701e4666405cbea5d338f56c10c, 218c8bf27d66a07b8f1cd76edbc1b67f00d63352, 68b4059aa3d18182a7404c9dac48ca38aa46dd7e and dcf36b0223b36ccc298d7d50c4708c53bf9346c6 apply the exact type and formatter repairs.
derived:
  - The bounded implementation remains research-only and leaves selected_model null.
unknown:
  - Latest-base merge-ref CI conclusions after develop advanced to 0bc35521debd33312820dfad9f010e22aa651610.
conflicts: []
first_failure:
  marker: AI_STRATEGY_ENGINE_RUFF_DTZ007
  evidence: Run 30582108151 rejected naive datetime parsing; the repaired parser then passed exact-head AI Strategy Engine runs.
rejected_hypotheses:
  - Redefine shared contracts or feature registry entries.
  - Use protected final holdout evidence iteratively.
  - Allow ranking score to mutate or promote an active model.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ai-routing-ranking.md
  - ai_strategy_engine/src/strategy_engine/ai/__init__.py
  - ai_strategy_engine/src/strategy_engine/ai/regime_router.py
  - ai_strategy_engine/src/strategy_engine/ai/ensemble_ranker.py
  - ai_strategy_engine/tests/unit/test_regime_router.py
  - ai_strategy_engine/tests/unit/test_ensemble_ranker.py
  - ai_strategy_engine/tests/integration/test_routing_ranking_evidence.py
validation:
  - command: isolated python -m compileall -q strategy_engine tests
    result: PASS
  - command: isolated pytest -q tests/test_regime_router.py tests/test_ensemble_ranker.py tests/test_routing_ranking_evidence.py
    result: PASS
    evidence: 15 passed after protocol, Optional and formatter repairs
  - command: AI Strategy Engine run 30583049517
    result: PASS
    evidence: all package, Portal, Ruff, mypy, compile, deterministic E2E, schema, materialization and boundary stages succeeded
  - command: GitHub Actions Security Analysis run 30583049726
    result: PASS
  - command: Freqtrade CI run 30583049602
    result: SUPERSEDED
    evidence: all completed jobs were green, but develop advanced before the Python 3.12 coverage job reached a terminal state
  - command: live open-PR and owned-path comparison
    result: PASS
    evidence: PR 829 changes exactly seven owned paths and had zero review threads at last inspection.
blockers: []
next_action: Verify PR 829 latest-base merge-ref CI and resolve the first failing check or review thread.
```
