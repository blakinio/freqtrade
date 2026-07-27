---
task_id: FTAI-20260727-portal-bm06-exchange-connection-product
status: active
branch: feat/portal-bm06-exchange-connection-product
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
owned_paths:
  - ai_platform/portal/exchange_connections/**
  - tests/ai_platform/portal/exchange_connections/**
  - docs/agents/tasks/FTAI-20260727-portal-bm06-exchange-connection-product.md
---

# BM-06 — Exchange connection product

## Goal

Implement the secret-free exchange-connection product domain over the merged BM-00 contracts: account/subaccount metadata, capability profiles, supported markets/symbols/precision/functions, verification lifecycle, trading and withdrawal permission status, degraded credential states and a narrow opaque-reference seam for later PI-07.

## Entry gate

- PR #440 is merged into `develop` as `5e960d45ba29c494a517937a4b7e0838ae9737db`.
- BM-00 head `632fe1efe465a79c2c13ddd9656c01c530a8b735` passed AI Platform CI run 1935, Freqtrade CI run 2369 and GitHub Actions Security Analysis run 2232.
- The BM-00 merge commit is an ancestor of the current `develop` used for this branch.
- No open PR or active discovered task owns `ai_platform/portal/exchange_connections/**`.

## Dependencies

- merged BM-00 exchange capability, metadata and verification contracts;
- `SECURITY_ARCHITECTURE.md` credential and tenant boundaries;
- `BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md` section 4.9;
- `BOT_MANAGEMENT_AGENT_PLAN.md` BM-06 ownership and wave-1 rules.

## Scope

- feature-local schemas, repository, service and verification state machine;
- opaque credential-reference status interface for later PI-07;
- account/subaccount compatibility validation;
- exchange market, symbol, precision, order-type and function capabilities;
- tenant-scoped connection metadata and product states;
- pending, verified, failed and stale verification transitions;
- unavailable, revoked and rotation-required product states;
- explicit trading permission and expected/confirmed/rejected withdrawal status;
- focused tests for secret exclusion, tenant isolation, invalid capabilities, stale verification and withdrawal-enabled rejection.

## Non-goals

- no secret-provider selection or implementation;
- no API key, secret, passphrase, token, private endpoint or resolved secret-store path storage/retrieval;
- no private exchange trading endpoint calls;
- no shared API registration, BFF, migrations or infrastructure changes;
- no PI-07, PI-08, live-capital or withdrawal enablement.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T15:42:09+02:00
head: 59775a93fb606ac5bf25796f3f43ef912928bade
branch: feat/portal-bm06-exchange-connection-product
pr: null
status: active
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - ai_platform/portal/contracts/bot_management/exchange_connections.py
  - ai_platform/portal/web/app/platform/exchanges/page.tsx
owned_paths:
  - ai_platform/portal/exchange_connections/**
  - tests/ai_platform/portal/exchange_connections/**
  - docs/agents/tasks/FTAI-20260727-portal-bm06-exchange-connection-product.md
proven:
  - BM-00 is merged and its required workflows are green.
  - Current Exchange Connections UI renders only opaque references derived from bot configurations.
  - BM-00 forbids withdrawal-enabled permission observations and secret-bearing contract fields.
derived:
  - BM-06 can implement a secret-free feature-local product and leave provider resolution to PI-07.
  - No migration or shared API composition is authorized in this task.
unknown: []
conflicts: []
first_failure: null
rejected_hypotheses:
  - Select or implement a secret provider in BM-06.
  - Fetch real credentials or call private trading endpoints.
  - Modify shared API, migration, BFF or infrastructure paths.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-portal-bm06-exchange-connection-product.md
validation:
  - command: isolated pytest for proposed BM-06 module
    result: PASS
    evidence: 5 focused tests passed against copied merged BM-00 dependencies.
  - command: python -m compileall ai_platform/portal/exchange_connections
    result: PASS
    evidence: Proposed module compiled in the isolated validation workspace.
blockers: []
next_action: Commit the feature-local BM-06 module and focused tests, then open its dedicated PR against current develop.
```
