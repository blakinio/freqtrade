---
task_id: FTAI-20260723-portal-operational-read-models
status: ready
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
updated_at: 2026-07-23T23:00:00+02:00
validated_implementation_head: c88909895999610c5d0da8622a7e961a07405c44
branch: feat/portal-operational-read-models-20260723
pr: 229
status: ready
proven:
  - develop base remains 26a3f10fa5a2ad964b99448a2b48d3898b6c63b0 and the branch was behind_by=0 before this documentation-only checkpoint.
  - FreqtradeExecutionAdapter query methods remain fail closed with POSITION_QUERY_NOT_IMPLEMENTED, ORDER_QUERY_NOT_IMPLEMENTED and TRADE_QUERY_NOT_IMPLEMENTED.
  - a tenant-scoped operational mirror now persists normalized order and open-position lifecycle evidence without exposing private Freqtrade endpoints.
  - Trade History and realized Performance are read from persisted attributable TradeOutcome/TradeAnalysis evidence.
  - Risk Events read persisted RiskDecision evidence; Audit Events and Execution Activity require AUDIT_READ and remain tenant scoped.
  - API mode returns canonical records or truthful empty results; fixture rows remain development/E2E-only evidence.
  - raw runtime stdout/stderr and Signal Logs remain explicit future read-model gaps.
  - AI Platform CI 30043229611 passed on validated implementation head c88909895999610c5d0da8622a7e961a07405c44.
  - Portal Web CI 30043229614 passed on validated implementation head c88909895999610c5d0da8622a7e961a07405c44.
  - Portal Universal E2E 30043229670 passed on validated implementation head c88909895999610c5d0da8622a7e961a07405c44.
  - Freqtrade CI 30043229604 passed on validated implementation head c88909895999610c5d0da8622a7e961a07405c44.
  - zizmor security analysis 30043229472 passed on validated implementation head c88909895999610c5d0da8622a7e961a07405c44.
unknown: []
conflicts: []
blockers: []
next_action: Complete final documentation-only CI for this checkpoint, then mark PR #229 ready for human review and merge.
```
