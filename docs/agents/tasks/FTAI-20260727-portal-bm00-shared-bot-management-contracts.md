---
task_id: FTAI-20260727-portal-bm00-shared-bot-management-contracts
status: ready
branch: feat/portal-bm00-shared-contracts
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#440"
owned_paths:
  - ai_platform/portal/contracts/bot_management/**
  - tests/ai_platform/portal/contracts/bot_management/**
  - docs/agents/tasks/FTAI-20260727-portal-bm00-shared-bot-management-contracts.md
  - docs/agents/prompts/PORTAL_BOT_MANAGEMENT_AGENT_PROMPTS.md
---

# BM-00 — Shared bot-management contracts

## Goal

Freeze strict, versioned, deterministic and secret-free contracts for complete dry-run bot creation and management before downstream portal agents consume the schemas.

## Delivered

- capability vocabulary;
- bounded pagination and deterministic filtering;
- versioned bot templates and compatibility decisions;
- market, entry, position-sizing, DCA, TP, multiple-TP, SL, break-even, trailing, signal, grid and runtime policies;
- normalized bot-management configuration;
- lifecycle, position and order commands;
- exchange capability, connection and verification metadata;
- signal endpoint, schema, replay, validation and command-mapping records;
- execution attempt, acknowledgement, ambiguity and authoritative reconciliation records;
- focused negative and deterministic serialization tests.

## Frozen boundaries

- all records reuse `ContractModel`, remain frozen and reject unknown fields;
- prices, quantities, percentages and allocations use `Decimal`;
- state-changing commands require tenant, actor, environment, correlation, idempotency and exact immutable revisions;
- `ACCEPTED` never proves execution;
- successful execution requires authoritative reconciliation evidence bound to the exact tenant, bot, configuration revision, runtime and runtime revision;
- exchange and signal records cannot serialize API keys, secrets, passphrases, tokens, private endpoints or secret-store paths;
- no API route, persistence, migration, BFF/frontend, secret provider, Freqtrade call, order submission or live-capital behavior is activated.

## Validation summary

- narrow compile and 23 focused tests passed;
- Ruff lint and format passed;
- AI Platform CI passed on the final implementation head;
- Freqtrade CI passed on the final implementation head;
- GitHub Actions security analysis with zizmor passed;
- PR #440 merged into `develop` as `5e960d45ba29c494a517937a4b7e0838ae9737db`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T14:19:53+02:00
head: 5e960d45ba29c494a517937a4b7e0838ae9737db
branch: develop
pr: "#440"
status: ready
context_routes:
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
owned_paths:
  - ai_platform/portal/contracts/bot_management/**
  - tests/ai_platform/portal/contracts/bot_management/**
  - docs/agents/tasks/FTAI-20260727-portal-bm00-shared-bot-management-contracts.md
  - docs/agents/prompts/PORTAL_BOT_MANAGEMENT_AGENT_PROMPTS.md
proven:
  - BM-00 delivers eleven strict contract modules and three focused test modules.
  - Contract models inherit frozen and extra-forbid behavior from ContractModel.
  - Decimal validation rejects non-finite and invalid numeric values.
  - Command acceptance is distinct from reconciled execution success.
  - Successful reconciliation requires authoritative evidence with exact binding.
  - Secret-bearing fields and private provider paths are excluded from serialized contracts.
  - The final implementation head passed AI Platform CI and security analysis.
  - The final implementation head passed full Freqtrade CI.
  - PR 440 merged into develop as commit 5e960d45ba29c494a517937a4b7e0838ae9737db.
derived:
  - Downstream bot-management agents may now consume the merged BM-00 schemas.
  - PI-07, PI-08, P11 and P14 remain separate authorization gates.
unknown: []
conflicts: []
first_failure:
  marker: RUFF_FORMAT_DRIFT
  evidence: Initial implementation CI identified formatter-only drift in three files; Ruff 0.15.21 formatting corrected it without logic changes.
rejected_hypotheses:
  - Treat ACCEPTED acknowledgement as proven execution.
  - Store exchange credentials or resolved secret-store paths in contracts.
  - Implement API, persistence, runtime submission or live-capital behavior in BM-00.
changed_paths:
  - ai_platform/portal/contracts/bot_management/**
  - tests/ai_platform/portal/contracts/bot_management/**
  - docs/agents/prompts/PORTAL_BOT_MANAGEMENT_AGENT_PROMPTS.md
  - docs/agents/tasks/FTAI-20260727-portal-bm00-shared-bot-management-contracts.md
  - docs/agents/tasks/FTAI-20260727-portal-bot-management-architecture-and-agent-plan.md
validation:
  - command: python -m compileall ai_platform/portal/contracts/bot_management
    result: PASS
    evidence: AI Platform CI run 1935 compiled the final implementation head successfully.
  - command: pytest -q tests/ai_platform/portal/contracts/bot_management
    result: PASS
    evidence: Focused BM-00 suite passed with 23 tests.
  - command: ruff check and ruff format --check
    result: PASS
    evidence: AI Platform CI run 1935 completed Ruff lint and format successfully.
  - command: repository Freqtrade CI
    result: PASS
    evidence: Freqtrade CI run 2369 completed pre-commit, documentation, Python 3.11-3.14, coverage, smoke tests, Ruff, mypy, distribution build and CI Gate successfully.
  - command: GitHub Actions Security Analysis with zizmor
    result: PASS
    evidence: Security run 2232 completed successfully on the final implementation head.
  - command: merge PR #440 into develop
    result: PASS
    evidence: GitHub created merge commit 5e960d45ba29c494a517937a4b7e0838ae9737db.
blockers: []
next_action: Use the merged BM-00 contracts as the schema dependency for the first downstream bot-management implementation task.
```
