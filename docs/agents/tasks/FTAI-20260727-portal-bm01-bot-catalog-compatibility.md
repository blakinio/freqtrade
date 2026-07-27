---
task_id: FTAI-20260727-portal-bm01-bot-catalog-compatibility
status: ready
branch: feat/portal-bm01-bot-catalog-compatibility
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#474"
owned_paths:
  - ai_platform/portal/bot_catalog/**
  - tests/ai_platform/__init__.py
  - tests/ai_platform/portal/__init__.py
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
updated_at: 2026-07-27T16:56:00+02:00
head: c18241197af0d06215b3eaa844f6f062603f46ec
branch: feat/portal-bm01-bot-catalog-compatibility
pr: "#474"
status: ready
context_routes:
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
owned_paths:
  - ai_platform/portal/bot_catalog/**
  - tests/ai_platform/__init__.py
  - tests/ai_platform/portal/__init__.py
  - tests/ai_platform/portal/bot_catalog/**
  - docs/agents/tasks/FTAI-20260727-portal-bm01-bot-catalog-compatibility.md
proven:
  - BM-00 contracts are merged into develop through PR 440.
  - BM-01 delivers immutable catalog snapshots for templates, strategies, models, exchange profiles, runtimes and risk policies.
  - Exact and latest catalog revision lookup, bounded deterministic filtering and request-bound cursor pagination are implemented.
  - Tenant and capability gates fail closed before catalog access or compatibility evaluation.
  - Compatibility decisions use BM-00 contracts with stable identifiers, sorted reason codes and authoritative evidence references.
  - Missing, unavailable, deprecated and stale catalog evidence paths are explicitly represented and tested.
  - Catalog serialization rejects extras and contains no secret values or secret-store paths.
  - The test namespace is explicit so the BM-01 conftest cannot collide with the repository root conftest under mypy.
  - Exact-head c18241197af0d06215b3eaa844f6f062603f46ec passed AI Platform CI 30276129183.
  - Exact-head c18241197af0d06215b3eaa844f6f062603f46ec passed Freqtrade CI 30276129746, including Python 3.11 through 3.14, coverage, smoke tests, Ruff, mypy, distribution build and CI Gate.
  - Exact-head c18241197af0d06215b3eaa844f6f062603f46ec passed GitHub Actions Security Analysis with zizmor 30276129235.
  - PR 474 changed-path audit contains only the declared BM-01 implementation, test-package markers, tests and task checkpoint.
  - PR 474 has no review threads and no submitted change requests.
derived:
  - BM-02 can consume the frozen BM-01 catalog and compatibility service without adding routes, migrations or execution authority to BM-01.
unknown: []
conflicts: []
first_failure:
  marker: MYPY_DUPLICATE_CONFTEST_MODULE
  evidence: Repository mypy discovered the nested fixture file as another top-level conftest; explicit package markers and package-qualified test imports removed the collision without weakening mypy or changing fixture behavior.
rejected_hypotheses:
  - Add catalog routes to shared control-plane composition in this task.
  - Add mutable database persistence or migration heads in this task.
  - Resolve exchange credentials or activate Freqtrade execution from catalog compatibility.
  - Disable or narrow repository mypy to bypass the nested conftest collision.
  - Replace authoritative compatibility evidence with client-side inference.
changed_paths:
  - ai_platform/portal/bot_catalog/**
  - tests/ai_platform/__init__.py
  - tests/ai_platform/portal/__init__.py
  - tests/ai_platform/portal/bot_catalog/**
  - docs/agents/tasks/FTAI-20260727-portal-bm01-bot-catalog-compatibility.md
validation:
  - command: pytest -q tests/ai_platform/portal/bot_catalog
    result: PASS
    evidence: Focused BM-01 suite passed with 27 tests.
  - command: ruff check ai_platform/portal/bot_catalog tests/ai_platform/portal/bot_catalog
    result: PASS
    evidence: Ruff 0.15.21 passed with repository lint selectors and test security ignores.
  - command: ruff format --check ai_platform/portal/bot_catalog tests/ai_platform/portal/bot_catalog
    result: PASS
    evidence: Ruff 0.15.21 reported no formatting drift.
  - command: AI Platform CI 30276129183 on c18241197af0d06215b3eaa844f6f062603f46ec
    result: PASS
    evidence: Compile, 27 focused tests, Ruff, formatting, codespell and JSON validation all passed.
  - command: Freqtrade CI 30276129746 on c18241197af0d06215b3eaa844f6f062603f46ec
    result: PASS
    evidence: Pre-commit, docs, Python 3.11-3.14 core tests, coverage, smoke tests, Ruff, mypy, build and CI Gate all passed.
  - command: GitHub Actions Security Analysis 30276129235 on c18241197af0d06215b3eaa844f6f062603f46ec
    result: PASS
    evidence: zizmor workflow completed successfully.
  - command: PR 474 changed-path and review-thread audit
    result: PASS
    evidence: Thirteen declared files only; review_threads is empty and no change-request review exists.
blockers: []
next_action: Merge PR #474 into develop after the terminal checkpoint exact-head CI passes.
```
