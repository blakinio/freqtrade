---
task_id: FTAI-20260727-portal-bm05-grid-capability
status: ready_for_merge
branch: feat/portal-bm05-grid-capability
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_pr: 565
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

Provide tenant-scoped, deterministic and evidence-driven grid configuration preview plus immutable dry-run policy revisions. The package models arithmetic and geometric levels, allocation, exchange precision and minima without submitting an order or activating a runtime.

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
updated_at: 2026-07-28T09:38:00+02:00
head_parent: 1e1d7b2d40f510a222832742fc7819588f0ce52e
base_develop: b6f4589ff4da88a9cbd91342c657de6b57def142
branch: feat/portal-bm05-grid-capability
pr: 565
status: ready_for_merge
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
  - The feature branch is synchronized with develop b6f4589ff4da88a9cbd91342c657de6b57def142 through feature-branch-only PR 563.
  - No open PR or existing branch owned the canonical BM-05 grid_control paths when work began.
  - PR 565 changes exactly twelve declared feature, test and checkpoint paths.
  - Forty-nine focused BM-05 test functions cover level generation, validation, exchange minima, immutable persistence and non-execution safety.
  - AI Platform CI 30338054945 passed compilation, the full AI Platform test suite, Ruff, Ruff format, codespell and JSON validation at head 1e1d7b2d40f510a222832742fc7819588f0ce52e.
  - Freqtrade CI 30338054961 passed pre-commit, documentation, Python 3.11-3.14 tests, full Python 3.12 coverage, Ruff, formatting, mypy, smoke tests, distribution build and final CI Gate at head 1e1d7b2d40f510a222832742fc7819588f0ce52e.
  - GitHub Actions security analysis 30338054982 passed at head 1e1d7b2d40f510a222832742fc7819588f0ce52e.
  - Exact Ruff 0.15.21 formatting was applied by feature-branch-only PR 568; the remaining S101 and C901 findings were captured in artifact 8679615072 and repaired in feature-owned service code.
  - Temporary diagnostic PR 570 was closed without merge and its workflow path is absent from PR 565.
  - The service exposes preview and immutable persistence only and has no order submission or execution method.
derived:
  - Durable database migration, feature router and root composition remain integration-owner responsibilities.
unknown: []
conflicts: []
first_failure:
  marker: BM05_RUFF_S101_C901
  evidence: Initial exact-head CI passed compilation and tests but reported two assert rules and one complexity rule; all were repaired without changing the safety boundary.
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
  - command: AI Platform compilation, tests, Ruff, format, codespell and JSON validation
    result: PASS
    evidence: workflow 30338054945
  - command: Freqtrade full matrix, typing, distribution build and final CI Gate
    result: PASS
    evidence: workflow 30338054961
  - command: GitHub Actions security analysis
    result: PASS
    evidence: workflow 30338054982
  - command: terminal documentation-only checkpoint head
    result: PENDING
blockers: []
next_action: Validate this documentation-only checkpoint exact head, audit changed paths and review state against current develop, then guarded squash-merge PR 565.
```
