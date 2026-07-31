---
task_id: FTAI-20260730-closure-ai-routing-ranking
status: completed
branch: agent/closure-ai-routing-ranking-terminal
base_branch: develop
created: 2026-07-30
updated: 2026-07-31
related_pr: 829
terminal_pr: 868
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

## Terminal result

- PR #829 merged normally into `develop` as `11f5924a2c8bed093fa1486c8df05df081121443`.
- OI and funding alignment preserves source identity, schema/data version and event, receive and availability timestamps.
- Regime routing consumes approved identity-bound features and point-in-time liquidation alignment, with explicit trend/range, high/low-volatility, stressed/normal liquidation and stable/drifted/unknown states.
- Missing, delayed, stale, ambiguous or identity-incompatible evidence fails closed to unknown or ineligible output.
- Ensemble ranking is deterministic and uses explicit OOS profit, correlation, instability, drawdown and calibration components from immutable validated evidence.
- Versioned manifest, policy, explanation and ranking hashes bind feature-registry, configuration, data and routing identities.
- `selected_model = null`, frozen thresholds `0.006/-0.009`, protected holdout `20260801-20260930`, Risk Core authority and active-model immutability remain unchanged.
- No promotion, execution authorization, order submission, exchange credential or live-capital path was introduced.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T15:25:04+02:00
head: 11f5924a2c8bed093fa1486c8df05df081121443
branch: agent/closure-ai-routing-ranking-terminal
pr: 829
status: ready
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
  - Shared Contracts PR 781, Feature Engine PR 780 and Research Data PR 821 were merged before implementation.
  - PR 829 changed exactly the seven declared owned paths and merged from exact final head 461c1d0c0b30fbda1523e7cf806720e878c9eb5b.
  - Regime routing consumes approved feature-registry identities and point-in-time liquidation alignment without future-data access.
  - Missing, delayed, stale, ambiguous and incompatible inputs fail closed to explicit unknown states with deterministic reason codes.
  - Ranking exposes OOS profit, correlation, instability, drawdown and calibration components without selecting or promoting a model.
  - Manifest, policy, explanation and ranking evidence use deterministic versioned hashes bound to feature, configuration, data and routing identities.
  - Protected holdout 20260801-20260930 is rejected and frozen thresholds 0.006/-0.009 are unchanged.
  - selected_model remains null; promotion_authorized, execution_authorized, risk_core_bypassed and active_model_mutated remain false.
  - AI Strategy Engine run 30633414223, Freqtrade CI run 30633414236 and security run 30633414280 passed on exact final head.
  - PR 829 merged as 11f5924a2c8bed093fa1486c8df05df081121443 with zero unresolved review threads.
derived:
  - All assigned AI routing and ranking gaps are complete within research-only paper, shadow and dry-run authority.
  - Integration/E2E can consume the merged deterministic routing and ranking evidence contracts.
unknown: []
conflicts: []
first_failure:
  marker: AI_STRATEGY_ENGINE_RUFF_DTZ007
  evidence: Initial validation rejected naive datetime parsing; timezone-safe date parsing plus protocol, Optional and formatter repairs passed exact-head CI.
rejected_hypotheses:
  - Redefine shared contracts or feature-registry entries.
  - Use protected final holdout evidence iteratively.
  - Allow ranking score to mutate, select or promote an active model.
  - Add Risk Core bypass, order submission or live-capital authority.
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
  - command: isolated focused routing and ranking pytest suite
    result: PASS
    evidence: 15 deterministic tests passed.
  - command: AI Strategy Engine run 30633414223
    result: PASS
    evidence: Package tests, Portal research tests, Ruff, mypy, compile, deterministic E2E, schema, materialization and boundary scans passed.
  - command: Freqtrade CI run 30633414236
    result: PASS
    evidence: Pre-commit, scope, documentation, Python 3.11 through 3.14, full 3.12 coverage, distributions and CI Gate passed.
  - command: GitHub Actions Security Analysis run 30633414280
    result: PASS
    evidence: Exact final head passed workflow security analysis.
  - command: PR 829 merge and review audit
    result: PASS
    evidence: Squash merge 11f5924a2c8bed093fa1486c8df05df081121443 changed exactly seven owned paths and had zero unresolved review threads.
blockers: []
next_action: Closure coordinator consumes merge 11f5924a2c8bed093fa1486c8df05df081121443 to mark AI routing and ranking complete and release Integration/E2E.
```
