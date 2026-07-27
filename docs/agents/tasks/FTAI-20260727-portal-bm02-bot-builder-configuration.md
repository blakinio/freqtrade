---
task_id: FTAI-20260727-portal-bm02-bot-builder-configuration
status: ready
branch: develop
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#492"
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
updated_at: 2026-07-27T19:02:00+02:00
head: 94460e7071e2e7155681b8727fa93661c6ec5378
branch: develop
pr: "#492"
status: ready
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
  - BM-02 delivers immutable tenant-scoped configuration draft revisions with optimistic concurrency.
  - Completeness previews, deterministic policy-family derivation and authoritative BM-01 compatibility evaluation are implemented.
  - Invalid cross-policy composition and rejected compatibility fail closed without persisting configuration revisions.
  - Finalized configurations bind the exact compatibility decision, deterministic configuration identifier and canonical SHA-256 digest.
  - First configuration creation requires BOT_CREATE and later configuration revisions require BOT_REVISE.
  - Draft finalization is idempotent for the exact tenant, draft and revision.
  - PR 492 changed exactly ten declared BM-02 implementation, test and checkpoint files.
  - PR 492 had no review threads and no submitted change-request reviews before merge.
  - Terminal exact-head 5f6c4c20d37bd0f8ce4786a4ebf9f805bf9662c2 passed AI Platform CI 30285681973.
  - Terminal exact-head 5f6c4c20d37bd0f8ce4786a4ebf9f805bf9662c2 passed Freqtrade CI 30285681810, including pre-commit, docs, Python 3.11 through 3.14, coverage, smoke tests, Ruff, mypy, distribution build and CI Gate.
  - Terminal exact-head 5f6c4c20d37bd0f8ce4786a4ebf9f805bf9662c2 passed GitHub Actions Security Analysis with zizmor 30285681735.
  - PR 492 was marked ready and squash-merged into develop as 94460e7071e2e7155681b8727fa93661c6ec5378.
derived:
  - BM-05 can consume finalized BM-02 policy composition without changing BM-02 ownership boundaries.
  - Later API integration can wrap this service without duplicating configuration or compatibility policy.
unknown: []
conflicts: []
first_failure:
  marker: NONE_OBSERVED
  evidence: Focused validation and both exact-head repository CI cycles passed without a BM-02 failure.
rejected_hypotheses:
  - Add root API registration or BFF routes in BM-02.
  - Add mutable database persistence or migration revisions in BM-02.
  - Resolve exchange credentials or call Freqtrade while composing configuration.
  - Allow a rejected compatibility decision to produce a final configuration revision.
  - Bypass BM-01 compatibility with client-side or builder-local inference.
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
  - command: AI Platform CI 30285681973 on 5f6c4c20d37bd0f8ce4786a4ebf9f805bf9662c2
    result: PASS
    evidence: Compile, AI platform tests, Ruff, formatting, codespell and JSON validation passed.
  - command: Freqtrade CI 30285681810 on 5f6c4c20d37bd0f8ce4786a4ebf9f805bf9662c2
    result: PASS
    evidence: Pre-commit, docs, Python 3.11-3.14, coverage, smoke tests, Ruff, mypy, distributions and CI Gate passed.
  - command: GitHub Actions Security Analysis 30285681735 on 5f6c4c20d37bd0f8ce4786a4ebf9f805bf9662c2
    result: PASS
    evidence: zizmor workflow completed successfully.
  - command: PR 492 merge verification
    result: PASS
    evidence: PR is closed and merged with squash commit 94460e7071e2e7155681b8727fa93661c6ec5378.
blockers: []
next_action: Use the merged BM-02 configuration builder as the policy-composition dependency for BM-05 and future bot-builder API integration.
```
