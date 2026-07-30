---
task_id: FTAI-20260730-closure-ai-routing-ranking
status: blocked
branch: agent/closure-ai-routing-ranking
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
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
updated_at: 2026-07-30T10:55:00+02:00
head: 1d347a785eddc900f4484c30e06c3ab4e8851b29
branch: agent/closure-ai-routing-ranking
pr: null
status: blocked
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
  - The roadmap still marks the regime layer planned, and no canonical Regime Router or Ensemble Ranker implementation exists. Candidate generation and constrained optimization are already complete and must be reused.
derived:
  - The bounded implementation scope is restricted to 7 exact path entries.
unknown:
  - Exact implementation HEAD, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: UPSTREAM_CONTRACT_AND_FEATURE_DEPENDENCY
  evidence: Routing and ranking must consume the frozen typed AST, feature identities and source-aligned liquidation evidence rather than define competing models.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts.
  - Repository fixtures may be described as real external acceptance.
changed_paths: []
validation:
  - command: python tools/agents/checkpoint.py <task-path> --require-checkpoint
    result: PASS
    evidence: Gate 0 validates this compact checkpoint before dispatch.
blockers:
  - Typed strategy and evidence contracts are not frozen yet.
  - Liquidation regime depends on the blocked research-data workstream.
next_action: Wait for the shared contracts and prerequisite feature and research PRs to merge, then create the branch from current develop.
```
