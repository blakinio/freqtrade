---
task_id: FTAI-20260722-portal-p4-data-observability
status: ready
branch: feat/portal-p4-data-observability
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "#119"
owned_paths:
  - ai_platform/portal/events/
  - ai_platform/portal/observability/
  - tests/ai_platform/portal/events/
  - tests/ai_platform/portal/observability/
  - docs/ai_platform/portal/DATA_OBSERVABILITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p4-data-observability.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - ai_platform/portal/contracts/events.py
  - ai_platform/portal/control_plane/models.py
search_first:
  - current develop and open PRs or active tasks overlapping P5 model_control ownership
  - merged PR #119 and P4 checkpoint before declaring successor work
  - canonical P1 model and audit contracts plus existing registry semantics
optional_reads:
  - only model lifecycle implementation-adjacent files when the successor task requires them
---

# AI Trading Portal P4 — Data / Observability Foundation

## Goal

Implement durable at-least-once outbox publication, idempotent consumer reference infrastructure, correlation-preserving structured telemetry and secret redaction without owning bot business logic or redefining P1 events.

## Deliverables

- outbox publisher abstraction consuming P2 `portal_outbox_events`;
- transport protocol with at-least-once semantics and publish acknowledgment only after successful transport call;
- durable tenant-aware event inbox/deduplication table and idempotent consumer reference;
- correlation-preserving structured logs, metric and trace abstractions;
- recursive secret redaction for operational telemetry;
- targeted duplicate-delivery, publish-failure, correlation and redaction tests;
- implementation documentation.

## Non-negotiable boundaries

- Do not modify upstream `freqtrade/` core.
- Do not redefine or fork P1 `EventEnvelope`; `event_version` remains canonical.
- Do not own bot state/business transitions in P4.
- Treat delivery as at-least-once; do not claim exactly-once publication.
- A transport failure must leave an outbox row unpublished.
- Consumer side effects and durable inbox marker must commit in one database transaction.
- Duplicate event delivery for the same consumer must not re-run side effects.
- Events/logs/metrics/traces must not expose secret/token/password/private-key values.
- Do not deploy NATS, Redis, Prometheus, Grafana or an external trace backend in P4.
- Do not alter frozen thresholds, protected holdout, completed Phase 6 or `selected_model = null`.

## Acceptance criteria

1. P2 outbox rows can be published through a replaceable transport and marked published only after successful send.
2. A failed publish remains eligible for retry; duplicate delivery is explicitly possible and documented.
3. Reference consumer deduplication is durable per `(consumer_name, event_id)` and tenant-aware.
4. Consumer handler side effects and inbox marker are transactional.
5. P1 EventEnvelope correlation/request/causation IDs propagate through publisher and consumer paths unchanged.
6. Structured logs and trace/metric attributes recursively redact sensitive fields.
7. Basic operation instrumentation emits correlated start/success/failure evidence and duration/error metrics without logging exception messages.
8. No external infrastructure or bot business logic is introduced.
9. Targeted tests, AI Platform tests, Ruff, pre-commit, mypy and required repository CI pass.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T16:47:37+02:00
head: ef32a6e90b3075e3170c093d483fb76bf8625dce
branch: develop
pr: "#119"
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
owned_paths:
  - ai_platform/portal/events/
  - ai_platform/portal/observability/
  - tests/ai_platform/portal/events/
  - tests/ai_platform/portal/observability/
  - docs/ai_platform/portal/DATA_OBSERVABILITY_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p4-data-observability.md
proven:
  - P4 implements replaceable at-least-once outbox publication over P2 portal_outbox_events and marks published_at only after a successful transport call.
  - P4 adds durable portal_event_inbox deduplication keyed by consumer_name and event_id with handler side effects in the same transaction.
  - P4 propagates canonical request, correlation and causation identifiers without changing the P1 EventEnvelope schema.
  - P4 structured telemetry recursively redacts secret/token/password/private-key/cookie fields and records exception types without exception messages.
  - PR #119 final head a64709b3c7158425be0d80b57383b14ad7e4892d passed AI Platform CI 29929002230, Freqtrade CI 29929002827 and zizmor 29929002195.
  - PR #119 had no submitted reviews or review threads and was squash-merged as ef32a6e90b3075e3170c093d483fb76bf8625dce.
  - develop was verified identical to ef32a6e90b3075e3170c093d483fb76bf8625dce immediately after the P4 merge.
derived:
  - P4 acceptance criteria are complete and successor work can proceed as a separate P5 Model Lifecycle Control task without changing P4 contracts.
unknown:
  - Final event bus and telemetry backend implementations remain intentionally replaceable deployment decisions outside P4.
conflicts: []
first_failure:
  marker: pytest-module-name-collision
  evidence: Initial P4 AI Platform CI failed collection because two non-package test_migration.py modules collided; renaming the P4 test to test_event_inbox_migration.py resolved collection.
rejected_hypotheses:
  - Claim exactly-once delivery from the transactional outbox alone.
  - Store Redis as authoritative inbox or audit state.
  - Treat any handler IntegrityError as duplicate delivery.
  - Emit exception messages or full credential-bearing request bodies into telemetry.
changed_paths:
  - ai_platform/portal/events/__init__.py
  - ai_platform/portal/events/consumer.py
  - ai_platform/portal/events/migrations/0001_event_inbox.sql
  - ai_platform/portal/events/models.py
  - ai_platform/portal/events/outbox.py
  - ai_platform/portal/events/schema.py
  - ai_platform/portal/observability/__init__.py
  - ai_platform/portal/observability/redaction.py
  - ai_platform/portal/observability/telemetry.py
  - docs/agents/tasks/FTAI-20260722-portal-p4-data-observability.md
  - docs/ai_platform/portal/DATA_OBSERVABILITY_FOUNDATION.md
  - tests/ai_platform/portal/events/test_consumer.py
  - tests/ai_platform/portal/events/test_event_inbox_migration.py
  - tests/ai_platform/portal/events/test_outbox.py
  - tests/ai_platform/portal/observability/test_redaction.py
  - tests/ai_platform/portal/observability/test_telemetry.py
validation:
  - command: AI Platform CI run 29925402251
    result: PASS
    evidence: Compile, AI Platform tests, Ruff, Ruff format, Codespell and JSON validation succeeded on implementation head 0327c75159cdd70d754051383304646c192cc92a.
  - command: Freqtrade CI run 29925401946
    result: PASS
    evidence: Pre-commit, docs, full platform matrix, coverage, smoke tests, Ruff, formatter, mypy and CI Gate succeeded on the implementation head.
  - command: AI Platform CI run 29929002230
    result: PASS
    evidence: Final checkpoint-only head a64709b3c7158425be0d80b57383b14ad7e4892d passed AI Platform validation.
  - command: Freqtrade CI run 29929002827
    result: PASS
    evidence: Final checkpoint-only head passed pre-commit, documentation, full platform matrix, coverage, mypy and final CI Gate.
  - command: zizmor run 29929002195
    result: PASS
    evidence: Final checkpoint-only head passed GitHub Actions security analysis.
  - command: Pre-commit Types update run 29929002829
    result: NOT_RUN
    evidence: Workflow concluded skipped and is not a failure gate.
blockers: []
next_action: Declare and start a separate P5 Model Lifecycle Control task from current develop after checking live open PRs and active tasks for model_control overlap; preserve frozen research boundaries and do not modify P4 contracts.
```
