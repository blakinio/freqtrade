---
task_id: FTAI-20260722-portal-p9-continual-learning
status: done
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

# AI Trading Portal P9.1 — Safe Continual Learning Backend Foundation

## Goal

Turn durable P8 insights into reproducible hypothesis/experiment/candidate history while preventing iterative protected-holdout use and any automatic model promotion or bot assignment.

This historical task completed the **P9 backend foundation** merged in PR #158. The canonical P9 roadmap stage additionally declared `Learning History UI`; that presentation/read-only integration is completed separately by `FTAI-20260723-portal-ui-completion`.

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

## Stage-completion clarification

PR #158 merged the bounded learning backend foundation as `41857e7d4eb9ce72f74ca99941fff6e292308569`. The PR contained no portal web files, so it did not by itself deliver the roadmap-declared Learning History product surface.

The later UI completion task adds an aggregate tenant-scoped history read path and read-only portal UI. Candidate creation still never implies promotion or assignment.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T20:20:00+02:00
head: 41857e7d4eb9ce72f74ca99941fff6e292308569
branch: develop
pr: "#158"
status: done
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/TRADE_INTELLIGENCE_FOUNDATION.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
proven:
  - P8 trade intelligence was merged before P9 and provides durable TradeInsight provenance inputs.
  - LearningHypothesis pins source insight and evidence links.
  - LearningExperiment pins evidence window, autonomy level, durable outcome and result summary.
  - LearningCandidate pins source experiment, model family/version, dataset and feature-schema identities and is always created unpromoted/unassigned.
  - Iterative evidence windows overlapping protected final holdout v2 are rejected.
  - Negative experiment history remains durable and cannot produce a candidate.
  - PR #158 merged the bounded P9 backend foundation as 41857e7d4eb9ce72f74ca99941fff6e292308569.
  - PR #158 did not deliver the roadmap-declared Learning History UI.
derived:
  - Backend-foundation completion and full P9 product-stage completion must be tracked separately.
unknown: []
conflicts: []
first_failure:
  marker: historical-task-state-stale
  evidence: The task record remained active after PR #158 merged and did not distinguish backend foundation from missing UI delivery.
validation:
  - command: PR #158 merge state
    result: PASS
    evidence: PR #158 is merged; merge commit 41857e7d4eb9ce72f74ca99941fff6e292308569
blockers: []
next_action: Complete and validate the P9 Learning History presentation/read-only integration only through FTAI-20260723-portal-ui-completion without enabling automatic promotion, assignment or protected-holdout use.
```
