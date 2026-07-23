---
task_id: FTAI-20260723-portal-operational-read-models
status: active
branch: feat/portal-operational-read-models-20260723
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: null
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
- simulator scenario writes order/position/trade evidence into the normalized read model;
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

1. Simulator evidence persists attributable order, open-position lifecycle and normalized trade records.
2. `/v1/positions`, `/v1/orders`, `/v1/trades`, `/v1/performance`, `/v1/risk-events`, `/v1/audit-events` and `/v1/execution-activity` are tenant scoped.
3. Audit reads require `AUDIT_READ`; general operational reads require an existing read capability and never broaden execution authority.
4. Trade/performance data is derived from persisted evidence rather than fixture-only rows.
5. API mode renders canonical data or truthful empty states; fixture mode remains deterministic test evidence only.
6. Raw execution stdout/stderr and Signal Logs remain explicitly out of scope unless a durable source exists.
7. Required CI passes before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T21:20:00+02:00
head: 26a3f10fa5a2ad964b99448a2b48d3898b6c63b0
branch: feat/portal-operational-read-models-20260723
pr: none
status: active
proven:
  - develop starts from 26a3f10fa5a2ad964b99448a2b48d3898b6c63b0 after merged UI completion and closure PRs #227/#228.
  - open PR #109 is documentation/design-reference only and does not overlap runtime implementation.
  - FreqtradeExecutionAdapter query methods still fail closed with POSITION_QUERY_NOT_IMPLEMENTED, ORDER_QUERY_NOT_IMPLEMENTED and TRADE_QUERY_NOT_IMPLEMENTED.
  - persisted TradeOutcome, RiskDecision and AuditEvent data already provide authoritative sources for bounded trade/performance/risk/audit reads.
  - deterministic simulator creates attributable OrderRecord and TradeOutcome evidence but did not previously persist an execution read model.
unknown:
  - final repository CI result for this task
conflicts: []
blockers: []
next_action: Implement normalized operational read models and wire trusted API/UI reads without changing the private Freqtrade fail-closed boundary.
```
