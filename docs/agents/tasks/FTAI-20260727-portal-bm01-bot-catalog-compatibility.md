---
task_id: FTAI-20260727-portal-bm01-bot-catalog-compatibility
status: active
branch: feat/portal-bm01-bot-catalog-compatibility
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
owned_paths:
  - ai_platform/portal/bot_catalog/**
  - tests/ai_platform/portal/bot_catalog/**
  - docs/agents/tasks/FTAI-20260727-portal-bm01-bot-catalog-compatibility.md
---

# BM-01 — Bot catalog and compatibility

## Goal

Implement the first downstream consumer of the merged BM-00 contracts: an immutable, server-owned bot catalog with bounded template discovery and deterministic compatibility decisions.

## Scope

- immutable versioned catalog snapshots;
- template, strategy, model, exchange-profile, runtime and risk-policy catalog entries;
- exact snapshot lookup and latest-version discovery;
- bounded deterministic template filtering and cursor pagination;
- tenant and capability gates;
- authoritative compatibility decisions using BM-00 reason and evidence contracts;
- explicit missing, stale and unavailable evidence handling;
- no routes, migrations, browser work, credential resolution, Freqtrade calls or execution activation.

## Acceptance

- catalog entries and snapshots are frozen, strict and deterministically ordered;
- exact catalog revision lookup fails closed;
- list pagination is bounded to the shared maximum and cursors are request-bound;
- compatibility decisions have deterministic identifiers, sorted reason codes and sorted evidence references;
- model-required, stale revision, unsupported capability, missing evidence, tenant mismatch and missing capability paths are tested;
- catalog serialization contains no secret values or secret-store paths;
- focused tests, Ruff and repository CI pass.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T14:35:00+02:00
head: 49e7fd328fef0b51ed80b5a15ea2e4f2035a2d2b
branch: feat/portal-bm01-bot-catalog-compatibility
pr: null
status: active
context_routes:
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
owned_paths:
  - ai_platform/portal/bot_catalog/**
  - tests/ai_platform/portal/bot_catalog/**
  - docs/agents/tasks/FTAI-20260727-portal-bm01-bot-catalog-compatibility.md
proven:
  - BM-00 contracts are merged into develop through PR 440.
  - BM-01 is the first safe downstream catalog and compatibility workstream in wave 1.
  - No open PR currently owns bot_catalog paths.
derived:
  - A repository-only immutable catalog can be delivered without migration coordination.
unknown: []
conflicts: []
first_failure: null
rejected_hypotheses:
  - Add catalog routes to shared control-plane composition in this task.
  - Add mutable database persistence or migration heads in this task.
  - Resolve exchange credentials or activate Freqtrade execution from catalog compatibility.
changed_paths: []
validation: []
blockers: []
next_action: Commit the BM-01 module and focused tests, open a draft PR, and validate the exact head in CI.
```
