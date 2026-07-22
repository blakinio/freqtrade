---
task_id: FTAI-20260722-portal-p8-trade-intelligence
status: active
branch: feat/portal-p8-trade-intelligence
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
owned_paths:
  - ai_platform/portal/intelligence/
  - tests/ai_platform/portal/intelligence/
  - docs/ai_platform/portal/TRADE_INTELLIGENCE_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p8-trade-intelligence.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
search_first:
  - current develop and open PRs or active tasks overlapping intelligence ownership
  - existing decision snapshot, trade mirror and execution evidence semantics
optional_reads:
  - AI synthesis implementation details only if a concrete integration blocker requires them
---

# AI Trading Portal P8 — Trade Intelligence

## Goal

Create durable decision-time evidence and deterministic post-trade diagnosis that may produce AI-assisted insight without overclaiming causality or affecting execution.

## Acceptance criteria

1. DecisionSnapshot and TradeOutcome remain separate immutable evidence records.
2. Every analysis pins exact config/strategy/model/risk/runtime evidence through the snapshot.
3. Losing trades are not automatically classified as model errors.
4. Incomplete reconciliation produces DATA_GAP rather than speculative diagnosis.
5. Optional AI synthesis cannot overwrite deterministic diagnosis and failure falls back safely.
6. Tenant and bot/pair/runtime attribution are fail-closed.
7. Analysis code has no execution submission path and cannot mutate active bot/model configuration.
8. Targeted tests and required repository CI pass before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T23:20:00+02:00
head: 1ad8e34cb55503d69a469b33dbfa52e168c7440e
branch: feat/portal-p8-trade-intelligence
pr: none
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
proven:
  - P4 event/observability foundations are already merged and provide correlation semantics without owning trade intelligence business logic.
  - P8 DecisionSnapshot stores only decision-time identity/evidence reference and hash; outcome data is persisted separately.
  - Deterministic diagnosis distinguishes PROFITABLE, LOSS_WITHIN_EXPECTED_RISK, LOSS_REQUIRES_REVIEW and DATA_GAP.
  - Optional synthesis is append-only narrative and exceptions fall back to deterministic analysis.
derived:
  - P9 can consume durable TradeInsight records as provenance inputs without changing active models.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: P8 executable CI has not run yet.
changed_paths:
  - ai_platform/portal/intelligence/__init__.py
  - ai_platform/portal/intelligence/database.py
  - ai_platform/portal/intelligence/migrations/0001_trade_intelligence.sql
  - ai_platform/portal/intelligence/models.py
  - ai_platform/portal/intelligence/repository.py
  - ai_platform/portal/intelligence/schema.py
  - ai_platform/portal/intelligence/service.py
  - tests/ai_platform/portal/intelligence/test_trade_intelligence_migration.py
  - tests/ai_platform/portal/intelligence/test_trade_intelligence_service.py
  - docs/ai_platform/portal/TRADE_INTELLIGENCE_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p8-trade-intelligence.md
validation: []
blockers: []
next_action: Open the bounded P8 trade intelligence PR, use repository CI as the executable gate, fix only concrete failures, then merge when green before starting P9 learning-loop implementation.
```
