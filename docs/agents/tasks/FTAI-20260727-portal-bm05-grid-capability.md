---
task_id: FTAI-20260727-portal-bm05-grid-capability
status: validating
branch: feat/portal-bm05-grid-capability
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: null
owned_paths:
  - ai_platform/portal/grid_control/**
  - tests/ai_platform/portal/grid_control/**
  - docs/agents/tasks/FTAI-20260727-portal-bm05-grid-capability.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
---

# BM-05 grid product capability

## Goal

Provide tenant-scoped, deterministic and evidence-driven grid configuration preview plus immutable dry-run policy revisions. The package must model arithmetic and geometric levels, allocation, exchange precision and minima without submitting an order or activating a runtime.

## Delivered

- Decimal-only arithmetic and geometric level generation with explicit precision-floor behavior.
- Tenant-scoped template and exchange capability evidence with freshness and exact revision binding.
- Deterministic preview identity, stable sorted reason codes and explicit per-level precision/minimum evidence.
- Total-quote and per-level quote allocation with over-allocation rejection.
- Capability gates for spacing, direction, level count, trailing grid, TP, SL, leverage and margin mode.
- Dry-run-only preview and immutable contiguous policy revision persistence.
- Structural `order_submission_performed=false` evidence and no execution/order adapter surface.
- In-memory feature repository only; shared API registration and migration remain integration-owner work.

## Safety boundary

This task adds no API registration, migration, BFF route, exchange credential access, Freqtrade call, runtime mutation, order placement, PI-08 activation or live-capital authority. A valid preview or persisted policy is configuration evidence only.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T08:45:00+02:00
base_develop: 22b3288c141a70abe67c61f4e737561ecf6d7379
branch: feat/portal-bm05-grid-capability
pr: null
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - ai_platform/portal/contracts/bot_management/policies.py
  - ai_platform/portal/contracts/bot_management/capabilities.py
owned_paths:
  - ai_platform/portal/grid_control/**
  - tests/ai_platform/portal/grid_control/**
  - docs/agents/tasks/FTAI-20260727-portal-bm05-grid-capability.md
proven:
  - BM-00 and BM-02 policy/capability contracts are merged and expose GridPolicyVersion and GRID_CONFIGURE.
  - BM-04 merged into develop as 22b3288c141a70abe67c61f4e737561ecf6d7379 before this branch was created.
  - No open PR or existing branch owned the canonical BM-05 grid_control paths when work began.
  - All new feature code is confined to grid_control, focused tests and this checkpoint.
  - The service exposes preview and immutable persistence only and has no order submission or execution method.
derived:
  - Durable database migration, feature router and root composition remain integration-owner responsibilities.
unknown:
  - Focused test, lint, typing and terminal exact-head repository workflow results.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Use binary floats for grid prices or quantities.
  - Infer exchange support without explicit current capability evidence.
  - Persist a rejected preview.
  - Activate grid runtime commands or submit exchange/Freqtrade orders.
  - Modify root API, migration, BFF or execution adapter paths.
changed_paths:
  - ai_platform/portal/grid_control/__init__.py
  - ai_platform/portal/grid_control/evidence.py
  - ai_platform/portal/grid_control/level_generation.py
  - ai_platform/portal/grid_control/repository.py
  - ai_platform/portal/grid_control/schema.py
  - ai_platform/portal/grid_control/service.py
  - tests/ai_platform/portal/grid_control/__init__.py
  - tests/ai_platform/portal/grid_control/support.py
  - tests/ai_platform/portal/grid_control/test_level_generation.py
  - tests/ai_platform/portal/grid_control/test_preview_validation.py
  - tests/ai_platform/portal/grid_control/test_persistence_and_safety.py
  - docs/agents/tasks/FTAI-20260727-portal-bm05-grid-capability.md
validation:
  - command: focused Python compilation
    result: PENDING
  - command: focused pytest suite
    result: PENDING
  - command: Ruff, Ruff format and mypy
    result: PENDING
  - command: terminal exact-head repository workflows
    result: PENDING
blockers: []
next_action: Open the bounded BM-05 PR, collect focused and repository validation, repair only task-caused failures, audit exact changed paths and review state, then squash-merge.
```
