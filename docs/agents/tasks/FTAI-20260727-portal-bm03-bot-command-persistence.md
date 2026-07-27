---
task_id: FTAI-20260727-portal-bm03-bot-command-persistence
status: ready
branch: feat/portal-bm03-bot-command-persistence
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: 479
owned_paths:
  - ai_platform/portal/bot_operations/**
  - tests/ai_platform/portal/bot_operations/**
  - docs/agents/tasks/FTAI-20260727-portal-bm03-bot-command-persistence.md
required_reads:
  - AGENTS.md
  - ai_platform/AGENTS.md
  - ai_platform/portal/AGENTS.md
  - docs/AGENTS.md
  - docs/agents/AGENTS.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - ai_platform/portal/contracts/bot_management/commands.py
  - ai_platform/portal/contracts/bot_management/capabilities.py
  - ai_platform/portal/contracts/bot_management/command_conformance.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/execution/private_read.py
  - ai_platform/portal/risk/policy.py
  - docs/agents/tasks/FTAI-20260726-portal-bm00-bot-management-contracts.md
---

# BM-03 bot command persistence

## Delivered

- Feature-local SQLAlchemy records for lifecycle, position and order command intent.
- Tenant-scoped exact idempotent replay and append-only conflict evidence.
- Binding to tenant, actor, environment, bot, config revision, runtime and runtime revision.
- Outcomes `ACCEPTED`, `REJECTED`, `BLOCKED` and `PENDING_RECONCILIATION`.
- Sequenced append-only command history with prepared audit and event evidence.
- Deterministic capability, stale revision, stale runtime and kill-switch decisions.
- No execution-success state; pending reconciliation requires an external execution-attempt reference.

## Safety boundary

The feature does not call Freqtrade or an exchange, mutate positions or orders, resolve credentials, implement PI-08, register a root API route, add a migration, alter shared BFF code or authorize live capital. Migration sequencing and shared API/database composition remain integration-owner responsibilities.

## Validation

- Cross-tenant rejection, missing capability, duplicate idempotency, revision mismatch, stale runtime, kill switch and append-only history are covered.
- Clean implementation head `955ba8dfc93ed79859319d60c776a79915d3ebd1` passed AI Platform CI run `30283271761`, Freqtrade CI run `30283271736` and zizmor run `30283271689`.
- Changed-path audit contains exactly the eight feature files, two focused test files and this task record.
- Pull request review-thread audit found zero open threads.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T18:29:00+02:00
validated_implementation_head: 955ba8dfc93ed79859319d60c776a79915d3ebd1
branch: feat/portal-bm03-bot-command-persistence
pr: 479
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - ai_platform/portal/contracts/bot_management/commands.py
  - ai_platform/portal/contracts/bot_management/capabilities.py
  - ai_platform/portal/risk/policy.py
  - ai_platform/portal/execution/private_read.py
owned_paths:
  - ai_platform/portal/bot_operations/**
  - tests/ai_platform/portal/bot_operations/**
  - docs/agents/tasks/FTAI-20260727-portal-bm03-bot-command-persistence.md
proven:
  - BM-00 PR 440 was merged into develop and its required CI was green before implementation began.
  - Command acceptance is persisted as intent only and never as execution success.
  - Exact replay does not append history; conflicting reuse records rejected evidence.
  - Tenant, actor, environment, revision, runtime freshness and kill-switch gates fail closed.
  - Required implementation-head CI and security analysis passed.
derived:
  - Integration requires an additive migration and shared API/database composition owned outside this task.
unknown: []
conflicts: []
blockers: []
next_action: Integration owner reviews and merges PR 479, then owns the additive migration and shared API/database composition in a separate task.
```
