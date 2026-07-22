---
task_id: FTAI-20260722-portal-p2-control-plane-core
status: ready
branch: feat/portal-p2-control-plane-core
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "#116"
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

P2 was validated on PR #116. The AI Platform workflow permanently adds only lightweight dependencies already present in repository runtime/development requirements so control-plane tests can exercise FastAPI, Pydantic and SQLAlchemy without starting production infrastructure.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T13:18:49+02:00
head: 473124c61e966bd5fbd01e6fc5933bc81d9af567
branch: feat/portal-p2-control-plane-core
pr: "#116"
status: ready
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
  - Shared-contract PR #115 was squash-merged as 4ea0f9c5f2c8fbd206d7b29f0487135ec875ac22 after required CI passed, resolving the first P2 semantic blocker.
  - P2 provides a fail-closed trusted identity-context dependency; no configured provider returns 401 and arbitrary browser identity headers are not trusted.
  - Bot repository, service and HTTP boundaries scope every resource lookup and mutation by trusted tenant_id and do not disclose cross-tenant bots.
  - Server-side P1 permissions gate bot create/read and start/pause/stop desired-state requests; missing permissions deny access.
  - Bot creation atomically persists BotInstance, immutable revision 1, AuditEvent and outbox EventEnvelope; outbox failure rolls the transaction back.
  - Configuration revisions append monotonically and prior revision rows remain unchanged; duplicate or skipped identities are rejected.
  - Desired state commands emit requested semantics and never mutate observed runtime state; concrete runtime reconciliation remains outside P2.
  - PostgreSQL-compatible migration defines tenant-scoped bot/revision metadata plus append-oriented audit and outbox tables with identity constraints.
  - Browser-facing OpenAPI and bot responses expose no raw exchange credentials, Freqtrade credentials, private runtime addresses or direct Freqtrade routes.
  - Frozen thresholds, protected final holdout, completed Phase 6 and selected_model = null were not changed or evaluated.
  - AI Platform CI run 29914226566 passed on implementation head 473124c61e966bd5fbd01e6fc5933bc81d9af567.
  - Freqtrade CI run 29914226561 and zizmor run 29914226587 passed on implementation head 473124c61e966bd5fbd01e6fc5933bc81d9af567; optional types run 29914226540 was skipped.
derived:
  - P2 now supplies a stable tenant-scoped desired-state and persistence boundary that P3 can consume without exposing Freqtrade directly to the portal.
  - P4 can consume durable outbox rows later without changing P2 transactional domain semantics.
  - Final production identity/session provider and production database migration runner remain replaceable deployment decisions.
unknown:
  - Final production identity/session provider remains intentionally deferred.
  - Final PostgreSQL deployment configuration and migration runner remain intentionally deferred.
conflicts: []
first_failure:
  marker: shared-contract-gap
  evidence: Initial P2 preflight found missing desired-state/configuration command semantics; dedicated PR #115 resolved the gap before downstream implementation.
rejected_hypotheses:
  - P2 may emit observed bot.paused or bot.stopped events for desired-state requests.
  - P2 may define private duplicate event or audit enums.
  - P2 requires direct Freqtrade API calls.
  - Outbox query order is causal operation order when occurred_at values are identical.
changed_paths:
  - .github/workflows/ai-platform.yml
  - ai_platform/portal/control_plane/__init__.py
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/context.py
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/control_plane/migrations/0001_control_plane.sql
  - ai_platform/portal/control_plane/models.py
  - ai_platform/portal/control_plane/repository.py
  - ai_platform/portal/control_plane/service.py
  - docs/agents/tasks/FTAI-20260722-portal-p2-control-plane-core.md
  - docs/ai_platform/portal/CONTROL_PLANE_CORE.md
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/control_plane/test_migration.py
  - tests/ai_platform/portal/control_plane/test_service.py
validation:
  - command: P2 resume preflight
    result: PASS
    evidence: Contract blocker resolved by merged PR #115 and P2 branch reset to current develop before implementation resumed.
  - command: python -m compileall -q ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29914226566 passed compile validation.
  - command: python -m pytest -q -o addopts='' --confcutdir=tests/ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29914226566 passed all AI Platform tests including P2 service API migration and negative security cases.
  - command: ruff check ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29914226566 and Freqtrade quality job passed Ruff.
  - command: ruff format --check ai_platform tests/ai_platform
    result: PASS
    evidence: AI Platform CI run 29914226566 and Freqtrade quality job passed Ruff format.
  - command: pre-commit checks
    result: PASS
    evidence: Freqtrade CI run 29914226561 Pre-commit checks job passed after mypy test typing fixes.
  - command: mypy
    result: PASS
    evidence: Freqtrade CI run 29914226561 Ubuntu 3.13 quality job passed mypy.
  - command: documentation build
    result: PASS
    evidence: Freqtrade CI run 29914226561 Documentation build job passed.
  - command: Freqtrade CI and CI Gate
    result: PASS
    evidence: Freqtrade CI run 29914226561 completed successfully with required matrix and gate outcomes.
  - command: zizmor
    result: PASS
    evidence: GitHub Actions Security Analysis run 29914226587 completed successfully.
  - command: Pre-commit Types update
    result: NOT_RUN
    evidence: Optional workflow run 29914226540 was skipped and is not a failure.
blockers: []
next_action: Review and squash-merge PR #116; after merge, start P3 Execution Adapter, P4 Data / Observability, P5 Model Lifecycle Control and P10a Exchange Simulator Core as separate disjoint bounded tasks from current develop.
```
