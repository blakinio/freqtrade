---
task_id: FTAI-20260723-portal-operational-read-models
status: done
branch: feat/portal-operational-read-models-20260723
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "#229"
owned_paths:
  - ai_platform/portal/operations/
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/intelligence/repository.py
  - ai_platform/portal/intelligence/service.py
  - ai_platform/portal/simulator/runner.py
  - ai_platform/portal/web/
  - tests/ai_platform/portal/
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/agents/tasks/FTAI-20260723-portal-operational-read-models.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
search_first:
  - current develop and open PRs overlapping portal operational read models
  - existing authoritative trade outcome, risk decision, audit and simulator evidence
---

# AI Trading Portal — Operational Read Models

## Goal

Close the remaining bounded operational UI read-model gaps that can be backed by authoritative existing portal data, without implementing live order submission, exposing private Freqtrade endpoints, or fabricating runtime records.

## Deliverables

- tenant-scoped normalized execution read model for simulator/private-adapter evidence;
- Orders and Open Positions read APIs backed by the normalized read model;
- Trade History and realized Performance read APIs derived from persisted TradeOutcome evidence;
- Risk Events read API from persisted deterministic risk decisions;
- Audit Events read API from persisted audit events with `AUDIT_READ` authorization;
- Execution activity read API from attributable audit events, explicitly distinct from raw container stdout;
- simulator scenario writes order/open-position lifecycle evidence into the normalized read model while persisted TradeOutcome remains the canonical completed-trade source;
- portal UI consumes the new APIs in API mode and keeps empty states honest;
- update UI delivery matrix to distinguish integrated operational evidence from remaining raw-log/signal/drift gaps;
- browser and backend tests.

## Non-negotiable boundaries

- no direct browser-to-Freqtrade or browser-to-exchange path;
- no live-capital authorization or order-submission implementation;
- `FreqtradeExecutionAdapter.get_open_positions/get_orders/get_trades` remain fail-closed until separately integrated with private runtime transport;
- no exchange secrets, runtime credentials or private addresses in public contracts;
- no fabricated API-mode data;
- tenant scope and server-side authorization are mandatory;
- protected final holdout and model-promotion boundaries remain unchanged.

## Acceptance criteria

1. Simulator evidence persists attributable order/open-position lifecycle evidence and completed trades remain attributable through persisted TradeOutcome/TradeAnalysis evidence.
2. `/v1/positions`, `/v1/orders`, `/v1/trades`, `/v1/performance`, `/v1/risk-events`, `/v1/audit-events` and `/v1/execution-activity` are tenant scoped.
3. Audit reads require `AUDIT_READ`; general operational reads require an existing read capability and never broaden execution authority.
4. Trade/performance data is derived from persisted evidence rather than fixture-only rows.
5. API mode renders canonical data or truthful empty states; fixture mode remains deterministic test evidence only.
6. Raw execution stdout/stderr and Signal Logs remain explicitly out of scope unless a durable source exists.
7. Required CI passes before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T23:20:00+02:00
head: cc41e2a61439abf94a4dee2733c3d1e09005b448
branch: develop
pr: "#229"
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
owned_paths:
  - ai_platform/portal/operations/
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/intelligence/repository.py
  - ai_platform/portal/intelligence/service.py
  - ai_platform/portal/simulator/runner.py
  - ai_platform/portal/web/
  - tests/ai_platform/portal/
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/agents/tasks/FTAI-20260723-portal-operational-read-models.md
proven:
  - PR #229 was squash-merged to develop as cc41e2a61439abf94a4dee2733c3d1e09005b448.
  - The final PR branch was behind_by=0 against develop before merge.
  - The tenant-scoped operational mirror persists normalized order and open-position lifecycle evidence without exposing private Freqtrade endpoints.
  - Trade History and realized Performance are derived from persisted attributable TradeOutcome and TradeAnalysis evidence.
  - Risk Events read persisted RiskDecision evidence; Audit Events and Execution Activity require AUDIT_READ and remain tenant scoped.
  - API mode returns canonical records or truthful empty results; fixture rows remain development and E2E-only evidence.
  - FreqtradeExecutionAdapter position, order and trade query methods remain deliberately fail-closed.
  - Raw runtime stdout and stderr plus Signal Logs remain explicit future read-model gaps.
  - Final checkpoint-only AI Platform CI, Portal Web CI, Portal Universal E2E, Freqtrade CI and zizmor all passed on head 9b96d3b3af4417947bf66d99d8afb0771526ac1f.
derived:
  - The bounded operational read-model task is complete without broadening execution authority or live-capital capability.
  - Remaining UI gaps require separate authoritative data sources or separately reviewed integration work and are not part of this completed task.
unknown: []
conflicts: []
first_failure:
  marker: no-final-blocking-failure
  evidence: The final documentation-only checkpoint completed all required CI successfully; no unresolved blocking failure remained at merge.
rejected_hypotheses:
  - Treat fixture-only rows as canonical API-mode operational evidence.
  - Expose Freqtrade query endpoints directly to the browser to fill portal read-model gaps.
  - Implement live order submission or live-capital authorization as part of this read-only task.
changed_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/operations/__init__.py
  - ai_platform/portal/operations/migrations/0001_operational_read_models.sql
  - ai_platform/portal/operations/models.py
  - ai_platform/portal/operations/repository.py
  - ai_platform/portal/operations/schema.py
  - ai_platform/portal/operations/service.py
  - ai_platform/portal/simulator/runner.py
  - ai_platform/portal/web/app/operations/audit/page.tsx
  - ai_platform/portal/web/app/operations/execution-logs/page.tsx
  - ai_platform/portal/web/app/operations/risk-events/page.tsx
  - ai_platform/portal/web/app/orders/page.tsx
  - ai_platform/portal/web/app/performance/page.tsx
  - ai_platform/portal/web/app/positions/page.tsx
  - ai_platform/portal/web/app/trades/page.tsx
  - ai_platform/portal/web/e2e/shell.spec.ts
  - ai_platform/portal/web/lib/contracts.ts
  - ai_platform/portal/web/lib/fixtures.ts
  - ai_platform/portal/web/lib/portal-api.ts
  - docs/agents/tasks/FTAI-20260723-portal-operational-read-models.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/operations/test_operational_read_models.py
  - tests/ai_platform/portal/simulator/test_universal_scenario.py
validation:
  - command: AI Platform CI 30044473807
    result: PASS
    evidence: Final checkpoint-only AI Platform validation passed on PR #229 head 9b96d3b3af4417947bf66d99d8afb0771526ac1f.
  - command: Portal Web CI 30044473863
    result: PASS
    evidence: Final checkpoint-only portal web validation passed on PR #229 head 9b96d3b3af4417947bf66d99d8afb0771526ac1f.
  - command: Portal Universal E2E 30044473652
    result: PASS
    evidence: Final checkpoint-only universal portal E2E passed on PR #229 head 9b96d3b3af4417947bf66d99d8afb0771526ac1f.
  - command: Freqtrade CI 30044473716
    result: PASS
    evidence: Final checkpoint-only pre-commit, docs and required Freqtrade matrix passed on PR #229 head 9b96d3b3af4417947bf66d99d8afb0771526ac1f.
  - command: zizmor 30044473661
    result: PASS
    evidence: Final checkpoint-only GitHub Actions security analysis passed on PR #229 head 9b96d3b3af4417947bf66d99d8afb0771526ac1f.
blockers: []
next_action: Do not reopen this completed task; declare a separate bounded task only when implementing a remaining authoritative read-model gap, while program-level P11 stays deferred until the owner starts the real infrastructure phase.
```
