---
task_id: FTAI-20260722-portal-p4-data-observability
status: active
branch: feat/portal-p4-data-observability
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
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
  - current develop and merged P3 state
  - open PRs overlapping events or observability ownership
  - canonical P1 EventEnvelope and P2 transactional outbox
optional_reads:
  - only event publication and telemetry implementation-adjacent files
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
updated_at: 2026-07-22T15:30:00+02:00
head: 4ccbfcdcc4b18a69b352679793d4028bcbc6f120
branch: feat/portal-p4-data-observability
pr: null
status: implementing
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
  - P3 PR #118 was squash-merged to develop as 4ccbfcdcc4b18a69b352679793d4028bcbc6f120 after final-head required CI passed.
  - Current develop is identical to 4ccbfcdcc4b18a69b352679793d4028bcbc6f120 and P4 branch was created from that exact commit.
  - Open PR #112 and #109 do not own events or observability paths.
  - P1 EventEnvelope is frozen and already rejects sensitive payload keys.
  - P2 persists canonical EventEnvelope JSON in portal_outbox_events with published_at nullable until publication.
  - Architecture requires at-least-once delivery, idempotent consumers and correlation IDs distinct from trace/span IDs.
derived:
  - P4 can implement publication and consumer deduplication without modifying P1 event schemas or P2 bot business logic.
unknown:
  - Final external event bus and telemetry backends remain intentionally replaceable deployment decisions.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Claim exactly-once delivery from the transactional outbox alone.
  - Store Redis as authoritative inbox/audit state.
  - Log full request bodies for convenience.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-portal-p4-data-observability.md
validation:
  - command: live-state P4 preflight
    result: PASS
    evidence: develop verified after P3 merge; P4 ownership is disjoint; canonical event/outbox contracts reviewed.
blockers: []
next_action: Implement outbox publication, durable idempotent consumer reference and correlation-safe telemetry under P4-owned paths.
```
