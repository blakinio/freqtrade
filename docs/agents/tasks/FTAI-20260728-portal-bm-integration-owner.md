---
task_id: FTAI-20260728-portal-bm-integration-owner
status: active
branch: feat/portal-bm-integration-owner-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
owned_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/bot_catalog/router.py
  - ai_platform/portal/bot_builder/router.py
  - ai_platform/portal/bot_operations/router.py
  - ai_platform/portal/signal_control/router.py
  - ai_platform/portal/grid_control/router.py
  - ai_platform/portal/exchange_connections/router.py
  - tests/ai_platform/portal/control_plane/test_bot_management_api.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bm-integration-owner.md
---

# Bot-management integration owner

## Goal

Compose the merged BM-01 through BM-06 feature services into the canonical private control-plane API without adding credential resolution, private execution submission, runtime activation or live-capital authority.

## Deliverables

- deterministic bridge from trusted portal permissions to the frozen BM-00 capability vocabulary;
- feature-owned FastAPI router factories for catalog, builder, command persistence, signal control, grid configuration and exchange metadata;
- central application composition through the existing control-plane factory;
- fail-closed default providers where external signature or credential verification is unavailable;
- exact tenant, actor, environment, revision and correlation propagation;
- API/OpenAPI/security regression tests;
- no direct browser, exchange, secret-store or Freqtrade access.

## Non-goals

- PI-07 credential brokering or secret backend selection;
- PI-08 private Freqtrade submission or reconciliation activation;
- BM-07 position/order execution activation;
- real Authentik, Cloudflare, Synology or observability acceptance;
- live capital or withdrawals.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T10:40:00+02:00
head: e79f4f1358a67304eab8667f165a9d94723103ce
branch: feat/portal-bm-integration-owner-v1
pr: null
status: active
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
owned_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/bot_catalog/router.py
  - ai_platform/portal/bot_builder/router.py
  - ai_platform/portal/bot_operations/router.py
  - ai_platform/portal/signal_control/router.py
  - ai_platform/portal/grid_control/router.py
  - ai_platform/portal/exchange_connections/router.py
  - tests/ai_platform/portal/control_plane/test_bot_management_api.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bm-integration-owner.md
proven:
  - BM-00 through BM-06 are merged on develop.
  - No open PR currently owns the declared shared control-plane or bot-management router paths.
  - PI-07 and PI-08 remain explicitly gated and are outside this package.
derived:
  - The next safe software action is router composition and trusted capability bridging without execution activation.
unknown:
  - Exact service-constructor requirements for all fail-closed default providers until source inspection is complete.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Treat BM-05 merge as completion of the entire bot-management program.
  - Start PI-07 or PI-08 without the required owner/security decisions.
changed_paths:
  - docs/agents/tasks/FTAI-20260728-portal-bm-integration-owner.md
validation:
  - command: repository preflight
    result: PASS
    evidence: develop head e79f4f1358a67304eab8667f165a9d94723103ce and no overlapping open PR paths
blockers: []
next_action: Inspect exact feature service schemas and add the capability bridge plus router factories with focused API tests.
```
