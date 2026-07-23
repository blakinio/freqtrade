---
task_id: FTAI-20260722-portal-p9-continual-learning
status: active
branch: feat/portal-p9-learning-loop-clean
base_branch: develop
created: 2026-07-22
updated: 2026-07-23
related_pr: "#158"
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
updated_at: 2026-07-23T09:48:00+02:00
head: cb272ae7bc86f1687cb728f4af436693c240cb9a
branch: feat/portal-p9-learning-loop-clean
pr: 158
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/TRADE_INTELLIGENCE_FOUNDATION.md
proven:
  - P8 trade intelligence is merged to develop as 0c0a9e28598f60d61bf4e75bbd4d5c8bba8dc456.
  - LearningHypothesis pins source insight and evidence links.
  - LearningExperiment pins evidence window, autonomy level, durable outcome and result summary.
  - LearningCandidate pins source experiment, model family/version, dataset and feature-schema identities and is always created unpromoted/unassigned.
  - Protected final holdout v2 is represented as 2026-08-01T00:00:00Z through 2026-10-01T00:00:00Z exclusive-end and overlapping iterative windows are rejected.
  - Negative experiment history remains durable and cannot produce a candidate.
  - Clean P9 PR #158 contains only the 11 declared P9-owned files after replacing obsolete stacked PR #149.
  - Clean P9 implementation head 5f911b8185c10bcf8eb97e3aaade8c37756142e4 passed AI Platform CI 29962706629, Freqtrade CI 29962706531 and zizmor 29962706515.
  - Sync PR #165 merged current develop into the P9 branch as cb272ae7bc86f1687cb728f4af436693c240cb9a; compare now reports behind_by=0 and only P9-owned files differ from develop.
derived:
  - P10 can consume P9 candidate provenance without changing active model assignment.
  - The final checkpoint-only head must pass required merge-state CI before P9 squash-merge.
unknown: []
conflicts: []
first_failure:
  marker: stacked-squash-history
  evidence: Original stacked P9 PR #149 included already-merged P8 files after P8 squash-merge; P9 was recreated from clean develop with only P9-owned paths.
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
validation:
  - command: AI Platform CI 29962706629
    result: PASS
  - command: Freqtrade CI 29962706531
    result: PASS
  - command: GitHub Actions Security Analysis with zizmor 29962706515
    result: PASS
  - command: compare develop...feat/portal-p9-learning-loop-clean after sync PR #165
    result: PASS
    evidence: behind_by=0; diff remains limited to 11 P9-owned files.
blockers: []
next_action: Verify required CI on this checkpoint-only synchronized P9 head, squash-merge PR #158 when green, then retarget and validate clean P10 PR #159 against merged develop.
```
