---
task_id: FTAI-20260728-portal-bm-integration-owner
status: validating
branch: feat/portal-bm-integration-owner-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 591
owned_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/control_plane/bot_management_errors.py
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

## Delivered

- Deterministic trusted-permission bridge to the frozen BM-00 capability vocabulary.
- Feature-owned FastAPI router factories for catalog, builder, command persistence, signal control, grid configuration and exchange metadata.
- Central composition through the existing control-plane application factory.
- Fail-closed signature verification until a separately reviewed provider is injected.
- BM-03 SQLAlchemy model registration in the development/test schema.
- Exact tenant, actor, environment, revision and correlation propagation.
- Focused API, OpenAPI, tenant, permission, persistence and secret-boundary tests.

## Safety boundary

This package adds no PI-07 credential resolution, PI-08 private submission, runtime adapter invocation, exchange request, browser-to-Freqtrade path, withdrawal authority or live capital. Persisted BM-03 commands remain intent and audit evidence only.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T10:57:00+02:00
head_parent: 57b48ec994d3fd3bc446294f039b29b7ad068c56
branch: feat/portal-bm-integration-owner-v1
pr: 591
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
owned_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/control_plane/bot_management_errors.py
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
  - No open PR owned the declared shared control-plane or bot-management router paths when this package began.
  - PI-07 and PI-08 remain explicitly gated and outside this package.
  - PR 591 contains the module-owned routers, capability bridge, fail-closed providers, central composition and focused tests.
  - Temporary composition workflow run 30344249683 succeeded and removed its own workflow file before the validation head.
derived:
  - The integrated API can expose configuration, metadata and command-intent evidence without activating execution.
unknown:
  - Exact-head lint, typing and test results for the connector-authored validation head.
conflicts: []
first_failure:
  marker: COMPOSITION_WORKFLOW_MARKER_INDENT
  evidence: Run 30344041384 stopped before commit because the first patch used a dedented marker that did not preserve source indentation; corrected run 30344249683 passed.
rejected_hypotheses:
  - Treat BM-05 merge as completion of the entire bot-management program.
  - Start PI-07 or PI-08 without the required owner and security decisions.
  - Resolve signal or exchange secrets inside a public feature router.
changed_paths:
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/control_plane/bot_management.py
  - ai_platform/portal/control_plane/bot_management_errors.py
  - ai_platform/portal/bot_catalog/router.py
  - ai_platform/portal/bot_builder/router.py
  - ai_platform/portal/bot_operations/router.py
  - ai_platform/portal/signal_control/router.py
  - ai_platform/portal/grid_control/router.py
  - ai_platform/portal/exchange_connections/router.py
  - tests/ai_platform/portal/control_plane/test_bot_management_api.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - docs/agents/tasks/FTAI-20260728-portal-bm-integration-owner.md
validation:
  - command: temporary composition workflow 30344249683
    result: PASS
    evidence: Exact shared-file patch committed and temporary workflow removed itself.
  - command: exact-head AI Platform CI, Freqtrade CI and security analysis
    result: NOT_RUN
    evidence: Connector-authored checkpoint commit will create the authoritative validation head.
blockers: []
next_action: Run exact-head CI for PR 591, repair only integration-owned findings, then audit and merge the package.
```
