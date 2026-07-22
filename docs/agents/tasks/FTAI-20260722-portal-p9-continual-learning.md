---
task_id: FTAI-20260722-portal-p9-continual-learning
status: active
branch: feat/portal-p9-learning-loop
base_branch: feat/portal-p8-trade-intelligence
created: 2026-07-22
updated: 2026-07-22
related_pr: null
owned_paths:
  - ai_platform/portal/learning/
  - tests/ai_platform/portal/learning/
  - docs/ai_platform/portal/CONTINUAL_LEARNING_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p9-continual-learning.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/TRADE_INTELLIGENCE_FOUNDATION.md
search_first:
  - current P8 merge state and open PRs/tasks overlapping learning ownership
  - protected final holdout declaration and frozen research boundaries
  - P5 model-control semantics proving candidate registration is not promotion
optional_reads:
  - model lifecycle implementation only if a concrete candidate-registration blocker requires it
---

# AI Trading Portal P9 — Safe Continual Learning

## Goal

Turn durable P8 insights into reproducible hypothesis/experiment/candidate history while preventing iterative protected-holdout use and any automatic model promotion or bot assignment.

## Acceptance criteria

1. Every hypothesis pins one source TradeInsight and durable evidence links.
2. Every experiment declares an explicit evidence window and autonomy level.
3. Iterative evidence windows overlapping final holdout v2 `20260801-20260930` are rejected.
4. Negative and inconclusive experiments remain durable.
5. Only positive experiments may register candidate metadata.
6. Candidate records remain `promoted=false` and `assigned_to_bot=false`.
7. Candidate creation does not call P5 promotion/rollback or mutate BotConfigRevision.
8. Tenant provenance is fail-closed.
9. Targeted tests and required repository CI pass before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T23:35:00+02:00
head: 4b94be27db8a022597432c2ffeb791b1f615811e
branch: feat/portal-p9-learning-loop
pr: none
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/TRADE_INTELLIGENCE_FOUNDATION.md
proven:
  - P9 is stacked on the bounded P8 trade-intelligence branch so source TradeInsight provenance is explicit.
  - LearningHypothesis pins source insight and evidence links.
  - LearningExperiment pins evidence window, autonomy level, durable outcome and result summary.
  - LearningCandidate pins source experiment, model family/version, dataset and feature-schema identities and is always created unpromoted/unassigned.
  - Protected final holdout v2 is represented as 2026-08-01T00:00:00Z through 2026-10-01T00:00:00Z exclusive-end and overlapping iterative windows are rejected.
  - Negative experiment history remains durable and cannot produce a candidate.
derived:
  - P10 can exercise the full insight-to-candidate workflow without changing the active model assignment.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: P9 executable CI has not run yet.
changed_paths:
  - ai_platform/portal/learning/__init__.py
  - ai_platform/portal/learning/database.py
  - ai_platform/portal/learning/migrations/0001_learning_loop.sql
  - ai_platform/portal/learning/models.py
  - ai_platform/portal/learning/repository.py
  - ai_platform/portal/learning/schema.py
  - ai_platform/portal/learning/service.py
  - tests/ai_platform/portal/learning/test_learning_migration.py
  - tests/ai_platform/portal/learning/test_learning_service.py
  - docs/ai_platform/portal/CONTINUAL_LEARNING_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p9-continual-learning.md
validation: []
blockers:
  - P9 merge must wait for P8 because this branch is intentionally stacked on P8 trade-intelligence schemas.
next_action: Open a stacked PR against the P8 feature branch, validate P9 independently, then retarget/synchronize to develop after P8 merges and merge P9 before starting the final P10 simulator/E2E task.
```
