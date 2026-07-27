---
task_id: FTAI-20260727-portal-bm02-bot-builder-configuration
status: active
branch: feat/portal-bm02-bot-builder-configuration
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
owned_paths:
  - ai_platform/portal/bot_builder/**
  - tests/ai_platform/portal/bot_builder/**
  - docs/agents/tasks/FTAI-20260727-portal-bm02-bot-builder-configuration.md
---

# BM-02 — Bot builder and configuration composition

## Goal

Implement the server-owned bot-configuration builder over the merged BM-00 contracts and BM-01 catalog compatibility service, without adding routes, migrations or execution authority.

## Scope

- immutable tenant-scoped draft revisions;
- full-snapshot draft replacement with optimistic revision checks;
- deterministic completeness previews;
- policy-family derivation from selected policy objects;
- authoritative BM-01 compatibility decisions before finalization;
- immutable `BotManagementConfiguration` composition;
- deterministic configuration identifiers and canonical SHA-256 evidence;
- idempotent finalization and optimistic configuration revision checks;
- no shared API registration, database migration, BFF work, credential resolution, Freqtrade call or execution activation.

## Acceptance

- drafts and finalizations are frozen, strict and tenant-scoped;
- draft and configuration revisions are contiguous and fail closed on stale expectations;
- missing fields are reported in deterministic sorted order;
- invalid cross-policy composition is reported without creating a configuration revision;
- rejected compatibility decisions cannot be finalized;
- finalized configurations bind the exact compatibility decision and canonical digest;
- first configuration requires `BOT_CREATE`; later revisions require `BOT_REVISE`;
- focused tests, Ruff, format and repository CI pass.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T17:30:00+02:00
head: 121f1b10dd584a81fb0ba93e83356833a2399110
branch: feat/portal-bm02-bot-builder-configuration
pr: null
status: implementing
context_routes:
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
owned_paths:
  - ai_platform/portal/bot_builder/**
  - tests/ai_platform/portal/bot_builder/**
  - docs/agents/tasks/FTAI-20260727-portal-bm02-bot-builder-configuration.md
proven:
  - BM-00 contracts are merged through PR 440.
  - BM-01 catalog and compatibility are merged through PR 474 at commit 2f17c994f8fa56cd0c7b0368195403e5ed932f9d.
  - No open PR owns bot_builder paths.
  - BM-03 PR 479 and BM-06 PR 480 own disjoint feature paths.
  - The local BM-02 focused suite passes with 25 tests.
  - Ruff 0.15.21 lint and format checks pass on BM-02 source and tests.
derived:
  - BM-02 can remain repository-only and consume BM-01 without shared composition changes.
  - Full-snapshot immutable draft revisions avoid ambiguous partial-patch semantics.
unknown: []
conflicts: []
first_failure:
  marker: NONE_OBSERVED
  evidence: Focused tests and exact repository Ruff validation pass before the first branch commit.
rejected_hypotheses:
  - Add root API registration or BFF routes in BM-02.
  - Add mutable database persistence or migration revisions in BM-02.
  - Resolve exchange credentials or call Freqtrade while composing configuration.
  - Allow a rejected compatibility decision to produce a final configuration revision.
changed_paths:
  - ai_platform/portal/bot_builder/**
  - tests/ai_platform/portal/bot_builder/**
  - docs/agents/tasks/FTAI-20260727-portal-bm02-bot-builder-configuration.md
validation:
  - command: pytest -q tests/ai_platform/portal/bot_builder
    result: PASS
    evidence: Focused BM-02 suite passed with 25 tests.
  - command: ruff check ai_platform/portal/bot_builder tests/ai_platform/portal/bot_builder
    result: PASS
    evidence: Ruff 0.15.21 passed with repository selectors.
  - command: ruff format --check ai_platform/portal/bot_builder tests/ai_platform/portal/bot_builder
    result: PASS
    evidence: Ruff 0.15.21 reported no formatting drift.
blockers: []
next_action: Commit the bounded BM-02 implementation, open a draft PR and validate exact-head repository CI.
```
