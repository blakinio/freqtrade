---
task_id: FTAI-20260722-portal-p2-control-plane-core
status: active
branch: feat/portal-p2-control-plane-core
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
owned_paths:
  - ai_platform/portal/control_plane/
  - tests/ai_platform/portal/control_plane/
  - docs/ai_platform/portal/CONTROL_PLANE_CORE.md
  - docs/agents/tasks/FTAI-20260722-portal-p2-control-plane-core.md
  - .github/workflows/ai-platform.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
search_first:
  - current develop HEAD and merged P1/contract-change PRs #114/#115
  - open PRs and active tasks overlapping control-plane ownership
  - existing P1 contracts and security helpers
  - existing FastAPI and SQLAlchemy dependency conventions
optional_reads:
  - only control-plane implementation-adjacent files
---

# AI Trading Portal P2 — Control Plane Core

## Goal

Implement the smallest modular FastAPI control-plane boundary that persists tenant-scoped BotInstances and immutable BotConfigRevisions, enforces server-side permissions, records audit evidence and writes domain events to a transactional outbox without exposing Freqtrade or exchange credentials.

## Deliverables

- fail-closed FastAPI application boundary under `ai_platform/portal/control_plane/`;
- trusted tenant/actor request-context dependency abstraction;
- SQLAlchemy persistence models and repository/service layer for bots and immutable revisions;
- PostgreSQL-compatible initial migration for control-plane metadata, audit and outbox tables;
- capability-gated bot create/read/state-change/revision operations;
- append-oriented audit persistence and transactional outbox persistence;
- OpenAPI/contract and tenant-isolation tests;
- implementation documentation in `docs/ai_platform/portal/CONTROL_PLANE_CORE.md`.

## Non-negotiable boundaries

- Do not modify upstream `freqtrade/` core.
- Do not implement real exchange integration or concrete Freqtrade adapter calls.
- Do not expose exchange secrets, Freqtrade credentials, runtime addresses or WebSocket tokens.
- Do not treat arbitrary browser headers as authenticated application identity; identity context must come from an explicitly configured trusted provider and otherwise fail closed.
- Do not add a test-only security bypass endpoint.
- Do not enable live capital; persisted bot specs remain limited by P1 execution-mode contracts.
- Every tenant-owned query and mutation must be scoped server-side by tenant_id.
- Every material bot configuration change creates a new immutable revision; existing revisions are never updated in place.
- Privileged mutations require explicit P1 permissions; missing or unknown permissions deny access.
- Audit and outbox writes for state-changing operations must occur in the same database transaction as domain persistence.
- Do not redefine P1 shared contracts locally.
- Do not change frozen thresholds `0.006/-0.009`, access protected final holdout `20260801-20260930`, reopen Phase 6, or change `selected_model = null`.

## Acceptance criteria

1. The application fails closed when no trusted identity-context provider is configured.
2. Tenant A cannot read or mutate Tenant B bot resources through repository, service or HTTP boundaries.
3. Bot creation requires `bot.create`; reads require `bot.read`; desired-state mutations require corresponding start/pause/stop permission.
4. Bot creation persists one BotInstance and its initial immutable BotConfigRevision atomically.
5. Material configuration changes append a new revision with monotonically increasing revision number and never mutate prior revision rows.
6. Desired state and observed state remain separate; P2 changes desired intent only and does not pretend execution occurred.
7. State-changing operations append an AuditEvent and EventEnvelope-compatible outbox record in the same transaction.
8. API responses contain no raw exchange credentials, Freqtrade credentials or private runtime addresses.
9. PostgreSQL-compatible migration creates tenant-scoped bot, revision, audit and outbox tables with required uniqueness constraints.
10. OpenAPI exposes only portal control-plane routes and remains compatible with P1 public contracts.
11. Targeted positive and negative tests, compile validation, Ruff lint/format, relevant AI Platform tests and repository CI pass.

## Validation

Run targeted control-plane tests first, then AI Platform tests, compile validation, Ruff lint and format. After push verify AI Platform CI, Freqtrade CI, zizmor, documentation build and CI Gate; optional skipped jobs are not failures.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T13:45:00+02:00
head: 4ea0f9c5f2c8fbd206d7b29f0487135ec875ac22
branch: feat/portal-p2-control-plane-core
pr: null
status: implementing
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/CONTRACTS_AND_SECURITY_FOUNDATION.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
owned_paths:
  - ai_platform/portal/control_plane/
  - tests/ai_platform/portal/control_plane/
  - docs/ai_platform/portal/CONTROL_PLANE_CORE.md
  - docs/agents/tasks/FTAI-20260722-portal-p2-control-plane-core.md
  - .github/workflows/ai-platform.yml
proven:
  - P1 PR #114 was squash-merged to develop as 1a6bb11f0eb6257c90c92dc43dffb3317c7149a8 before P2 started.
  - Shared-contract PR #115 was squash-merged as 4ea0f9c5f2c8fbd206d7b29f0487135ec875ac22 after AI Platform CI, Freqtrade CI and zizmor passed.
  - Develop is identical to 4ea0f9c5f2c8fbd206d7b29f0487135ec875ac22 and the P2 branch was reset to that exact commit before implementation resumed.
  - Open unrelated PRs do not own ai_platform/portal/control_plane or P2 test/documentation paths.
  - Repository dependencies already include FastAPI, Pydantic v2 and SQLAlchemy 2.
  - P1 plus PR #115 now provide truthful event/audit vocabulary for creation, immutable config revision and start/pause/stop requested commands.
derived:
  - P2 can remain entirely outside upstream freqtrade core and defer real runtime/exchange behavior to P3.
  - A trusted request-context provider abstraction avoids creating a fake authentication mechanism while allowing deterministic application authorization tests.
unknown:
  - Final production identity/session provider remains intentionally deferred.
  - Final PostgreSQL deployment configuration and migration runner remain intentionally deferred; P2 provides portable SQLAlchemy metadata plus a PostgreSQL-compatible initial migration.
conflicts: []
first_failure:
  marker: shared-contract-gap
  evidence: Initial P2 preflight found missing desired-state/configuration command semantics; dedicated PR #115 resolved the gap before downstream implementation.
rejected_hypotheses:
  - P2 may emit observed bot.paused or bot.stopped events for desired-state requests.
  - P2 may define private duplicate event or audit enums.
  - P2 requires direct Freqtrade API calls.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-portal-p2-control-plane-core.md
validation:
  - command: P2 resume preflight
    result: PASS
    evidence: Contract blocker resolved by merged PR #115 and P2 branch rebased cleanly by ref reset to current develop.
blockers: []
next_action: Implement the fail-closed control-plane application, persistence, bot service, transactional audit/outbox and targeted tests within the declared P2 owned paths.
```
